"""Offline BF-post NC trace reader. No machine connection or NC generation.

Only the observed G0/G1 absolute XYZ subset is traced. Every unsupported word
blocks trace acceptance. This is not controller emulation or collision checking.
"""
import math
import re

TOKEN = re.compile(r'([A-Z])([+-]?(?:\d+(?:\.\d*)?|\.\d+))')


def review_nc(text, tools, *, z_zero=None):
    position = dict.fromkeys('XYZ')
    motion = None
    absolute = False
    tool = selected_tool = offset = spindle = feed = None
    units = work_offset = None
    trace_trusted = True
    spinning = False
    ended = False
    segments, issues, changes, custom = [], [], [], []
    def issue(line, message):
        issues.append({'line': line, 'message': message})
    for number, raw in enumerate(text.splitlines(), 1):
        line = re.sub(r'\([^()]*\)', '', raw.upper()).split(';', 1)[0].strip()
        if not line:
            continue
        if ended:
            issue(number, 'Content after program end')
            continue
        words = TOKEN.findall(line)
        if TOKEN.sub('', line).strip():
            issue(number, 'Unparsed content; trace is incomplete')
            trace_trusted = False
            continue
        values = {}
        invalid_block = False
        for key, value in words:
            numeric = float(value)
            if not math.isfinite(numeric):
                issue(number, 'Nonfinite value')
                invalid_block = True
                continue
            values.setdefault(key, []).append(numeric)
            if key not in 'NGMTHSFXYZ':
                issue(number, 'Unsupported word ' + key)
                invalid_block = True
        for key in 'THSFXYZ':
            if len(values.get(key, [])) > 1:
                issue(number, 'Repeated word ' + key)
                invalid_block = True
        motion_words = [g for g in values.get('G', []) if g in (0, 1)]
        if len(motion_words) > 1:
            issue(number, 'Conflicting motion modes in one block')
            invalid_block = True
        if invalid_block:
            trace_trusted = False
            continue
        unsupported_motion = False
        for g in values.get('G', []):
            if g == 90:
                absolute = True
            elif g in (0, 1):
                motion = int(g)
            elif g == 21:
                units = 'mm'
            elif g == 54:
                work_offset = 'G54'
            elif g != 43:
                issue(number, 'Unsupported G code ' + str(g))
                unsupported_motion = True
        if 'T' in values:
            selected_tool = values['T'][-1]
            if not selected_tool.is_integer() or int(selected_tool) not in tools:
                issue(number, 'Tool absent from workshop profile')
        if 'S' in values:
            spindle = values['S'][-1]
        if 'F' in values:
            feed = values['F'][-1]
        for m in values.get('M', []):
            if m == 6:
                tool = selected_tool
                offset = None
                feed = None
                changes.append({'line':number, 'tool':tool})
                if tool is None:
                    issue(number, 'Tool change without selected tool')
                if spinning:
                    issue(number, 'Tool change while spindle command is active')
            elif m == 3:
                spinning = True
            elif m == 5:
                spinning = False
            elif m == 30:
                ended = True
            elif m == 100:
                custom.append({'line':number, 'code':'M100', 'meaning_verified':False})
            else:
                issue(number, 'Unsupported M code ' + str(m))
                trace_trusted = False
        if 'H' in values:
            if 43 not in values.get('G', []):
                issue(number, 'H offset without supported G43 activation')
            else:
                offset = values['H'][-1]
                if not offset.is_integer() or offset <= 0:
                    issue(number, 'Invalid tool length offset number')
        if unsupported_motion:
            position = dict.fromkeys('XYZ')
            absolute = False
            trace_trusted = False
        if not any(a in values for a in 'XYZ'):
            continue
        if not trace_trusted or not absolute or unsupported_motion or motion is None:
            issue(number, 'Cannot trace motion without supported absolute mode')
            # Do not propagate uncertain coordinates into subsequent segments.
            position = dict.fromkeys('XYZ')
            absolute = False
            continue
        target = {a: values[a][-1] if a in values else position[a] for a in 'XYZ'}
        if any(v is None for v in target.values()):
            issue(number, 'Motion has unknown initial axis coordinates')
        if work_offset is None:
            issue(number, 'Motion without verified G54 work offset selection')
        if motion == 1:
            if not spinning or spindle is None or spindle <= 0:
                issue(number, 'Feed motion without known active spindle')
            if feed is None or feed <= 0:
                issue(number, 'Feed motion without positive feed')
            if tool is None or offset != tool:
                issue(number, 'Missing or mismatched tool length offset')
            if tool is not None and (not tool.is_integer() or int(tool) not in tools):
                issue(number, 'Feed motion uses unknown loaded tool')
        if z_zero == 'machine_table_surface' and target['Z'] is not None and target['Z'] < 0:
            issue(number, 'Commanded Z below configured table reference; review required')
        segments.append({'line':number, 'motion':'rapid' if motion==0 else 'feed',
                         'from':position.copy(), 'to':target.copy(), 'tool':tool,
                         'feed':feed if motion==1 else None, 'spindle':spindle})
        position = target
    if not ended:
        issue(len(text.splitlines()), 'Missing M30 program end')
    return {'stage':'offline_trace_review', 'trace_complete':not issues,
            'issues':issues, 'tool_changes':changes, 'custom_commands':custom,
            'segments':segments, 'z_zero_reference':z_zero,
            'units_evidence': 'explicit_G21' if units == 'mm' else 'not_explicit_in_program',
            'work_offset':work_offset,
            'machine_execution_performed':False, 'manufacturing_approved':False,
            'limitations':['No stock, clamps, tool-shape or collision simulation',
                          'M100 behavior and controller startup units are not verified',
                          'Coordinates are commanded work coordinates, not physical machine travel']}
