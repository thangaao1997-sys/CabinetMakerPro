require 'minitest/autorun'
require 'tmpdir'
require_relative '../workshop_plugin/ai_idea_workshop/inventory'

module Sketchup
  class Face
    attr_accessor :material, :back_material
    attr_reader :vertices
    def initialize(points)
      @vertices=points.map { |p| Struct.new(:position).new(Struct.new(:to_a).new(p)) }
    end
    def loops; [Struct.new(:vertices).new(@vertices)]; end
  end
  class ComponentInstance
    attr_accessor :material, :name, :hidden_value
    attr_reader :definition, :transformation, :persistent_id, :layer
    def initialize(id, definition, transform=AIIDEAWorkshop::Inventory::IDENTITY)
      @persistent_id=id; @definition=definition; @transformation=Struct.new(:to_a).new(transform)
      @name="Instance #{id}"; @hidden_value=false; @layer=Struct.new(:visible?).new(true)
    end
    def hidden?; @hidden_value; end
  end
  class Group < ComponentInstance; end
end

class WorkshopInventoryTests < Minitest::Test
  def definition(children)
    Struct.new(:name,:entities).new('Part definition',children)
  end
  def box
    # Coordinates are inches, as in the SketchUp API.
    vertices=[0,1].product([0,2],[0,3])
    faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]
    definition(faces.map { |ids| Sketchup::Face.new(ids.map { |i| vertices[i] }) })
  end
  def model(instances, context=nil)
    Struct.new(:entities,:active_path,:title).new(instances,context,'Sample')
  end
  def collect(instances)
    AIIDEAWorkshop::Inventory.collect(model(instances))
  end
  def test_shared_definition_is_counted_per_occurrence
    shared=box
    report=collect([Sketchup::Group.new(1,shared),Sketchup::ComponentInstance.new(2,shared)])
    assert_equal 2,report['instances'].length
    assert_equal [[1],[2]],report['instances'].map { |p| p['instance_path'] }
    [25.4,50.8,76.2].zip(report['instances'][0]['local_geometry_size_mm']).each { |a,b| assert_in_delta a,b,1e-8 }
    refute report['model_changed']
    refute report['manufacturing_approved']
  end
  def test_nested_rotation_and_scale_do_not_swap_local_panel_dimensions
    child=Sketchup::Group.new(2,box)
    # Rotate 90 degrees around Z and apply scales X=2, Y=3, Z=1.
    transform=[0,2,0,0,-3,0,0,0,0,0,1,0,10,0,0,1]
    parent=Sketchup::Group.new(1,definition([child]),transform)
    part=collect([parent])['instances'][0]
    assert_equal [1,2],part['instance_path']
    [50.8,152.4,76.2].zip(part['scaled_local_size_candidate_mm']).each { |a,b| assert_in_delta a,b,1e-8 }
    assert_in_delta 101.6,part['world_bounds_mm'][0]['min'],1e-8
    assert_in_delta 254.0,part['world_bounds_mm'][0]['max'],1e-8
  end
  def test_hidden_and_material_inheritance
    child=Sketchup::Group.new(2,box)
    parent=Sketchup::Group.new(1,definition([child]))
    parent.hidden_value=true
    parent.material=Struct.new(:display_name).new('MDF example')
    part=collect([parent])['instances'][0]
    assert part['hidden_including_ancestors']
    assert_equal 'MDF example',part['material_including_inheritance']
    refute part['production_part_verified']
  end
  def test_shear_not_reported_as_valid_scaled_dimensions
    transform=AIIDEAWorkshop::Inventory::IDENTITY.dup; transform[4]=0.5
    part=collect([Sketchup::Group.new(1,box,transform)])['instances'][0]
    assert_nil part['scaled_local_size_candidate_mm']
    assert part['warnings'].any? { |w| w.include?('Sheared') }
  end
  def test_mirrored_geometry_requires_face_orientation_review
    transform=AIIDEAWorkshop::Inventory::IDENTITY.dup;transform[0]=-1
    assert collect([Sketchup::Group.new(1,box,transform)])['instances'][0]['mirrored']
  end
  def test_edit_context_and_cycles_rejected
    assert_raises(RuntimeError) { AIIDEAWorkshop::Inventory.collect(model([],['editing'])) }
    children=[]; parent=Sketchup::Group.new(1,definition(children)); children<<parent
    assert_raises(RuntimeError) { collect([parent]) }
  end
  def test_export_is_repeatable_and_preserves_existing_file
    sample=model([Sketchup::Group.new(1,box)])
    first=AIIDEAWorkshop::Inventory.collect(sample)
    assert_equal first,AIIDEAWorkshop::Inventory.collect(sample)
    Dir.mktmpdir do |dir|
      path=File.join(dir,'inventory.json')
      AIIDEAWorkshop::Inventory.export_to(path,sample)
      bytes=File.binread(path)
      assert_equal first,JSON.parse(bytes)
      assert_raises(Errno::EEXIST) { AIIDEAWorkshop::Inventory.export_to(path,sample) }
      assert_equal bytes,File.binread(path)
    end
  end
  def test_loose_geometry_is_not_silently_counted_as_panel
    result=collect([Object.new])
    assert_empty result['instances']
    assert result['warnings'].any? { |w| w.include?('Root loose') }
  end
  def test_vertex_fingerprint_changes_when_geometry_changes
    shared=box; entity=Sketchup::Group.new(1,shared)
    first=collect([entity])['instances'][0]['local_vertex_coordinates_sha256']
    shared.entities[0].vertices[0].position.to_a[0]=0.1
    refute_equal first,collect([entity])['instances'][0]['local_vertex_coordinates_sha256']
  end
end
