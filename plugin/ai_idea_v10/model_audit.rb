# encoding: UTF-8
# Read-only inspection of AI IDEA draft group dimensions in SketchUp.
# Checks one explicitly selected draft root; never changes geometry.
require 'json'
module AIIDEA
  module ModelAudit
    module_function

    TOLERANCE_MM = 0.10

    def audit(model)
      raise ArgumentError, 'No active SketchUp model' unless model && model.respond_to?(:selection)
      selected = model.selection.to_a
      raise ArgumentError, 'Select exactly ONE AI IDEA DRAFT parent group' unless selected.size == 1
      root = selected.first
      raise ArgumentError, 'Selected item is not a SketchUp group' unless root.is_a?(Sketchup::Group)
      marker = root.get_attribute('AI_IDEA', 'scene_schema', nil)
      raise ArgumentError, 'Selected group is not a V1.7 AI IDEA draft' unless marker == 'ai-idea.scene.v1'
      raise ArgumentError, 'Manufacturing approval is not allowed' unless root.get_attribute('AI_IDEA', 'manufacturing_approved', nil) == false
      expected_count = root.get_attribute('AI_IDEA', 'expected_parts_count', nil)
      raise ArgumentError, 'Missing expected part count' unless expected_count.is_a?(Integer) && expected_count > 0
      entities = root.entities.to_a
      raise ArgumentError, 'Non-group geometry found under draft root' unless entities.all? { |part| part.is_a?(Sketchup::Group) }
      errors = []
      errors << "Expected #{expected_count} panels, found #{entities.length}" if entities.length != expected_count
      seen_names = {}
      entities.each do |part|
        name = part.name.to_s
        errors << 'Unnamed part found' if name.empty?
        errors << "Duplicate panel ID: #{name}" if seen_names[name]
        seen_names[name] = true
        expected = part.get_attribute('AI_IDEA', 'expected_size_mm', nil)
        unless expected.is_a?(Array) && expected.length == 3 && expected.all? { |v| v.is_a?(Numeric) && v.finite? && v > 0 }
          errors << "#{name}: missing valid size metadata"
          next
        end
        begin
          box = part.bounds
          actual = [box.width, box.height, box.depth].map { |length| length.to_mm.to_f }
        rescue StandardError
          errors << "#{name}: cannot determine bounding box"
          next
        end
        unless actual.all? { |v| v.finite? && v > 0 }
          errors << "#{name}: invalid or empty bounding box"
          next
        end
        (0..2).each do |index|
          delta = (actual[index] - expected[index]).abs
          errors << "#{name}: #{%w[X Y Z][index]} differs by #{delta.round(3)} mm" if delta > TOLERANCE_MM
        end
      end
      {
        'schema_version' => 'ai-idea.model-audit.v1',
        'mode' => 'read_only',
        'status' => errors.empty? ? 'passed' : 'failed',
        'expected_panels' => expected_count,
        'inspected_panels' => entities.length,
        'tolerance_mm' => TOLERANCE_MM,
        'errors' => errors,
        'model_changed' => false,
        'manufacturing_approved' => false
      }
    end

    def run_gui
      report = audit(Sketchup.active_model)
      message = "AI IDEA DRAFT size audit: #{report['status'].upcase}\n" +
                "Panels: #{report['inspected_panels']}/#{report['expected_panels']}\n" +
                "Tolerance: #{report['tolerance_mm']} mm\n" +
                (report['errors'].empty? ? 'No dimension discrepancies detected.' : report['errors'].first(8).join("\n")) +
                "\nREAD ONLY. Not approved for manufacturing."
      UI.messagebox(message)
      report
    end
  end
end
