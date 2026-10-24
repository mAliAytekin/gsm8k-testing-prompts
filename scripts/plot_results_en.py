"""Render an English figure from saved cell results, without model calls."""
import argparse
import json
import pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from gsm8k_lab.common import ROOT

LABELS={
    'K2':('CoT — step-by-step natural-language reasoning',0),
    'K3':('Arithmetic expression',0),
    'K4':('Python/PAL — unrestricted solution representation',0),
    'K5':('Python — deterministic state updates',0),
    'K6':('SymPy — zero-shot',0),
    'K7':('SymPy — one-shot',1),
    'K8':('SymPy — two-shot',2),
    'K9':('Teacher CoT — Gemma demonstration',1),
}
for arm in ('K2','K3','K4','K5'):
    for count in (1,2):LABELS[f'{arm}_{count}shot']=(LABELS[arm][0],count)


def render(run_id):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    out=ROOT/'reports'/run_id
    summary=json.loads((out/'summary.json').read_text())
    cells=summary['cells'];n=len(summary['question_ids'])
    models=['lfm2-350m','lfm2-700m','lfm2-1.2b','qwen3-0.6b','qwen3-1.7b']
    conditions=list(dict.fromkeys(c['condition'] for c in cells))
    if set(conditions)!=set(LABELS):raise ValueError('Unrecognized condition set')
    matrix=np.full((len(conditions),len(models)),np.nan)
    for y,condition in enumerate(conditions):
        for x,model in enumerate(models):
            cell=next(c for c in cells if c['condition']==condition and c['model']==model)
            if cell['complete'] and cell['accuracy'] is not None:matrix[y,x]=100*cell['accuracy']
    labels=[f'{c} — {LABELS[c][0]}\n{LABELS[c][1]} solved '+('example' if LABELS[c][1]==1 else 'examples') for c in conditions]
    fig,ax=plt.subplots(figsize=(15,14))
    im=ax.imshow(matrix,vmin=0,vmax=100,cmap='Blues',aspect='auto')
    for y in range(len(conditions)):
        for x in range(len(models)):
            v=matrix[y,x]
            ax.text(x,y,'N/A' if np.isnan(v) else f'{v:.1f}%',ha='center',va='center',fontsize=12,color='white' if v>65 else 'black')
    ax.set_yticks(range(len(conditions)),labels,fontsize=10)
    ax.set_xticks(range(len(models)),models,rotation=20,ha='right',fontsize=10)
    ax.set_title(f'GSM8K • {n:,} questions per cell • 5 models (Q8_0)\nEnd-to-end accuracy: format + execution + numerical answer',fontsize=15,pad=18)
    fig.colorbar(im,ax=ax,label='Accuracy (%)',fraction=.03,pad=.03)
    fig.text(.02,.018,f'CoT: natural-language reasoning | PAL: Python program | SymPy: symbolic mathematics\nK9: 1 Gemma teacher example; no judge. Repeated measurements on the same {n:,} questions; exploratory results.\nN/A: incomplete infrastructure coverage; see the report for the planned and evaluable denominators.',fontsize=10)
    fig.subplots_adjust(left=.45,right=.92,top=.92,bottom=.11)
    for extension in ('png','svg'):fig.savefig(out/f'accuracy.en.{extension}',dpi=180)
    plt.close(fig)
    print(out/'accuracy.en.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    render(parser.parse_args().run_id)
