"""Package only the read-only workshop inventory reader."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
MEMBERS=('ai_idea_workshop.rb','ai_idea_workshop/main.rb','ai_idea_workshop/inventory.rb')


def build_reader(destination, root=ROOT):
    destination=Path(destination)
    sources=[]
    for name in MEMBERS:
        path=Path(root)/'workshop_plugin'/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing regular reader source: '+name)
        data=path.read_bytes()
        if not data:raise ValueError('Empty reader source')
        sources.append((name,data))
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'x',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sources:
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644<<16
            archive.writestr(info,data)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None or sorted(archive.namelist())!=sorted(MEMBERS):
            raise ValueError('Reader archive integrity failure')
        for name,data in sources:
            if archive.read(name)!=data:raise ValueError('Reader source parity failure')
    return {'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'files':len(sources)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    print(build_reader(parser.parse_args().output))
