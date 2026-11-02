# encoding: UTF-8
require 'sketchup.rb'
require 'extensions.rb'
module AIIDEAWorkshop
  unless @reader_registered
    extension=SketchupExtension.new('AI IDEA - Workshop Reader','ai_idea_workshop/main')
    extension.description='Read-only workshop geometry inventory; no CNC output or model changes.'
    extension.version='0.1.0'
    extension.creator='AI IDEA'
    Sketchup.register_extension(extension,false)
    @reader_registered=true
  end
end
