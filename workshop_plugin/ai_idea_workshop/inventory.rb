# encoding: UTF-8
require 'json'
require 'digest'

module AIIDEAWorkshop
  module Inventory
    module_function
    IDENTITY = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1].freeze

    def matrix(value)
      a = value.to_a
      raise 'Invalid instance transformation' unless a.length == 16 && a.all? { |n| n.is_a?(Numeric) && n.finite? }
      raise 'Unsupported projective transformation' unless [3,7,11].all? { |i| a[i].abs < 1e-9 } && (a[15]-1).abs < 1e-9
      a
    end

    def multiply(a, b)
      (0...16).map { |i| col=i/4; row=i%4; (0...4).sum { |k| a[k*4+row]*b[col*4+k] } }
    end

    def transform(p, m)
      (0..2).map { |r| m[r]*p[0]+m[4+r]*p[1]+m[8+r]*p[2]+m[12+r] }
    end

    def material_name(material)
      material ? material.display_name.to_s : nil
    end

    def instance?(entity)
      entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)
    end

    def collect(model)
      raise 'No model' unless model
      raise 'Exit group/component editing before export' unless model.active_path.nil?
      state = { 'instances'=>[], 'warnings'=>[], 'node_count'=>0, 'vertex_count'=>0 }
      root_geometry = model.entities.to_a.reject { |e| instance?(e) }
      state['warnings'] << 'Root loose geometry is not treated as a cabinet panel' if root_geometry.any?
      model.entities.to_a.select { |e| instance?(e) }.each do |e|
        visit(e, IDENTITY, [], [], nil, false, state)
      end
      report = {
        'schema_version'=>'ai-idea.sketchup-workshop-inventory.v1',
        'model_title'=>model.title.to_s, 'units'=>'mm',
        'coordinate_space'=>'world', 'transform_translation_units'=>'inches',
        'instances'=>state['instances'], 'warnings'=>state['warnings'],
        'model_changed'=>false, 'manufacturing_approved'=>false,
        'scope'=>'Read-only geometry candidates, not approved parts or machining instructions'
      }
      report['snapshot_sha256'] = Digest::SHA256.hexdigest(JSON.generate(report))
      report
    end

    def visit(entity, parent_matrix, parent_path, ancestors, inherited_material, ancestor_hidden, state)
      state['node_count'] += 1
      raise 'Inventory exceeds 20000 instances' if state['node_count'] > 20000
      raise 'Inventory nesting exceeds 32 levels' if parent_path.length >= 32
      definition = entity.definition
      raise 'Cyclic component definition' if ancestors.include?(definition.object_id)
      path = parent_path + [entity.persistent_id]
      world = multiply(parent_matrix, matrix(entity.transformation))
      hidden = ancestor_hidden || entity.hidden? || !entity.layer.visible?
      material = material_name(entity.material) || inherited_material
      contents = definition.entities.to_a
      children = contents.select { |e| instance?(e) }
      faces = contents.select { |e| e.is_a?(Sketchup::Face) }
      if faces.any?
        loops_mm = faces.map { |f| f.loops.map { |loop| loop.vertices.map { |v| v.position.to_a.map { |n| n.to_f*25.4 } } } }
        points = faces.flat_map { |f| f.vertices.map { |v| v.position.to_a.map(&:to_f) } }.uniq.sort
        state['vertex_count'] += points.length
        raise 'Inventory exceeds 500000 face vertices' if state['vertex_count'] > 500000
        raise 'Nonfinite vertex coordinate' unless points.all? { |p| p.length == 3 && p.all?(&:finite?) }
        minimum=(0..2).map { |i| points.map { |p| p[i] }.min }
        maximum=(0..2).map { |i| points.map { |p| p[i] }.max }
        axes=(0..2).map { |c| (0..2).map { |r| world[c*4+r] } }
        scale=axes.map { |v| Math.sqrt(v.sum { |n| n*n }) }
        shear=(0..2).to_a.combination(2).any? do |i,j|
          scale[i] <= 1e-12 || scale[j] <= 1e-12 ||
            ((0..2).sum { |k| axes[i][k]*axes[j][k] }/(scale[i]*scale[j])).abs > 1e-7
        end
        determinant = axes[0][0]*(axes[1][1]*axes[2][2]-axes[1][2]*axes[2][1]) -
          axes[1][0]*(axes[0][1]*axes[2][2]-axes[0][2]*axes[2][1]) +
          axes[2][0]*(axes[0][1]*axes[1][2]-axes[0][2]*axes[1][1])
        world_points=points.map { |p| transform(p,world).map { |n| n*25.4 } }
        materials=faces.flat_map { |f| [material_name(f.material),material_name(f.back_material)] }.compact.uniq.sort
        warnings=[]
        warnings << 'Hidden instance or layer; do not auto-release' if hidden
        warnings << 'Mixed nested geometry and direct faces' if children.any?
        warnings << 'Sheared or singular transform; dimensions require review' if shear || scale.any? { |s| s <= 1e-12 }
        warnings << 'Mirrored transform; machining face orientation requires review' if determinant < 0
        warnings << 'Multiple face materials require review' if materials.length > 1
        warnings << 'No explicit material' if material.nil? && materials.empty?
        warnings << 'No verified edge banding, grain or machining face mapping'
        state['instances'] << {
          'instance_path'=>path, 'instance_name'=>entity.name.to_s, 'definition_name'=>definition.name.to_s,
          'world_transform'=>world, 'local_geometry_size_mm'=>(0..2).map { |i| (maximum[i]-minimum[i])*25.4 },
          'scaled_local_size_candidate_mm'=>shear ? nil : (0..2).map { |i| (maximum[i]-minimum[i])*scale[i]*25.4 },
          'world_bounds_mm'=>(0..2).map { |i| { 'min'=>world_points.map { |p| p[i] }.min, 'max'=>world_points.map { |p| p[i] }.max } },
          'material_including_inheritance'=>material, 'explicit_face_materials'=>materials,
          'hidden_including_ancestors'=>hidden, 'mirrored'=>determinant < 0,
          'face_count'=>faces.length, 'unique_vertex_count'=>points.length,
          'face_loops_local_mm'=>loops_mm,
          'face_loops_sha256'=>Digest::SHA256.hexdigest(JSON.generate(loops_mm)),
          'local_vertex_coordinates_sha256'=>Digest::SHA256.hexdigest(JSON.generate(points)),
          'warnings'=>warnings, 'production_part_verified'=>false
        }
      end
      children.each { |child| visit(child,world,path,ancestors+[definition.object_id],material,hidden,state) }
    end

    def export_to(path, model)
      raise 'Choose a new JSON file' unless File.extname(path).downcase == '.json'
      report=collect(model)
      payload=JSON.pretty_generate(report)+"\n"
      File.open(path,File::WRONLY | File::CREAT | File::EXCL,0o600) { |f| f.write(payload) }
      report
    end

    def run_gui
      path=UI.savepanel('Export workshop inventory — READ ONLY model',nil,'IDEA_WORKSHOP_INVENTORY.json')
      return unless path
      result=export_to(path,Sketchup.active_model)
      UI.messagebox("Exported #{result['instances'].length} geometry candidates. Model unchanged. NOT approved for CNC.")
    rescue StandardError => e
      UI.messagebox("Workshop inventory failed: #{e.message}")
    end
  end
end
