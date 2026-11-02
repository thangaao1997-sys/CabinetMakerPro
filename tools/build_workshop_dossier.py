"""Create a fresh offline review dossier without copying or generating NC."""
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from core.nc_review import review_nc
from core.workshop_review import review_job
from core.feed_inventory import inventory_feed_runs


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _sources(folder):
    root=Path(folder).resolve()
    if not root.is_dir():
        raise ValueError('NC directory not found')
    files=sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower()=='.nc')
    if not files:
        raise ValueError('No NC input files')
    for file in files:
        if file.is_symlink() or not file.resolve().is_relative_to(root):
            raise ValueError('Linked NC input is not supported')
    return root, files


def collect(folder, profile):
    root, files=_sources(folder)
    programs=[]
    known={t['tool_number']:t.get('diameter_mm') for t in profile.get('tools',[]) if t.get('diameter_mm') is not None}
    for file in files:
        if file.stat().st_size>10_000_000:
            raise ValueError('NC file exceeds intake size limit')
        data=file.read_bytes()
        reviewed=review_job(data,profile)
        trace=review_nc(data.decode('ascii'),known,z_zero=profile.get('production_z_zero_reference'))
        programs.append({'relative_path':file.relative_to(root).as_posix(),
                         'source_sha256':digest(data), 'review':reviewed,
                         'feed_inventory':inventory_feed_runs(trace), 'trace':trace})
    return {'schema_version':'ai-idea.offline-dossier.v1', 'programs':programs,
            'file_count':len(programs), 'manufacturing_approved':False,
            'machine_release_allowed':False, 'machine_execution_performed':False}


def _plot(trace, axes):
    segments=[s for s in trace['segments'] if all(s[e][a] is not None for e in ('from','to') for a in axes)]
    if not segments:
        return '<p>Không có quỹ đạo đủ tọa độ.</p>'
    xs=[s[e][axes[0]] for s in segments for e in ('from','to')]
    ys=[s[e][axes[1]] for s in segments for e in ('from','to')]
    xmin,xmax,ymin,ymax=min(xs),max(xs),min(ys),max(ys)
    def point(p):
        return (30+(p[axes[0]]-xmin)/max(xmax-xmin,1)*950,
                290-(p[axes[1]]-ymin)/max(ymax-ymin,1)*250)
    parts=[f'<h3>Hình chiếu {axes}</h3><svg viewBox="0 0 1020 330" role="img" aria-label="{axes}">']
    palette={1:'#1463a0',2:'#d57b13',3:'#a73591',4:'#158058'}
    for seg in segments:
        x1,y1=point(seg['from']);x2,y2=point(seg['to'])
        rapid=seg['motion']=='rapid'
        color='#aeb6bd' if rapid else palette.get(seg['tool'],'#333')
        dash=' stroke-dasharray="4 4"' if rapid else ''
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}"{dash}><title>Dòng {seg["line"]}</title></line>')
    parts.append(f'<text x="30" y="320" font-size="12">{axes[0]}: {xmin:g}…{xmax:g}; {axes[1]}: {ymin:g}…{ymax:g}. Tọa độ lệnh; hai trục co giãn riêng.</text></svg>')
    return '\n'.join(parts)


def render(dossier):
    escape=lambda x:html.escape(str(x))
    chunks=['<!doctype html><html lang="vi"><meta charset="utf-8"><title>IDEA — Hồ sơ gia công ngoại tuyến</title>',
        '<style>body{font:16px system-ui;background:#f1f4f6;color:#172a35;max-width:1200px;margin:32px auto;padding:20px}section{padding:24px;background:white;border-radius:14px;margin:24px 0}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #d3dce0;padding:8px;text-align:left}svg{width:100%;background:#fafcfd;border:1px solid #ddd}p{line-height:1.6}.notice{background:#fff1cf;padding:16px}code{word-break:break-all}</style>',
        '<h1>Hồ sơ gia công ngoại tuyến — IDEA</h1>',
        '<p class="notice">Hồ sơ để đối chiếu, chưa được phép bàn giao chạy máy. Không sinh hoặc sao chép NC. Hình mô phỏng chỉ là tọa độ lệnh G0/G1, chưa có va chạm/phôi/gá kẹp.</p>',
        '<p>“Cụm ăn dao” là các dòng G1 liên tiếp. Không tự đồng nhất với số lỗ, chi tiết, thao tác gia công hoặc chiều sâu cắt.</p>']
    kinds={'z_only_feed_run':'Ăn dao chỉ theo Z','xy_feed_run':'Ăn dao trong XY','xyz_feed_run':'Ăn dao phối hợp XYZ'}
    for p in dossier['programs']:
        inv=p['feed_inventory'];review=p['review']
        chunks.append('<section><h2>'+escape(p['relative_path'])+'</h2><p>SHA-256: <code>'+p['source_sha256']+'</code></p>')
        if not review['trace_complete']:
            chunks.append('<p class="notice">Quỹ đạo chưa đọc đầy đủ; không thống kê cụm ăn dao từ kết quả một phần.</p>')
        chunks.append('<p>Thứ tự gọi dao: '+escape(' → '.join('T'+str(t['tool']) for t in review['tool_changes']))+'</p>')
        chunks.append('<h3>Các mục cần đối chiếu trước bàn giao</h3><ul>')
        labels={'startup_units_unknown':'Chưa xác minh đơn vị khởi động của bộ điều khiển (file không có G21).',
                'controller_unknown':'Chưa xác minh cấu hình bộ điều khiển.',
                'custom_m_codes_unvalidated':'Chưa xác minh hành vi M100 trên máy.',
                'head_mapping_missing':'Chưa đối chiếu số dao với từng đầu máy.',
                'physical_tool_unverified':'Chưa kiểm chứng dao thực tế đang lắp.',
                'setup_and_simulation_pending':'Chưa mô phỏng phôi, dao, gá kẹp và hành trình máy.',
                'z_reference_unverified':'Mốc Z chưa khớp cấu hình mặt bàn.',
                'nc_trace_issues':'Có dòng lệnh hoặc trạng thái chưa đọc được đầy đủ.'}
        for code in dict.fromkeys(b['code'] for b in review['release_blockers']):
            chunks.append('<li>'+escape(labels.get(code,code))+'</li>')
        chunks.append('</ul>')
        if inv['status']=='feed_inventory_ready':
            chunks.append(f'<p>{len(inv["runs"])} cụm ăn dao; tổng quãng đường lệnh ăn dao {inv["total_feed_distance_mm"]:.2f} mm.</p>')
            chunks.append('<table><tr><th>Cụm</th><th>Dao</th><th>Dòng NC</th><th>Dạng chuyển động</th><th>Z thấp/cao</th><th>Khép XY</th></tr>')
            for r in inv['runs']:
                z=r['commanded_bounds']['Z']
                chunks.append(f'<tr><td>{r["run_id"]}</td><td>T{r["tool_number"]}</td><td>{r["start_line"]}–{r["end_line"]}</td><td>{kinds[r["classification"]]}</td><td>{z["min"]:g} / {z["max"]:g}</td><td>{"Có" if r["closed_in_xy"] else "Không"}</td></tr>')
            chunks.append('</table>')
        for axes in ('XY','XZ','YZ'):
            chunks.append(_plot(p['trace'],axes))
        for issue in review['trace_issues']:
            chunks.append('<p>'+escape(issue)+'</p>')
        chunks.append('</section>')
    return '\n'.join(chunks+['</html>'])


def build(folder, profile, output):
    source=Path(folder).resolve();target=Path(output).resolve()
    if target.is_relative_to(source) or source.is_relative_to(target):
        raise ValueError('Output directory must be separate from NC input')
    if target.exists():
        raise FileExistsError('Use a new dossier directory')
    dossier=collect(source,profile)
    # Validate and render completely before creating deliverables.
    payload=json.dumps(dossier,ensure_ascii=False,indent=2,allow_nan=False)
    page=render(dossier)
    target.mkdir(parents=True,exist_ok=False)
    (target/'dossier.json').write_text(payload,encoding='utf-8')
    (target/'index.html').write_text(page,encoding='utf-8')
    with (target/'feed_runs.csv').open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['file','run_id','tool','start_line','end_line','classification','start_x','start_y','start_z','end_x','end_y','end_z','z_min','z_max','feed_distance_mm'])
        for p in dossier['programs']:
            name=p['relative_path']
            if name.startswith(('=','+','-','@','\t','\r')):name="'"+name
            for r in p['feed_inventory']['runs']:
                writer.writerow([name,r['run_id'],r['tool_number'],r['start_line'],r['end_line'],r['classification'],
                                 *[r['start_xyz'][a] for a in 'XYZ'],*[r['end_xyz'][a] for a in 'XYZ'],
                                 r['commanded_bounds']['Z']['min'],r['commanded_bounds']['Z']['max'],r['feed_distance_mm']])
    manifest={'schema_version':'ai-idea.dossier-manifest.v1',
              'sources':{p['relative_path']:p['source_sha256'] for p in dossier['programs']},
              'outputs':{name:digest((target/name).read_bytes()) for name in ('dossier.json','index.html','feed_runs.csv')},
              'profile_sha256':dossier['programs'][0]['review']['profile_sha256'],
              'manufacturing_approved':False}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return dossier


def verify(folder, output, profile):
    source=Path(folder).resolve();target=Path(output).resolve()
    manifest=json.loads((target/'manifest.json').read_text(encoding='utf-8'))
    problems=[]
    if manifest.get('schema_version')!='ai-idea.dossier-manifest.v1':
        raise ValueError('Unsupported manifest')
    for base, entries, kind in ((source,manifest['sources'],'source'),(target,manifest['outputs'],'output')):
        for name,expected in entries.items():
            path=(base/name).resolve()
            if not path.is_relative_to(base):
                raise ValueError('Manifest path escapes expected directory')
            if not path.is_file() or digest(path.read_bytes())!=expected:
                problems.append({'kind':kind,'file':name,'reason':'missing_or_changed'})
    actual={p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file() and p.suffix.lower()=='.nc'}
    for extra in sorted(actual-set(manifest['sources'])):
        problems.append({'kind':'source','file':extra,'reason':'new_nc_file'})
    canonical=json.dumps(profile,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    if digest(canonical)!=manifest['profile_sha256']:
        problems.append({'kind':'profile','reason':'configuration_changed'})
    return {'file_evidence_current':not problems,'problems':problems,'machine_release_allowed':False,
            'scope':'File consistency check, not a digital signature or manufacturing approval.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nc-dir',required=True)
    parser.add_argument('--profile',required=True)
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--verify',action='store_true',help='Check existing dossier against current inputs')
    args=parser.parse_args()
    profile=json.loads(Path(args.profile).read_text(encoding='utf-8-sig'))
    if args.verify:
        result=verify(args.nc_dir,args.output_dir,profile)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['file_evidence_current'] else 2
    dossier=build(args.nc_dir,profile,args.output_dir)
    print(f"Dossier created: {dossier['file_count']} NC files. No machine release.")
    return 0


if __name__=='__main__':
    raise SystemExit(main())
