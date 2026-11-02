"""Offline job reviewer: read NC folder + workshop profile, emit JSON only."""
import argparse
import json
from pathlib import Path
from core.workshop_review import review_job


def review_folder(folder, profile):
    folder=Path(folder)
    if not folder.is_dir():
        raise ValueError('NC input must be a directory')
    files=sorted(p for p in folder.rglob('*') if p.is_file() and p.suffix.lower()=='.nc')
    if not files:
        raise ValueError('No NC files found')
    reports=[]
    for file in files:
        result=review_job(file.read_bytes(),profile)
        result['source_relative_path']=file.relative_to(folder).as_posix()
        reports.append(result)
    return {'schema_version':'ai-idea.workshop-job-review.v1',
            'files_reviewed':len(reports), 'programs':reports,
            'manufacturing_approved':False, 'machine_release_allowed':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nc-dir',required=True)
    parser.add_argument('--profile',required=True)
    parser.add_argument('--report',required=True,help='New JSON report path; never overwrites')
    args=parser.parse_args()
    destination=Path(args.report)
    if destination.suffix.lower()!='.json':
        parser.error('Report must have JSON extension')
    with open(args.profile,encoding='utf-8-sig') as source:
        profile=json.load(source)
    result=review_folder(args.nc_dir,profile)
    payload=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    with destination.open('x',encoding='utf-8') as target:
        target.write(payload)
    print(f"Reviewed {result['files_reviewed']} files. Technician review required; no CNC generated.")


if __name__=='__main__':
    main()
