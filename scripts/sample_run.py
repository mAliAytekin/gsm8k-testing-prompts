"""Run/resume the fixed 1000-question, 16-condition warm-model experiment."""
import argparse
import json
import pathlib
import sqlite3
import sys
import zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from gsm8k_lab.common import ROOT,read_json
from extensions.repeat10 import run,analyze
from extensions.sampling import select

CONFIG='configs/sample1000.json'


def report(rid):
    analyze(rid,CONFIG)
    from scripts.explain_report import enrich
    cfg=read_json(ROOT/CONFIG);enrich(rid,cfg['database'])
    out=ROOT/'reports'/rid
    with zipfile.ZipFile(out/'GSM8K_REPORT_PACKAGE.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in ('REPORT.md','accuracy.png','accuracy.svg','summary.json','summary.csv','audit.json'):z.write(out/name,arcname=name)
        z.write(ROOT/cfg['question_manifest'],arcname='question-manifest.json')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    for name in ('prepare','run','status'):s.add_parser(name)
    for name in ('resume','analyze'):s.add_parser(name).add_argument('run_id')
    a=p.parse_args();cfg=read_json(ROOT/CONFIG)
    if a.command=='prepare':
        qs=select(cfg);m=read_json(ROOT/cfg['question_manifest']);print(json.dumps({k:v for k,v in m.items() if k not in ('question_ids','question_hashes','previous_pilot_ids')},indent=2));print('Selected',len(qs),'previous pilot overlap',len(m['previous_pilot_ids']))
    elif a.command=='status':
        latest=read_json(ROOT/'artifacts/repeat1000-latest.json')
        with sqlite3.connect(f'file:{ROOT/cfg["database"]}?mode=ro',uri=True) as db:
            counts=dict(db.execute('SELECT state,count(*) FROM records WHERE run_id=? GROUP BY state',(latest['run_id'],)))
        print(json.dumps(dict(**latest,states=counts),indent=2))
    elif a.command=='analyze':report(a.run_id)
    else:report(run(a.run_id if a.command=='resume' else None,CONFIG))
