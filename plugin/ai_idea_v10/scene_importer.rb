# encoding: UTF-8
# AI IDEA draft scene importer: only into a new, unsaved, empty model.
# No production approval, no CNC, and no remote network actions.
require 'json'
require_relative 'geometry_fingerprint'
module AIIDEA
  module SceneImporter
    module_function

    def finite_number(x, positive=false)
      x.is_a?(Numeric) && x.finite? && x >= 0 && (!positive || x > 0)
    end

    def parse_scene(text)
      data=JSON.parse(text)
      raise ArgumentError,'Invalid schema or units' unless data.is_a?(Hash) && data['schema_version']=='ai-idea.scene.v1' && data['units']=='mm'
      raise ArgumentError,'Approval forbidden' unless data['manufacturing_approved']==false
      rid=data['request_id']
      raise ArgumentError,'Invalid request ID' unless rid.is_a?(String) && !rid.strip.empty? && rid.length<=100
      env=data['envelope_mm']
      raise ArgumentError,'Invalid envelope' unless env.is_a?(Hash) && env.keys.sort==%w[depth height width]
      limits=%w[width depth height].map{|k|env[k]}
      raise ArgumentError,'Invalid envelope dimensions' unless limits.all?{|n|finite_number(n,true)}
      objects=data['objects']
      raise ArgumentError,'Invalid object count' unless objects.is_a?(Array) && objects.length.between?(1,2000)
      ids={};bounds=[]
      objects.each do |obj|
        raise ArgumentError,'Invalid ID' unless obj.is_a?(Hash) && obj['id'].is_a?(String) && !obj['id'].empty?
        raise ArgumentError,'Duplicate ID' if ids[obj['id']]
        ids[obj['id']]=true
        raise ArgumentError,'Unknown material' unless %w[panel back].include?(obj['material'])
        %w[origin_mm size_mm].each do |key|
          v=obj[key]
          raise ArgumentError,'Invalid vector' unless v.is_a?(Hash) && v.keys.sort==%w[x y z]
          raise ArgumentError,'Invalid dimension' unless %w[x y z].all?{|k|finite_number(v[k],key=='size_mm')}
        end
        pos=%w[x y z].map{|k|obj['origin_mm'][k]}
        size=%w[x y z].map{|k|obj['size_mm'][k]}
        raise ArgumentError,'Out of envelope' if (0..2).any?{|i|pos[i]+size[i]>limits[i]+0.0000001}
        bounds.each do |old_pos,old_size|
          intersects=(0..2).all?{|i|[pos[i]+size[i],old_pos[i]+old_size[i]].min-[pos[i],old_pos[i]].max>0.0000001}
          raise ArgumentError,'Overlapping solids' if intersects
        end
        bounds<<[pos,size]
      end
      data
    end

    def ensure_safe_target!(model)
      raise ArgumentError, 'No active SketchUp model' unless model
      required = [:entities, :active_entities, :active_path, :path, :get_attribute]
      raise ArgumentError, 'Cannot verify model safety' unless required.all? { |method| model.respond_to?(method) }
      raise ArgumentError, 'Open a NEW unsaved empty model for AI IDEA drafts' unless model.path.to_s.empty?
      raise ArgumentError, 'Exit group/component editing first' unless model.active_path.nil?
      root_entities = model.entities
      raise ArgumentError, 'Cannot verify root entities' unless root_entities.respond_to?(:to_a) && model.active_entities == root_entities
      raise ArgumentError, 'Current model is NOT empty; refusing to change it' unless root_entities.to_a.empty?
      locked = model.get_attribute('AI_IDEA', 'design_locked', false)
      raise ArgumentError, 'Model is explicitly locked' unless locked == false || locked.nil?
      true
    end

    def import_file(path)
      raise ArgumentError, 'Only a regular JSON file is accepted' unless File.file?(path) && !File.symlink?(path) && File.extname(path).downcase == '.json'
      raise ArgumentError, 'File too large' if File.size(path)>128_000
      scene=parse_scene(File.read(path,encoding:'UTF-8'))
      model=Sketchup.active_model
      ensure_safe_target!(model)
      model.start_operation('AI IDEA DRAFT Import',true)
      begin
        root=model.active_entities.add_group
        root.name="AI IDEA DRAFT - #{scene['request_id']}"
        root.set_attribute('AI_IDEA','manufacturing_approved',false)
        root.set_attribute('AI_IDEA','scene_schema','ai-idea.scene.v1')
        root.set_attribute('AI_IDEA','expected_parts_count',scene['objects'].length)
        # Persist original placement to detect subsequent movement/rotation.
        root.set_attribute('AI_IDEA','expected_root_transform',root.transformation.to_a)
        root.set_attribute('AI_IDEA','expected_root_name',root.name)
        scene['objects'].each do |obj|
          pos=%w[x y z].map{|k|obj['origin_mm'][k].mm}
          size=%w[x y z].map{|k|obj['size_mm'][k].mm}
          group=root.entities.add_group
          group.name=obj['id']
          group.set_attribute('AI_IDEA','role',obj['role'])
          group.set_attribute('AI_IDEA','material',obj['material'])
          group.set_attribute('AI_IDEA','expected_size_mm',%w[x y z].map{|axis|obj['size_mm'][axis]})
          group.set_attribute('AI_IDEA','expected_origin_mm',%w[x y z].map{|axis|obj['origin_mm'][axis]})
          group.set_attribute('AI_IDEA','expected_part_id',obj['id'])
          face=group.entities.add_face([[0,0,0],[size[0],0,0],[size[0],size[1],0],[0,size[1],0]])
          raise 'Face creation failed' unless face
          face.reverse! if face.normal.z<0
          face.pushpull(size[2])
          actual_geometry = AIIDEA::GeometryFingerprint.signature(group.entities)
          expected_geometry = AIIDEA::GeometryFingerprint.expected_box_signature(
            obj['size_mm']['x'], obj['size_mm']['y'], obj['size_mm']['z'])
          raise 'Panel geometry does not match requested rectangular prism' unless actual_geometry == expected_geometry
          group.transform!(Geom::Transformation.translation(pos))
          group.set_attribute('AI_IDEA','expected_part_transform',group.transformation.to_a)
          group.set_attribute('AI_IDEA','geometry_sha256',actual_geometry)
        end
        model.commit_operation
        root
      rescue StandardError
        model.abort_operation
        raise
      end
    end
  end
end
