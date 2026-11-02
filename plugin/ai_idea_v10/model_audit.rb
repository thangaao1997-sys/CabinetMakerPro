# encoding: UTF-8
# AI IDEA V1.8 read-only integrity audit of a selected DRAFT SketchUp group.
# Detects edits to size, placement, identity and parent/part transformation.
require_relative 'geometry_fingerprint'
require 'json'
module AIIDEA
  module ModelAudit
    module_function

    TOLERANCE_MM = 0.10
    # SketchUp transformation matrices hold their translation as inch values.
    MATRIX_TRANSLATION_TOLERANCE = TOLERANCE_MM / 25.4
    MATRIX_AXIS_TOLERANCE = 0.000001

    def finite_numbers?(values, length, positive: false)
      values.is_a?(Array) && values.length == length &&
        values.all? { |v| v.is_a?(Numeric) && v.finite? && (!positive || v > 0) }
    end

    def inspect_transform(instance, expected, label, errors)
      unless finite_numbers?(expected, 16)
        errors << "#{label}: missing valid transformation baseline (reimport using V1.8)"
        return
      end

      begin
        matrix = instance.transformation.to_a
        unless finite_numbers?(matrix, 16)
          errors << "#{label}: invalid transformation"
          return
        end
        matrix.each_index do |index|
          limit = (12..14).cover?(index) ? MATRIX_TRANSLATION_TOLERANCE : MATRIX_AXIS_TOLERANCE
          if (matrix[index] - expected[index]).abs > limit
            errors << "#{label}: transformation changed"
            break
          end
        end
      rescue StandardError
        errors << "#{label}: cannot inspect transformation"
      end
    end

    def audit(model)
      raise ArgumentError, 'No active SketchUp model' unless model && model.respond_to?(:selection)
      selected = model.selection.to_a
      raise ArgumentError, 'Select exactly ONE AI IDEA DRAFT parent group' unless selected.size == 1
      audit_root(selected.first)
    end

    # Audit an explicit parent group without changing the current selection.
    # Used by the disposable in-SketchUp self-test.
    def audit_root(root)
      raise ArgumentError, 'Selected item is not a SketchUp group' unless root.is_a?(Sketchup::Group)

      marker = root.get_attribute('AI_IDEA', 'scene_schema', nil)
      raise ArgumentError, 'Selected group is not an AI IDEA scene draft' unless marker == 'ai-idea.scene.v1'
      raise ArgumentError, 'Manufacturing approval is not allowed' unless root.get_attribute('AI_IDEA', 'manufacturing_approved', nil) == false
      expected_count = root.get_attribute('AI_IDEA', 'expected_parts_count', nil)
      raise ArgumentError, 'Missing expected part count' unless expected_count.is_a?(Integer) && expected_count > 0

      entities = root.entities.to_a
      raise ArgumentError, 'Non-group geometry found under draft root' unless entities.all? { |part| part.is_a?(Sketchup::Group) }

      errors = []
      errors << "Expected #{expected_count} panels, found #{entities.length}" if entities.length != expected_count

      expected_root_name = root.get_attribute('AI_IDEA', 'expected_root_name', nil)
      if !expected_root_name.is_a?(String) || expected_root_name.empty?
        errors << 'Parent group: missing original name metadata'
      elsif root.name != expected_root_name
        errors << 'Parent group: name changed'
      end
      inspect_transform(root, root.get_attribute('AI_IDEA', 'expected_root_transform', nil), 'Parent group', errors)

      seen_names = {}
      panels = []
      entities.each do |part|
        name = part.name.to_s
        first_error = errors.length
        panel = { 'name' => name, 'expected_size_mm' => nil, 'expected_origin_mm' => nil,
                  'actual_size_mm' => nil, 'actual_origin_mm' => nil,
                  'size_delta_mm' => nil, 'origin_delta_mm' => nil }
        panels << panel
        begin
          errors << 'Unnamed part found' if name.empty?
          errors << "Duplicate panel ID: #{name}" if seen_names[name]
          seen_names[name] = true

          expected_id = part.get_attribute('AI_IDEA', 'expected_part_id', nil)
          if !expected_id.is_a?(String) || expected_id.empty?
            errors << "#{name}: missing original part ID"
          elsif name != expected_id
            errors << "#{name}: original panel ID changed"
          end

          inspect_transform(part, part.get_attribute('AI_IDEA', 'expected_part_transform', nil), name, errors)

          expected_digest = part.get_attribute('AI_IDEA', 'geometry_sha256', nil)
          unless expected_digest.is_a?(String) && expected_digest.match?(/\A[0-9a-f]{64}\z/)
            errors << "#{name}: missing valid geometric fingerprint (reimport using V1.9)"
          else
            begin
              actual_digest = AIIDEA::GeometryFingerprint.signature(part.entities)
              errors << "#{name}: internal geometry changed" unless actual_digest == expected_digest
            rescue ArgumentError => e
              errors << "#{name}: cannot verify internal geometry (#{e.message})"
            end
          end

          size = part.get_attribute('AI_IDEA', 'expected_size_mm', nil)
          origin = part.get_attribute('AI_IDEA', 'expected_origin_mm', nil)
          unless finite_numbers?(size, 3, positive: true)
            errors << "#{name}: missing valid size metadata"
            next
          end
          unless finite_numbers?(origin, 3)
            errors << "#{name}: missing valid origin metadata (reimport using V1.8)"
            next
          end
          panel['expected_size_mm'] = size.dup
          panel['expected_origin_mm'] = origin.dup

          begin
            box = part.bounds
            actual_size = [box.width, box.height, box.depth].map { |length| length.to_mm.to_f }
            point = box.min
            actual_origin = [point.x, point.y, point.z].map { |length| length.to_mm.to_f }
          rescue StandardError
            errors << "#{name}: cannot determine bounding box and position"
            next
          end

          unless finite_numbers?(actual_size, 3, positive: true) && finite_numbers?(actual_origin, 3)
            errors << "#{name}: invalid bounding box or origin"
            next
          end
          panel['actual_size_mm'] = actual_size
          panel['actual_origin_mm'] = actual_origin
          panel['size_delta_mm'] = (0..2).map { |i| actual_size[i] - size[i] }
          panel['origin_delta_mm'] = (0..2).map { |i| actual_origin[i] - origin[i] }

          (0..2).each do |index|
            axis = %w[X Y Z][index]
            size_delta = (actual_size[index] - size[index]).abs
            origin_delta = (actual_origin[index] - origin[index]).abs
            errors << "#{name}: #{axis} size changed by #{size_delta.round(3)} mm" if size_delta > TOLERANCE_MM
            errors << "#{name}: #{axis} origin shifted by #{origin_delta.round(3)} mm" if origin_delta > TOLERANCE_MM
          end
        ensure
          panel['errors'] = errors[first_error..-1]
          panel['status'] = panel['errors'].empty? ? 'passed' : 'failed'
        end
      end

      {
        'schema_version' => 'ai-idea.model-audit.v4',
        'units' => 'mm',
        'axes' => ['X', 'Y', 'Z'],
        'coordinate_space' => 'draft_parent_local',
        'panels' => panels,
        'mode' => 'read_only',
        'status' => errors.empty? ? 'passed' : 'failed',
        'expected_panels' => expected_count,
        'inspected_panels' => entities.length,
        'tolerance_mm' => TOLERANCE_MM,
        'checks' => ['part_count', 'part_ids', 'part_sizes', 'part_origins', 'parent_transform', 'part_transforms', 'face_loops', 'edges'],
        'errors' => errors,
        'model_changed' => false,
        'manufacturing_approved' => false
      }
    end

    # Audits after the save dialog closes, so the report describes the current
    # selection. Only the explicitly chosen new JSON file is written.
    def export_to(path, model)
      raise ArgumentError, 'Only JSON reports are supported' unless File.extname(path).downcase == '.json'
      report = audit(model)
      payload = JSON.pretty_generate(report) + "\n"
      File.open(path, File::WRONLY | File::CREAT | File::EXCL, 0o600) do |file|
        file.write(payload)
      end
      report
    end

    def export_gui
      path = UI.savepanel('Save AI IDEA DRAFT audit report (new JSON file)', nil, 'AI_IDEA_DRAFT_AUDIT.json')
      return { 'status' => 'cancelled', 'model_changed' => false } unless path
      report = export_to(path, Sketchup.active_model)
      UI.messagebox("AI IDEA audit report saved: #{report['status'].upcase}. READ ONLY model audit. Not approved for manufacturing.")
      report
    end

    def run_gui
      report = audit(Sketchup.active_model)
      message = "AI IDEA DRAFT integrity audit: #{report['status'].upcase}\n" +
                "Panels: #{report['inspected_panels']}/#{report['expected_panels']}\n" +
                "Tolerance: #{report['tolerance_mm']} mm\n" +
                (report['errors'].empty? ? 'No dimension or placement discrepancies detected.' : report['errors'].first(8).join("\n")) +
                "\nREAD ONLY. Not approved for manufacturing."
      UI.messagebox(message)
      report
    end
  end
end
