# encoding: UTF-8
# AI IDEA read-only diagnostics: no model modification, no CNC, no network.
require 'json'
require_relative 'scene_importer'

module AIIDEA
  module Diagnostics
    module_function

    def fixture
      {
        'schema_version' => 'ai-idea.scene.v1',
        'units' => 'mm',
        'request_id' => 'DIAGNOSTIC-NO-WRITE',
        'manufacturing_approved' => false,
        'envelope_mm' => {'width' => 20, 'depth' => 20, 'height' => 20},
        'objects' => [{
          'id' => 'TEST-BOX', 'role' => 'diagnostic', 'material' => 'panel',
          'origin_mm' => {'x' => 0, 'y' => 0, 'z' => 0},
          'size_mm' => {'x' => 10, 'y' => 10, 'z' => 10}
        }]
      }
    end

    def collect
      version = Sketchup.respond_to?(:version) ? Sketchup.version.to_s : 'unavailable'
      parsed = AIIDEA::SceneImporter.parse_scene(JSON.generate(fixture))
      {
        'schema_version' => 'ai-idea.diagnostics.v1',
        'mode' => 'read_only',
        'sketchup_version' => version,
        'ruby_version' => RUBY_VERSION,
        'scene_parser_valid' => parsed['objects'].length == 1,
        'actual_geometry_created' => false,
        'model_changed' => false,
        'manufacturing_approved' => false,
        'network_started' => false
      }
    end

    def run_gui
      report = collect
      summary = "AI IDEA diagnostic (READ ONLY)\n" +
                "SketchUp: #{report['sketchup_version']}\n" +
                "Ruby: #{report['ruby_version']}\n" +
                "JSON parser: #{report['scene_parser_valid'] ? 'OK' : 'FAIL'}\n" +
                "No model changes performed."
      UI.messagebox(summary)
      # The user decides whether to save a sanitized report.
      file = UI.savepanel('Save AI IDEA diagnostic report (optional)', nil,
                          'AI_IDEA_DIAGNOSTICS.json')
      if file
        raise 'Only JSON files are supported' unless File.extname(file).downcase == '.json'
        File.open(file, 'w:UTF-8') do |f|
          f.write(JSON.pretty_generate(report) + "\n")
        end
      end
      report
    end
  end
end
