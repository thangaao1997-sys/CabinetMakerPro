# AI IDEA DRAFT scene importer: not production approved, no CNC.
require 'json'
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
    def import_file(path)
      raise ArgumentError,'File too large' if File.size(path)>128_000
      scene=parse_scene(File.read(path,encoding:'UTF-8'))
      model=Sketchup.active_model
      raise 'No active model' unless model
      model.start_operation('AI IDEA DRAFT Import',true)
      begin
        root=model.active_entities.add_group
        root.name="AI IDEA DRAFT - #{scene['request_id']}"
        root.set_attribute('AI_IDEA','manufacturing_approved',false)
        scene['objects'].each do |obj|
          pos=%w[x y z].map{|k|obj['origin_mm'][k].mm}
          size=%w[x y z].map{|k|obj['size_mm'][k].mm}
          group=root.entities.add_group
          group.name=obj['id']
          group.set_attribute('AI_IDEA','role',obj['role'])
          group.set_attribute('AI_IDEA','material',obj['material'])
          face=group.entities.add_face([[0,0,0],[size[0],0,0],[size[0],size[1],0],[0,size[1],0]])
          raise 'Face creation failed' unless face
          face.reverse! if face.normal.z<0
          face.pushpull(size[2])
          group.transform!(Geom::Transformation.translation(pos))
        end
        model.commit_operation
        root
      rescue Exception
        model.abort_operation
        raise
      end
    end
  end
end
