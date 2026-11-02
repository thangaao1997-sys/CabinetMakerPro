"""Workshop intake agent: inspect a scene and prepare technician review tasks.

This stage plans work; it neither changes geometry nor generates toolpaths.
Scene dimensions describe finished geometry, not machining blank allowances.
"""
import argparse
import hashlib
import json
import math
from collections import defaultdict


def _vector(value, positive=False):
    if not isinstance(value, dict) or set(value) != set('xyz'):
        raise ValueError('Expected X/Y/Z vector')
    result = [value[k] for k in 'xyz']
    if any(type(n) not in (int, float) or not math.isfinite(n) or
           (n <= 0 if positive else n < 0) for n in result):
        raise ValueError('Invalid scene dimensions or position')
    return result


def prepare_job(scene):
    """Derive geometry inventory and explicit decisions from an existing draft.

    Does not infer drill patterns, edge allowances, grain, machine capabilities
    or workshop approval from a geometrically valid scene.
    """
    if not isinstance(scene, dict) or scene.get('schema_version') != 'ai-idea.scene.v1':
        raise ValueError('Expected AI IDEA scene')
    if scene.get('units') != 'mm' or scene.get('manufacturing_approved') is not False:
        raise ValueError('Expected unapproved scene in mm')
    rid = scene.get('request_id')
    if not isinstance(rid, str) or not rid.strip() or len(rid) > 100:
        raise ValueError('Invalid request ID')
    envelope = scene.get('envelope_mm')
    if not isinstance(envelope, dict) or set(envelope) != {'width', 'depth', 'height'}:
        raise ValueError('Invalid envelope')
    limits = _vector(dict(zip('xyz', [envelope[k] for k in ('width', 'depth', 'height')])), True)
    objects = scene.get('objects')
    if not isinstance(objects, list) or not 1 <= len(objects) <= 2000:
        raise ValueError('Invalid panel count')
    panels, ids, bounds = [], set(), []
    groups = defaultdict(list)
    for obj in objects:
        if not isinstance(obj, dict):
            raise ValueError('Invalid panel')
        code = obj.get('id')
        if not isinstance(code, str) or not code.strip() or code in ids:
            raise ValueError('Missing or duplicate panel ID')
        ids.add(code)
        material = obj.get('material')
        if material not in ('panel', 'back'):
            raise ValueError('Unknown material')
        size, origin = _vector(obj.get('size_mm'), True), _vector(obj.get('origin_mm'))
        if any(origin[i] + size[i] > limits[i] + 1e-7 for i in range(3)):
            raise ValueError('Panel outside design envelope: ' + code)
        for old_origin, old_size in bounds:
            if all(min(origin[i] + size[i], old_origin[i] + old_size[i]) -
                   max(origin[i], old_origin[i]) > 1e-7 for i in range(3)):
                raise ValueError('Overlapping panel solids: ' + code)
        bounds.append((origin, size))
        smallest = min(size)
        candidates = [i for i, n in enumerate(size) if n == smallest]
        axis = candidates[0] if len(candidates) == 1 else None
        face = [n for i, n in enumerate(size) if i != axis] if axis is not None else None
        item = {
            'panel_id': code, 'material_role': material,
            'finished_size_xyz_mm': size, 'origin_xyz_mm': origin,
            'thickness_candidate_mm': smallest if axis is not None else None,
            'thickness_axis_candidate': 'xyz'[axis] if axis is not None else None,
            'finished_face_candidate_mm': face,
            'blank_size_mm': None,
            'decisions_required': ['material_stock', 'thickness_axis', 'face_orientation',
                                   'grain_and_rotation', 'edgebanding_and_allowances',
                                   'joinery_drilling_grooves'],
        }
        panels.append(item)
        # These are stock REVIEW groups, never optimized cutting groups.
        groups[(material, smallest if axis is not None else None)].append(code)
    encoded = json.dumps(scene, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    return {
        'schema_version': 'ai-idea.workshop-intake.v1',
        'job_id': rid, 'source_scene_sha256': hashlib.sha256(encoded).hexdigest(),
        'stage': 'awaiting_workshop_decisions', 'units': 'mm',
        'panel_count': len(panels), 'panels': panels,
        'stock_review_groups': [
            {'material_role': key[0], 'thickness_candidate_mm': key[1], 'panel_ids': values}
            for key, values in groups.items()
        ],
        'next_tasks': [
            {'task': 'review_construction', 'owner': 'technician',
             'requires': ['approved_design', 'base_and_doors', 'hardware_and_clearances']},
            {'task': 'complete_panel_decisions', 'owner': 'technician',
             'requires': ['all_panel_decisions']},
            {'task': 'prepare_nesting', 'owner': 'agent_after_configuration',
             'requires': ['blank_sizes', 'stock_sheet_sizes', 'grain_and_rotation',
                          'tool_diameter', 'sheet_margins', 'part_spacing', 'hold_down_rules']},
            {'task': 'prepare_machining', 'owner': 'agent_after_configuration',
             'requires': ['machine_controller', 'validated_postprocessor', 'tool_library',
                          'work_origin', 'safe_heights', 'operation_rules']},
            {'task': 'release_to_machine', 'owner': 'technician',
             'requires': ['simulation_review', 'setup_review', 'explicit_job_release']},
        ],
        'source_change_policy': 'Rebuild this intake and review dependent decisions when source hash changes.',
        'model_changed': False, 'cnc_files_generated': False, 'manufacturing_approved': False,
    }


def main():
    parser = argparse.ArgumentParser(description='Prepare workshop review tasks from a scene')
    parser.add_argument('--scene', required=True)
    args = parser.parse_args()
    with open(args.scene, encoding='utf-8') as source:
        result = prepare_job(json.load(source))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
