# encoding: UTF-8
# AI IDEA SketchUp self-test: explicitly invoked, disposable operation only.
# Refuses saved, nonempty, editing-context, or locked models.
require 'json'
require_relative 'scene_importer'
require_relative 'model_audit'

module AIIDEA
  module SelfTest
    module_function

    def fixture
      {
        'schema_version' => 'ai-idea.scene.v1',
        'units' => 'mm',
        'request_id' => 'SELFTEST-NONPRODUCTION',
        'manufacturing_approved' => false,
        'envelope_mm' => { 'width' => 120, 'depth' => 80, 'height' => 80 },
        'objects' => [{
          'id' => 'TEST-PANEL',
          'role' => 'test_cuboid',
          'material' => 'panel',
          'origin_mm' => { 'x' => 5, 'y' => 10, 'z' => 3 },
          'size_mm' => { 'x' => 60, 'y' => 40, 'z' => 17 }
        }]
      }
    end

    def run(model)
      # Inspect before any attempt to create a group or operation.
      AIIDEA::SceneImporter.ensure_safe_target!(model)
      raise ArgumentError, 'Model operation API unavailable' unless model.respond_to?(:start_operation) && model.respond_to?(:abort_operation)
      scene = AIIDEA::SceneImporter.parse_scene(JSON.generate(fixture))
      report = nil
      opened = false

      begin
        raise 'Unable to open SketchUp test transaction' unless model.start_operation('AI IDEA SELF TEST - ABORT', true)
        opened = true
        parent = AIIDEA::SceneImporter.draw_draft(scene, model)
        report = AIIDEA::ModelAudit.audit_root(parent)
        raise "Draft integrity test failed: #{report['errors'].first(3).join('; ')}" unless report['status'] == 'passed'
      ensure
        # A successful self-test must never commit the temporary geometry.
        model.abort_operation if opened
      end

      # Explicit post-condition; fail closed if the host did not undo.
      raise 'Self-test rollback incomplete; inspect the TEST model' unless model.entities.to_a.empty?
      {
        'schema_version' => 'ai-idea.sketchup-smoke.v1',
        'status' => 'passed',
        'mode' => 'temporary_geometry_rolled_back',
        'sketchup_version' => Sketchup.version.to_s,
        'ruby_version' => RUBY_VERSION,
        'panels_verified' => report['inspected_panels'],
        'geometry_audit' => report['status'],
        'model_unchanged_after_rollback' => true,
        'manufacturing_approved' => false,
        'network_started' => false
      }
    end

    def run_gui
      model = Sketchup.active_model
      AIIDEA::SceneImporter.ensure_safe_target!(model)
      message = 'AI IDEA Self-test builds ONE temporary panel and aborts the operation. ' +
                'Use ONLY a NEW UNSAVED EMPTY disposable model. Continue?'
      decision = UI.messagebox(message, MB_YESNO)
      return { 'status' => 'cancelled', 'model_changed' => false } unless decision == IDYES
      report = run(model)
      UI.messagebox("AI IDEA SELF-TEST PASSED. Geometry verified; test transaction aborted. " +
                    "Model contains no added geometry. NOT approved for manufacturing.")
      report
    end
  end
end
