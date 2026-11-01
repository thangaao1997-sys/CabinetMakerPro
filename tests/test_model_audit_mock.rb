require_relative '../plugin/ai_idea_v10/model_audit'

module Sketchup
  class Group
    attr_accessor :name, :entities, :box, :attributes
    def initialize(name='', children=[], expected=nil, mark=false)
      @name=name
      @entities=FakeEntities.new(children)
      @attributes={'AI_IDEA'=>{}}
      if mark
        @attributes['AI_IDEA']['scene_schema']='ai-idea.scene.v1'
        @attributes['AI_IDEA']['manufacturing_approved']=false
        @attributes['AI_IDEA']['expected_parts_count']=children.length
      end
      @attributes['AI_IDEA']['expected_size_mm']=expected if expected
      @box=FakeBox.new(10.0,20.0,30.0)
    end
    def get_attribute(scope,key,default=nil)
      @attributes.fetch(scope,{}).fetch(key,default)
    end
    def bounds; @box; end
  end
end
class Numeric
  def to_mm; self; end
end
class FakeBox
  attr_accessor :width,:height,:depth
  def initialize(a,b,c);@width=a;@height=b;@depth=c;end
end
class FakeEntities
  def initialize(items=[]);@items=items;end
  def to_a;@items;end
end
class FakeSelection
  def initialize(items);@items=items;end
  def to_a;@items;end
end
class FakeModel
  attr_accessor :selection
  def initialize(selected);@selection=FakeSelection.new(selected);end
end
def assert(condition,label)
  raise label unless condition
end

parts=[Sketchup::Group.new('SIDE-L',[],[10,20,30]),Sketchup::Group.new('SIDE-R',[],[10,20,30])]
root=Sketchup::Group.new('AI IDEA DRAFT',parts,nil,true)
report=AIIDEA::ModelAudit.audit(FakeModel.new([root]))
assert(report['status']=='passed','pass case')
assert(!report['model_changed'] && !report['manufacturing_approved'],'read-only and no production approval')
parts[0].box.width=11
report=AIIDEA::ModelAudit.audit(FakeModel.new([root]))
assert(report['status']=='failed' && report['errors'].any?{|m|m.include?('SIDE-L')},'dimension drift')
parts[0].box.width=10
parts.pop
report=AIIDEA::ModelAudit.audit(FakeModel.new([root]))
assert(report['status']=='failed','missing part')
parts << Sketchup::Group.new('SIDE-L',[],[10,20,30])
report=AIIDEA::ModelAudit.audit(FakeModel.new([root]))
assert(report['status']=='failed' && report['errors'].any?{|m|m.include?('Duplicate')},'duplicate ID')
begin
  AIIDEA::ModelAudit.audit(FakeModel.new([]))
  raise 'empty selection allowed'
rescue ArgumentError
end
begin
  AIIDEA::ModelAudit.audit(FakeModel.new([Sketchup::Group.new('OTHER')]))
  raise 'unmarked group allowed'
rescue ArgumentError
end
puts 'AI IDEA model audit mock: 7/7'
