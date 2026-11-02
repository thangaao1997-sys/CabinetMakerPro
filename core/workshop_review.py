"""Evidence-based offline NC review for the workshop agent.

No machine release API. Template feeds are references, never safety limits.
"""
import hashlib
import json
import math
from .nc_review import review_nc


def review_job(program, profile):
    if not isinstance(program, bytes) or not isinstance(profile, dict):
        raise ValueError('Expected NC bytes and workshop profile')
    text = program.decode('ascii')
    records = profile.get('tools', [])
    if not isinstance(records, list):
        raise ValueError('Tool list required')
    tools = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Invalid tool record')
        number, diameter = record.get('tool_number'), record.get('diameter_mm')
        if type(number) is not int or number <= 0 or number in tools:
            raise ValueError('Tool numbers must be unique positive integers')
        if diameter is not None and (type(diameter) not in (int, float) or
                not math.isfinite(diameter) or diameter <= 0):
            raise ValueError('Tool diameter must be finite and positive')
        tools[number] = record
    known = {n:r['diameter_mm'] for n,r in tools.items() if r.get('diameter_mm') is not None}
    trace = review_nc(text, known, z_zero=profile.get('production_z_zero_reference'))
    blockers, comparisons, usage = [], [], []
    def block(code, detail):
        blockers.append({'code':code, 'detail':detail})
    if not trace['trace_complete']:
        block('nc_trace_issues', 'Resolve all line-specific parsing and state issues.')
    if trace['units_evidence'] != 'explicit_G21':
        block('startup_units_unknown', 'Program does not explicitly select mm. Verify controller startup units; do not modify the production post automatically.')
    if not profile.get('controller'):
        block('controller_unknown', 'Controller model and startup behavior have not been recorded.')
    if profile.get('production_z_zero_reference') != 'machine_table_surface':
        block('z_reference_unverified', 'This workshop review requires the configured table-surface datum.')
    if trace['custom_commands']:
        # Merely filling m100_function with a string is not machine validation.
        block('custom_m_codes_unvalidated', 'M100 is present; its controller behavior has not been independently validated.')
    active = sorted({int(s['tool']) for s in trace['segments']
                     if s['tool'] is not None and s['tool'].is_integer()})
    for number in active:
        record = tools.get(number, {})
        segments = [s for s in trace['segments'] if s['tool'] == number]
        horizontal, vertical, speeds = set(), set(), set()
        for seg in segments:
            if seg['spindle'] is not None:
                speeds.add(seg['spindle'])
            if seg['motion'] != 'feed' or seg['feed'] is None:
                continue
            xyz_known = all(seg[e][a] is not None for e in ('from','to') for a in 'XYZ')
            if not xyz_known:
                continue
            if any(seg['from'][a] != seg['to'][a] for a in 'XY'):
                horizontal.add(seg['feed'])
            elif seg['from']['Z'] != seg['to']['Z']:
                vertical.add(seg['feed'])
        usage.append({'tool_number':number, 'diameter_mm':record.get('diameter_mm'),
                      'spindle_s_values':sorted(speeds),
                      'xy_feed_values':sorted(horizontal), 'z_only_feed_values':sorted(vertical)})
        if record.get('machine_head') is None:
            block('head_mapping_missing', f'T{number}: physical head mapping not verified.')
        if record.get('physical_tool_geometry_verified') is not True:
            block('physical_tool_unverified', f'T{number}: diameter/profile/installed tool not independently checked.')
        for key, actual in [('spindle_rpm',speeds), ('feed_mm_min',horizontal), ('plunge_mm_min',vertical)]:
            reference = record.get(key)
            if reference is not None and actual and actual != {reference}:
                comparisons.append({'tool_number':number, 'parameter':key,
                                    'template_reference':reference, 'program_values':sorted(actual),
                                    'meaning':'Difference from one observed template; not a proven unsafe limit violation.'})
    block('setup_and_simulation_pending', 'Stock, fixtures, swept tool geometry, offsets, machine travel and operation simulation are not validated.')
    return {'schema_version':'ai-idea.workshop-nc-review.v1',
            'stage':'needs_technician_review',
            'source_nc_sha256':hashlib.sha256(program).hexdigest(),
            'profile_sha256':hashlib.sha256(json.dumps(profile,sort_keys=True,ensure_ascii=False,
                separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest(),
            'trace_complete':trace['trace_complete'], 'trace_issues':trace['issues'],
            'units_evidence':trace['units_evidence'], 'work_offset':trace['work_offset'],
            'tool_changes':trace['tool_changes'], 'tool_usage':usage,
            'template_comparisons':comparisons, 'release_blockers':blockers,
            'machine_release_allowed':False, 'manufacturing_approved':False,
            'machine_execution_performed':False,
            'scope':'Offline commanded-path evidence only; no stock or collision simulation.'}
