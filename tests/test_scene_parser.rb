require 'json'
require_relative '../sketchup/ai_idea_scene_importer'
s=JSON.parse(File.read(File.expand_path('../examples/scene.json',__dir__)))
raise 'expected 5 objects' unless AIIDEA::SceneImporter.parse_scene(JSON.generate(s))['objects'].length==5
changes=[
  ->(v){v['manufacturing_approved']=true},
  ->(v){v['schema_version']='bad'},
  ->(v){v['objects'][0]['size_mm']['x']=-1},
  ->(v){v['objects'][1]['id']=v['objects'][0]['id']},
  ->(v){v['objects'][0]['origin_mm']['x']='bad'},
  ->(v){v['objects'][0]['origin_mm']['x']=900},
  ->(v){v['objects'][1]['origin_mm']['x']=10}
]
changes.each do |change|
  v=Marshal.load(Marshal.dump(s));change.call(v)
  begin
    AIIDEA::SceneImporter.parse_scene(JSON.generate(v))
    raise 'Expected parser rejection'
  rescue ArgumentError
  end
end
puts 'Ruby draft scene parser: 8/8'
