require 'json'
module Sketchup
  def self.version; '25.0.0-MOCK'; end
end
require_relative '../plugin/ai_idea_v10/diagnostics'

report = AIIDEA::Diagnostics.collect
raise 'incorrect schema' unless report['schema_version'] == 'ai-idea.diagnostics.v1'
raise 'parser failed' unless report['scene_parser_valid']
raise 'unsafe mode' unless report['mode'] == 'read_only'
raise 'model mutated' unless report['model_changed'] == false
raise 'network started' unless report['network_started'] == false
raise 'approval incorrectly granted' unless report['manufacturing_approved'] == false
raise 'wrong version' unless report['sketchup_version'] == '25.0.0-MOCK'
puts 'AI IDEA diagnostic mock: 7/7'
