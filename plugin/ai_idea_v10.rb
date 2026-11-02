# encoding: UTF-8
require 'sketchup.rb'
require 'extensions.rb'
module AIIDEA
  unless defined?(@extension_registered) && @extension_registered
    ext=SketchupExtension.new('AI IDEA V1.9.3 (DRAFT)', 'ai_idea_v10/main')
    ext.description='Manual import of verified draft scenes; no CNC or background network service.'
    ext.version='1.9.3-alpha'
    ext.creator='AI IDEA'
    Sketchup.register_extension(ext,false)
    @extension_registered=true
  end
end
