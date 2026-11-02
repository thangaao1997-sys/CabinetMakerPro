"""Inventory contiguous feed runs; does not infer holes, parts or cut depth."""
import math


def inventory_feed_runs(trace):
    if trace.get('trace_complete') is not True:
        return {'status':'blocked_trace_incomplete', 'runs':[], 'total_feed_distance_mm':None,
                'ideal_feed_travel_minutes':None}
    runs, current = [], []

    def finish():
        if not current:
            return
        points=[current[0]['from']]+[s['to'] for s in current]
        xyz_moved={a:any(s['from'][a]!=s['to'][a] for s in current) for a in 'XYZ'}
        distance=sum(math.dist([s['from'][a] for a in 'XYZ'],[s['to'][a] for a in 'XYZ']) for s in current)
        minutes=sum(math.dist([s['from'][a] for a in 'XYZ'],[s['to'][a] for a in 'XYZ'])/s['feed'] for s in current)
        xy_moved=xyz_moved['X'] or xyz_moved['Y']
        closed=xy_moved and all(abs(points[0][a]-points[-1][a]) <= 1e-6 for a in 'XY')
        kind='xyz_feed_run' if xy_moved and xyz_moved['Z'] else ('xy_feed_run' if xy_moved else 'z_only_feed_run')
        runs.append({'run_id':len(runs)+1, 'classification':kind,
                     'tool_number':int(current[0]['tool']),
                     'start_line':current[0]['line'], 'end_line':current[-1]['line'],
                     'start_xyz':points[0].copy(), 'end_xyz':points[-1].copy(),
                     'commanded_bounds':{a:{'min':min(p[a] for p in points),'max':max(p[a] for p in points)} for a in 'XYZ'},
                     'closed_in_xy':closed, 'feed_values':sorted({s['feed'] for s in current}),
                     'spindle_values':sorted({s['spindle'] for s in current}),
                     'feed_distance_mm':distance, 'ideal_feed_travel_minutes':minutes,
                     'machining_feature_identity':None, 'part_id':None, 'cut_depth_mm':None})
        current.clear()

    for segment in trace['segments']:
        if segment['motion']!='feed':
            finish()
            continue
        if any(segment[e][a] is None for e in ('from','to') for a in 'XYZ'):
            raise ValueError('Complete trace contains unknown coordinates')
        if segment['feed'] is None or segment['feed']<=0 or segment['tool'] is None:
            raise ValueError('Complete trace contains invalid feed/tool state')
        if current and (segment['tool']!=current[-1]['tool'] or
                        segment['line']!=current[-1]['line']+1 or
                        segment['from']!=current[-1]['to']):
            finish()
        current.append(segment)
    finish()
    return {'status':'feed_inventory_ready', 'runs':runs,
            'total_feed_distance_mm':sum(r['feed_distance_mm'] for r in runs),
            'ideal_feed_travel_minutes':sum(r['ideal_feed_travel_minutes'] for r in runs),
            'interpretation':'Geometry of contiguous feed commands, not a count of holes or finished parts.',
            'units_basis':'Commanded values interpreted as mm from workshop/post context; verify controller units separately.',
            'time_scope':'Feed travel at commanded F only; excludes rapids, acceleration, tool changes, spindle delays and all machine-specific behavior.',
            'manufacturing_approved':False}
