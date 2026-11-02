require_relative '../plugin/ai_idea_v10/model_audit'
require_relative 'support/mock_panel_geometry'

IDENTITY = [1.0,0.0,0.0,0.0, 0.0,1.0,0.0,0.0, 0.0,0.0,1.0,0.0, 0.0,0.0,0.0,1.0].freeze

class FakePoint
  attr_accessor :x, :y, :z
  def initialize(x=0.0, y=0.0, z=0.0); @x=x; @y=y; @z=z; end
end
class Numeric
  def to_mm; self; end
end
class FakeBox
  attr_accessor :width, :height, :depth, :min
  def initialize(a,b,c)
    @width=a; @height=b; @depth=c
    @min=FakePoint.new
  end
end
class FakeEntities
  attr_reader :geometry
  def initialize(items=[], geometry=[])
    @items=items
    @geometry=geometry
  end
  def to_a; @items+@geometry; end
end
class FakeSelection
  def initialize(items); @items=items; end
  def to_a; @items; end
end
class FakeModel
  attr_accessor :selection
  def initialize(selected); @selection=FakeSelection.new(selected); end
end

module Sketchup
  class Group
    attr_accessor :name, :entities, :box, :attributes, :matrix
    def initialize(name='', children=[], expected=nil, mark=false)
      @name=name
      @entities=FakeEntities.new(children,expected ? MockPanelGeometry.box(*expected) : [])
      @attributes={'AI_IDEA'=>{}}
      @matrix=IDENTITY.dup
      if mark
        @attributes['AI_IDEA']['scene_schema']='ai-idea.scene.v1'
        @attributes['AI_IDEA']['manufacturing_approved']=false
        @attributes['AI_IDEA']['expected_parts_count']=children.length
        @attributes['AI_IDEA']['expected_root_name']=name
        @attributes['AI_IDEA']['expected_root_transform']=IDENTITY.dup
      else
        @attributes['AI_IDEA']['expected_part_id']=name
        @attributes['AI_IDEA']['expected_part_transform']=IDENTITY.dup
        @attributes['AI_IDEA']['expected_size_mm']=expected if expected
        @attributes['AI_IDEA']['expected_origin_mm']=[0.0,0.0,0.0]
        @attributes['AI_IDEA']['geometry_sha256']=AIIDEA::GeometryFingerprint.signature(@entities) if expected
      end
      @box=FakeBox.new(10.0,20.0,30.0)
    end
    def get_attribute(scope,key,default=nil)
      @attributes.fetch(scope,{}).fetch(key,default)
    end
    def transformation
      Struct.new(:to_a).new(@matrix)
    end
    def bounds; @box; end
  end
end

def check(label)
  raise "FAILED: #{label}" unless yield
end

part_a=Sketchup::Group.new('SIDE-L',[],[10,20,30])
part_b=Sketchup::Group.new('SIDE-R',[],[10,20,30])
parts=[part_a,part_b]
root=Sketchup::Group.new('AI IDEA DRAFT',parts,nil,true)
run=-> { AIIDEA::ModelAudit.audit(FakeModel.new([root])) }

check('1 baseline pass') { run.call['status']=='passed' }
check('2 no changes or approval') do
  result=run.call
  !result['model_changed'] && !result['manufacturing_approved'] && result['schema_version']=='ai-idea.model-audit.v3'
end

part_a.box.width=11.0
check('3 size drift') { run.call['errors'].any? { |e| e.include?('X size changed') } }
part_a.box.width=10.0

part_a.box.min.x=0.25
check('4 position drift') { run.call['errors'].any? { |e| e.include?('X origin shifted') } }
part_a.box.min.x=0.0

part_a.matrix[12]=0.1
check('5 part transformation changed') { run.call['errors'].any? { |e| e.include?('SIDE-L: transformation changed') } }
part_a.matrix[12]=0.0

root.matrix[0]=0.9
check('6 parent rotation/scale changed') { run.call['errors'].any? { |e| e.include?('Parent group: transformation changed') } }
root.matrix[0]=1.0

parts.pop
check('7 missing part') { run.call['status']=='failed' && run.call['inspected_panels']==1 }
parts << part_b

part_b.name='SIDE-L'
check('8 duplicate ID') { run.call['errors'].any? { |e| e.include?('Duplicate panel ID') } }
part_b.name='SIDE-R'

part_a.name='SIDE-L-renamed'
check('9 renamed panel ID') { run.call['errors'].any? { |e| e.include?('original panel ID changed') } }
part_a.name='SIDE-L'

root.name='Changed name'
check('10 renamed parent') { run.call['errors'].any? { |e| e.include?('Parent group: name changed') } }
root.name='AI IDEA DRAFT'

part_a.attributes['AI_IDEA'].delete('expected_origin_mm')
check('11 legacy missing origin must fail') { run.call['status']=='failed' && run.call['errors'].any? { |e| e.include?('reimport using V1.8') } }
part_a.attributes['AI_IDEA']['expected_origin_mm']=[0,0,0]

root.attributes['AI_IDEA']['expected_root_transform']=[1,2]
check('12 malformed transform metadata') { run.call['errors'].any? { |e| e.include?('missing valid transformation baseline') } }
root.attributes['AI_IDEA']['expected_root_transform']=IDENTITY.dup

baseline_digest=part_a.attributes['AI_IDEA']['geometry_sha256']
part_a.entities.geometry << MockPanelGeometry::Edge.new([1,1,30],[2,1,30])
check('13 interior edge changed but bounding box unchanged') {
  run.call['errors'].any? { |e| e.include?('SIDE-L: internal geometry changed') }
}
part_a.entities.geometry.pop
check('14 geometry restoration validates') {
  run.call['status']=='passed' && part_a.attributes['AI_IDEA']['geometry_sha256']==baseline_digest
}

part_b.attributes['AI_IDEA'].delete('geometry_sha256')
check('15 old draft missing digest fails closed') {
  run.call['errors'].any? { |e| e.include?('reimport using V1.9') }
}
part_b.attributes['AI_IDEA']['geometry_sha256']=AIIDEA::GeometryFingerprint.signature(part_b.entities)

check('16 empty selection rejected') do
  begin
    AIIDEA::ModelAudit.audit(FakeModel.new([]))
    false
  rescue ArgumentError
    true
  end
end

check('17 unmarked root rejected') do
  begin
    AIIDEA::ModelAudit.audit(FakeModel.new([Sketchup::Group.new('OTHER')]))
    false
  rescue ArgumentError
    true
  end
end

check('18 non-group geometry rejected') do
  parts << Object.new
  begin
    run.call
    false
  rescue ArgumentError
    true
  ensure
    parts.pop
  end
end
puts 'AI IDEA model audit mock: 18/18'
