# encoding: UTF-8
# Isolated Ruby simulation; never claims that SketchUp was actually launched.
require_relative 'support/mock_panel_geometry'
MB_YESNO = 4 unless defined?(MB_YESNO)
IDYES = 6 unless defined?(IDYES)

module Geom
  class Transformation
    def self.translation(pos); pos; end
  end
end
class Numeric
  def mm; self; end
end

class SmokeFace
  def initialize(owner, points)
    @owner=owner
    @points=points
  end
  def normal; Struct.new(:z).new(1); end
  def pushpull(height)
    x=@points[1][0]-@points[0][0]
    y=@points[2][1]-@points[1][1]
    @owner.geometry=MockPanelGeometry.box(x,y,height)
    @owner.owner.sizes=[x,y,height]
    if @owner.owner.fail_geometry
      @owner.geometry << MockPanelGeometry::Edge.new([2,2,height],[3,2,height])
    end
  end
end
class SmokeBox
  attr_reader :width, :height, :depth, :min
  def initialize(sizes,origin)
    @width,@height,@depth=*sizes
    @min=Struct.new(:x,:y,:z).new(*origin)
  end
end
class SmokeEntities
  attr_reader :owner, :groups
  attr_accessor :geometry
  def initialize(owner=nil)
    @owner=owner
    @groups=[]
    @geometry=[]
  end
  def add_group
    group=SmokeGroup.new(@owner.is_a?(SmokeModel) ? @owner.fail_geometry : @owner.fail_geometry)
    @groups<<group
    group
  end
  def add_face(points)
    SmokeFace.new(self,points)
  end
  def to_a
    @groups+@geometry
  end
end
module Sketchup
  class Group; end
  def self.version; '25.0-MOCK'; end
end
class SmokeGroup < Sketchup::Group
  attr_accessor :name,:sizes
  attr_reader :entities,:fail_geometry
  def initialize(fail_geometry=false)
    @fail_geometry=fail_geometry
    @entities=SmokeEntities.new(self)
    @attributes={}
    @sizes=[0,0,0]
    @offset=[0,0,0]
    @matrix=[1.0,0,0,0, 0,1.0,0,0, 0,0,1.0,0, 0,0,0,1.0]
  end
  def get_attribute(scope,key,default=nil);@attributes.fetch([scope,key],default);end
  def set_attribute(scope,key,value);@attributes[[scope,key]]=value;end
  def transformation;Struct.new(:to_a).new(@matrix);end
  def transform!(offset)
    @offset=offset
    @matrix[12,3]=offset
  end
  def bounds; SmokeBox.new(@sizes,@offset); end
end
class SmokeModel
  attr_accessor :path,:active_path,:design_locked
  attr_reader :entities,:started,:aborted,:committed
  def initialize(fail_geometry:false)
    @fail_geometry=fail_geometry
    @entities=SmokeEntities.new(self)
    @path=''
    @active_path=nil
    @design_locked=false
    @started=false
    @aborted=false
    @committed=false
  end
  def fail_geometry;@fail_geometry;end
  def active_entities;@entities;end
  def get_attribute(scope,key,default=nil)
    [scope,key]==['AI_IDEA','design_locked'] ? @design_locked : default
  end
  def start_operation(*);@started=true;true;end
  def abort_operation
    @aborted=true
    @entities.groups.clear
  end
  def commit_operation;@committed=true;end
end
module Sketchup
  class << self
    attr_accessor :active_model
  end
end

module UI
  @response=IDYES
  @messages=[]
  class << self
    attr_accessor :response
    attr_reader :messages
    def messagebox(message, *_args)
      @messages << message
      @response
    end
  end
end

require_relative '../plugin/ai_idea_v10/self_test'

def expect(label)
  raise label unless yield
end

new_model=SmokeModel.new
result=AIIDEA::SelfTest.run(new_model)
expect('1 geometry and audit pass') { result['status']=='passed' && result['geometry_audit']=='passed' }
expect('2 result is non-production') { result['manufacturing_approved']==false && result['network_started']==false }
expect('3 transaction aborted and cleared') { new_model.started && new_model.aborted && !new_model.committed && new_model.entities.to_a.empty? }

populated=SmokeModel.new
populated.entities.add_group
begin
  AIIDEA::SelfTest.run(populated)
  raise 'expected nonempty gate rejection'
rescue ArgumentError
end
expect('4 populated model untouched') { !populated.started && populated.entities.to_a.length==1 }

saved=SmokeModel.new
saved.path='customer.skp'
begin;AIIDEA::SelfTest.run(saved);raise 'expected path rejection';rescue ArgumentError;end
expect('5 saved model untouched') { !saved.started }

locked=SmokeModel.new
locked.design_locked=true
begin;AIIDEA::SelfTest.run(locked);raise 'expected lock rejection';rescue ArgumentError;end
expect('6 locked model untouched') { !locked.started }

editing=SmokeModel.new
editing.active_path=['component']
begin;AIIDEA::SelfTest.run(editing);raise 'expected edit-context rejection';rescue ArgumentError;end
expect('7 edit context untouched') { !editing.started }

bad=SmokeModel.new(fail_geometry:true)
begin
  AIIDEA::SelfTest.run(bad)
  raise 'expected shape mismatch rejection'
rescue RuntimeError => e
  raise if e.message=='expected shape mismatch rejection'
end
expect('8 shape failure rolled back') { bad.started && bad.aborted && bad.entities.to_a.empty? }

cancelled=SmokeModel.new
Sketchup.active_model=cancelled
UI.response=0
report=AIIDEA::SelfTest.run_gui
expect('9 UI cancellation safe') { report['status']=='cancelled' && !cancelled.started }

confirmed=SmokeModel.new
Sketchup.active_model=confirmed
UI.response=IDYES
report=AIIDEA::SelfTest.run_gui
expect('10 UI confirmed disposable test') { report['status']=='passed' && confirmed.aborted && confirmed.entities.to_a.empty? }
puts 'AI IDEA disposable SketchUp self-test mock: 10/10'
