# encoding: UTF-8
require 'sketchup.rb'
require_relative 'scene_importer'
require_relative 'diagnostics'
require_relative 'model_audit'
require_relative 'self_test'
module AIIDEA
  unless defined?(@menu_registered) && @menu_registered
    UI.menu('Extensions').add_item('AI IDEA - Import DRAFT scene (JSON)') do
      file=UI.openpanel('Select AI IDEA DRAFT scene',nil,'JSON Files|*.json||')
      next unless file
      begin
        root=AIIDEA::SceneImporter.import_file(file)
        UI.messagebox("AI IDEA: Imported draft #{root.name}. Not approved for manufacturing.")
      rescue StandardError => e
        UI.messagebox("AI IDEA import failed: #{e.class}: #{e.message}")
      end
    end
    UI.menu('Extensions').add_item('AI IDEA - Diagnostics (READ ONLY)') do
      begin
        AIIDEA::Diagnostics.run_gui
      rescue StandardError => e
        UI.messagebox("AI IDEA diagnostics failed: #{e.class}: #{e.message}")
      end
    end
    UI.menu('Extensions').add_item('AI IDEA - Audit selected DRAFT (READ ONLY)') do
      begin
        AIIDEA::ModelAudit.run_gui
      rescue StandardError => e
        UI.messagebox("AI IDEA model audit failed: #{e.class}: #{e.message}")
      end
    end
    UI.menu('Extensions').add_item('AI IDEA - Self-test in EMPTY model (ABORT)') do
      begin
        AIIDEA::SelfTest.run_gui
      rescue StandardError => e
        UI.messagebox("AI IDEA self-test failed: #{e.class}: #{e.message}")
      end
    end
    @menu_registered=true
  end
end
