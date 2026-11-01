# encoding: UTF-8
# Mock only: checks menu registration and the user-triggered read-only action.
$LOADED_FEATURES << 'sketchup.rb'

module Sketchup
  def self.version
    '25.0.0-MOCK'
  end
end

module UI
  class Menu
    attr_reader :callbacks
    def initialize
      @callbacks = {}
    end
    def add_item(label, &block)
      @callbacks[label] = block
    end
  end
  @menus = {}
  @messages = []
  class << self
    attr_reader :messages
    def menu(name)
      @menus[name] ||= Menu.new
    end
    def messagebox(msg)
      @messages << msg
    end
    def savepanel(*)
      nil
    end
  end
end

require_relative '../plugin/ai_idea_v10/main'

callbacks = UI.menu('Extensions').callbacks
raise 'Import menu missing' unless callbacks.key?('AI IDEA - Import DRAFT scene (JSON)')
raise 'Diagnostic menu missing' unless callbacks.key?('AI IDEA - Diagnostics (READ ONLY)')
callbacks['AI IDEA - Diagnostics (READ ONLY)'].call
raise 'Diagnostic message missing' unless UI.messages.any? { |msg| msg.include?('No model changes performed') }
puts 'AI IDEA menu smoke mock: 3/3'
