require 'json'
require_relative '../sketchup/ai_idea_scene_importer'
class Numeric; def mm; self; end; end
module Geom
  class Transformation
    def self.translation(x);x;end
  end
end
class MockFace
  def normal; Struct.new(:z).new(1); end
  def pushpull(v);raise 'invalid thickness' unless v>0;end
end
class MockGroup
  attr_accessor :name
  attr_reader :entities,:attrs
  def initialize;@entities=MockEntities.new;@attrs={};end
  def set_attribute(g,k,v);@attrs[[g,k]]=v;end
  def transform!(v);raise 'invalid translation' unless v.size==3;end
end
class MockEntities
  attr_reader :groups
  def initialize;@groups=[];end
  def add_group;g=MockGroup.new;@groups<<g;g;end
  def add_face(v);raise 'invalid face' unless v.size==4;MockFace.new;end
end
class MockModel
  attr_reader :active_entities,:started,:committed
  def initialize;@active_entities=MockEntities.new;@started=false;@committed=false;end
  def start_operation(*);@started=true;end
  def commit_operation;@committed=true;end
  def abort_operation;@committed=false;end
end
module Sketchup
  def self.active_model;@model ||= MockModel.new;end
end
root=AIIDEA::SceneImporter.import_file(File.expand_path('../examples/scene.json',__dir__))
raise 'missing root' unless Sketchup.active_model.active_entities.groups.size==1
raise 'missing parts' unless root.entities.groups.size==5
raise 'not a draft' unless root.attrs[['AI_IDEA','manufacturing_approved']]==false
raise 'transaction not committed' unless Sketchup.active_model.started && Sketchup.active_model.committed
puts 'Mock SketchUp import: 4/4'
