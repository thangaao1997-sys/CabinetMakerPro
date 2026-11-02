require 'json'
require_relative '../plugin/ai_idea_v10/scene_importer'
require_relative 'support/mock_panel_geometry'

class Numeric
  def mm; self; end
end
module Geom
  class Transformation
    def self.translation(pos); pos; end
  end
end

class SafeMockFace
  def initialize(fail: false, parent: nil, points: nil)
    @fail=fail
    @parent=parent
    @points=points
  end
  def normal; Struct.new(:z).new(1); end
  def pushpull(height)
    raise 'forced PushPull failure' if @fail
    raise 'invalid height' unless height > 0
    width=@points[1][0]-@points[0][0]
    depth=@points[2][1]-@points[1][1]
    @parent.geometry=MockPanelGeometry.box(width,depth,height)
  end
end
class SafeMockGroup
  attr_accessor :name
  attr_reader :entities, :attributes
  def initialize(fail: false)
    @entities = SafeMockEntities.new(fail: fail)
    @attributes = {}
    @matrix = [1.0,0.0,0.0,0.0, 0.0,1.0,0.0,0.0, 0.0,0.0,1.0,0.0, 0.0,0.0,0.0,1.0]
  end
  def set_attribute(scope, key, value); @attributes[[scope,key]] = value; end
  def transformation; Struct.new(:to_a).new(@matrix); end
  def transform!(position)
    raise 'invalid position' unless position.length == 3
    @matrix[12, 3] = position
  end
end
class SafeMockEntities
  attr_reader :groups
  attr_accessor :geometry
  def initialize(fail: false)
    @groups=[]
    @geometry=[]
    @fail=fail
  end
  def add_group
    group = SafeMockGroup.new(fail: @fail)
    @groups << group
    group
  end
  def add_face(points)
    raise 'invalid face' unless points.length == 4
    SafeMockFace.new(fail: @fail, parent: self, points: points)
  end
  def to_a; @groups.dup+@geometry; end
end
class SafeMockModel
  attr_accessor :path, :active_path, :locked
  attr_reader :entities, :started, :committed, :aborted
  def initialize(fail: false)
    @entities = SafeMockEntities.new(fail: fail)
    @path = ''
    @active_path = nil
    @locked = false
    @started = false
    @committed = false
    @aborted = false
  end
  def active_entities; @entities; end
  def get_attribute(scope, key, default = nil)
    return @locked if [scope,key] == %w[AI_IDEA design_locked]
    default
  end
  def start_operation(*); @started = true; end
  def commit_operation; @committed = true; end
  def abort_operation
    @aborted = true
    @committed = false
    @entities.groups.clear
  end
end
module Sketchup
  class << self
    attr_accessor :active_model
  end
end

def assert(condition, message)
  raise message unless condition
end

def rejected_before_write(model, file)
  Sketchup.active_model = model
  before = model.entities.to_a.length
  begin
    AIIDEA::SceneImporter.import_file(file)
    raise 'Expected rejection'
  rescue ArgumentError
  end
  assert(!model.started, 'Rejected request started model operation')
  assert(model.entities.to_a.length == before, 'Rejected request changed root geometry')
end

fixture = File.expand_path('../examples/scene.json', __dir__)
model = SafeMockModel.new
Sketchup.active_model = model
root = AIIDEA::SceneImporter.import_file(fixture)
assert(model.started && model.committed, 'Normal import was not committed')
assert(root.entities.groups.size == 5, 'Normal import must create 5 panels')
assert(root.attributes[['AI_IDEA','manufacturing_approved']] == false, 'Draft flag wrong')
scene = JSON.parse(File.read(fixture, encoding: 'UTF-8'))
assert(root.attributes[['AI_IDEA','scene_schema']] == 'ai-idea.scene.v1', 'Missing scene schema metadata')
assert(root.attributes[['AI_IDEA','expected_parts_count']] == scene['objects'].size, 'Missing panel count metadata')
expected = scene['objects'].first['size_mm'].values_at('x','y','z')
assert(root.entities.groups.first.attributes[['AI_IDEA','expected_size_mm']] == expected, 'Panel dimensions not recorded')
assert(root.attributes[['AI_IDEA','expected_root_name']] == root.name, 'Root name baseline missing')
assert(root.attributes[['AI_IDEA','expected_root_transform']].length == 16, 'Root matrix baseline missing')
assert(root.entities.groups.first.attributes[['AI_IDEA','expected_part_id']] == scene['objects'].first['id'], 'Panel ID baseline missing')
assert(root.entities.groups.first.attributes[['AI_IDEA','expected_origin_mm']] ==
  scene['objects'].first['origin_mm'].values_at('x','y','z'), 'Panel origin baseline missing')
assert(root.entities.groups.first.attributes[['AI_IDEA','expected_part_transform']].length == 16, 'Panel transform baseline missing')
fingerprint = root.entities.groups.first.attributes[['AI_IDEA','geometry_sha256']]
assert(fingerprint.is_a?(String) && fingerprint.match?(/\A[0-9a-f]{64}\z/), 'Missing local geometry digest')
assert(fingerprint == AIIDEA::GeometryFingerprint.signature(root.entities.groups.first.entities), 'Digest mismatch')


populated = SafeMockModel.new
populated.entities.add_group
rejected_before_write(populated, fixture)

saved = SafeMockModel.new
saved.path = 'client_model.skp'
rejected_before_write(saved, fixture)

editing = SafeMockModel.new
editing.active_path = ['inside-group']
rejected_before_write(editing, fixture)

locked = SafeMockModel.new
locked.locked = true
rejected_before_write(locked, fixture)

broken = SafeMockModel.new(fail: true)
Sketchup.active_model = broken
begin
  AIIDEA::SceneImporter.import_file(fixture)
  raise 'Expected PushPull error'
rescue RuntimeError => e
  raise if e.message == 'Expected PushPull error'
end
assert(broken.aborted && !broken.committed, 'Failed import did not abort transaction')
assert(broken.entities.groups.empty?, 'Failed import left geometry')

Sketchup.active_model = Object.new
begin
  AIIDEA::SceneImporter.import_file(fixture)
  raise 'Expected fail-closed behavior'
rescue ArgumentError
end

puts 'AI IDEA model-protection smoke: 10/10'
