"""Prepare/validate the fixed teacher example bank; no student experiment."""
import argparse
import pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from extensions.k9.teacher import prepare
from extensions.k9.core import load_examples

if __name__=='__main__':
    p=argparse.ArgumentParser(description='K9 teacher examples; current experiment uses the first example only')
    p.add_argument('command',choices=['prepare','verify'])
    args=p.parse_args()
    if args.command=='prepare':prepare()
    else:
        artifact=load_examples()
        print('Verified teacher bank; active example: '+artifact['examples'][0]['question_id'])
