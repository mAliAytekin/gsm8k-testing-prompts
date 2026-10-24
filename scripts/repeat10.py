import argparse
import pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from extensions.repeat10 import run,analyze

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Repeat all 16 generation conditions on ten pilot questions; K9 one-shot, no cache')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('run')
    for command in ['resume','analyze']:sub.add_parser(command).add_argument('run_id')
    args=parser.parse_args()
    if args.command=='analyze':analyze(args.run_id)
    else:analyze(run(resume_id=args.run_id if args.command=='resume' else None))
