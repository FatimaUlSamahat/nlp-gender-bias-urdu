"""Matched Urdu Self-Debiasing extension. Run from repo root; see --help."""
import argparse
import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import numpy as np
import torch
from scipy.stats import chisquare
from src.disco.data_io import load_names, load_templates, validate
from src.disco.self_debias import SelfDebiasModel, BIAS_PREFIXES

METHODS = ('baseline', 'self_debias')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    tmp.replace(path)

def pairs(names, seed):
    male, female = list(names['male']), list(names['female'])
    rng = random.Random(seed)
    rng.shuffle(male)
    rng.shuffle(female)
    half = len(male)//2
    return {'MF':list(zip(male[:half], female[:half])),
            'MM':list(zip(male[:half], male[half:2*half])),
            'FF':list(zip(female[:half], female[half:2*half]))}

def sentence(template, name):
    return template.replace('{PERSON}', name).replace('{BLANK}', '<mask>')

def test(a, b, n):
    # Same lowercasing, probability chi-square, and Bonferroni threshold as control.py.
    x = {v['token_str'].lower():v['score'] for v in a}
    y = {v['token_str'].lower():v['score'] for v in b}
    tokens = sorted(set(x)|set(y))
    av=np.array([x.get(t,0.) for t in tokens])
    bv=np.array([y.get(t,0.) for t in tokens])
    with np.errstate(divide='ignore', invalid='ignore'):
        _, p=chisquare(av/av.sum(), bv/bv.sum())
    return int(p <= .05/n), int(set(x)!=set(y))

def evaluate(cache, templates, name_pairs, label, method):
    per=[]
    ga,gb={'MF':('male','female'),'MM':('male','male'),'FF':('female','female')}[label]
    for i in range(len(templates['male'])):
        values=[test(cache[sentence(templates[ga][i],a)][method],cache[sentence(templates[gb][i],b)][method],len(name_pairs)) for a,b in name_pairs]
        per.append({'template':i+1,'score':statistics.mean(v[0] for v in values),'support_mismatch':statistics.mean(v[1] for v in values)})
    return {'score':statistics.mean(v['score'] for v in per),'support_mismatch':statistics.mean(v['support_mismatch'] for v in per),'per_template':per}

@torch.inference_mode()
def probabilities(sd, texts):
    tok=sd.tokenizer
    inputs=tok(texts,padding=True,return_tensors='pt').to(sd.device)
    masks=inputs['input_ids'].eq(tok.mask_token_id)
    assert torch.all(masks.sum(1)==1)
    # The MLM head is token-local: apply it only at masks, avoiding full sequence vocab logits.
    hidden=sd.model.roberta(**inputs).last_hidden_state
    masked=hidden[masks]
    return torch.softmax(sd.model.lm_head(masked).float(),dim=-1)

def predictions(tok, probs):
    values,ids=torch.topk(probs,3,dim=-1)
    return [[{'token_str':tok.decode([int(i)]).strip(),'score':float(v),'token_id':int(i)} for i,v in zip(ii,vv)] for ii,vv in zip(ids,values)]

@torch.inference_mode()
def infer(sd, texts):
    base=probabilities(sd,texts)
    biased=probabilities(sd,[BIAS_PREFIXES['ur']+s for s in texts])
    difference=base-biased
    scaling=torch.where(difference>=0,torch.ones_like(difference),torch.maximum(torch.exp(sd.decay*difference),torch.full_like(difference,sd.epsilon)))
    adjusted=base*scaling
    retained=adjusted.sum(-1)
    adjusted=adjusted/retained[:,None]
    bpred=predictions(sd.tokenizer,base)
    spred=predictions(sd.tokenizer,adjusted)
    entropy=lambda p:-(p*p.clamp_min(1e-30).log()).sum(-1)
    be,se=entropy(base),entropy(adjusted)
    return [{'baseline':b,'self_debias':s,'retained_mass':float(m),'entropy_baseline':float(e),'entropy_self_debias':float(f)} for b,s,m,e,f in zip(bpred,spred,retained,be,se)]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',default='results/self_debias_extension')
    ap.add_argument('--batch-size',type=int,default=8)
    ap.add_argument('--threads',type=int,default=4)
    args=ap.parse_args()
    torch.set_num_threads(args.threads)
    torch.manual_seed(0)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    paths={k:Path(f'data/templates/{k}/disco_templates_ur.json') for k in ['v2','extended']}
    sets={k:load_templates(p) for k,p in paths.items()}
    names=load_names('ur')
    for t in sets.values():validate(t,names)
    manifest={'model':'xlm-roberta-base','prefix':BIAS_PREFIXES['ur'],'decay':50.,'epsilon':.01,'top_k':3,'seeds':list(range(5)),'template_hashes':{k:digest(p) for k,p in paths.items()},'names_sha256':digest('data/names/ur_names.json'),'implementation_sha256':digest('src/disco/self_debias.py'),'runner_sha256':digest(__file__),'python':platform.python_version(),'versions':{p:version(p) for p in ['torch','transformers','scipy','numpy','pandas','tokenizers','huggingface-hub']},'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'batch_size':args.batch_size,'threads':args.threads}
    cachepath=out/'predictions.json'
    oldmanifest=out/'manifest.json'
    if cachepath.exists():
        old=json.loads(oldmanifest.read_text(encoding='utf-8'))
        for key in ['model','prefix','decay','epsilon','template_hashes','names_sha256','implementation_sha256','runner_sha256','versions']:
            assert old[key]==manifest[key],f'Cache provenance mismatch: {key}; use a new --output'
    write(oldmanifest,manifest)
    cache=json.loads(cachepath.read_text(encoding='utf-8')) if cachepath.exists() else {}
    needed=list(dict.fromkeys(sentence(t[g][i],name) for t in sets.values() for i in range(len(t['male'])) for g in ['male','female'] for name in names[g]))
    print(f'{len(needed)} unique sentences; {len(cache)} cached',flush=True)
    sd=SelfDebiasModel(lang='ur')
    manifest['model_commit']=getattr(sd.model.config,'_commit_hash',None)
    manifest['device']=sd.device
    write(oldmanifest,manifest)
    # Verify optimized/batched inference against Laiba's unmodified predict(), across both sets and genders.
    samples=[sentence(t[g][i],names[g].iloc[0]) for t in sets.values() for g in ['male','female'] for i in [0,len(t['male'])-1]]
    batch=infer(sd,samples)
    max_error=0.
    for s,got in zip(samples,batch):
        ref=sd.predict(s)
        assert [p['token_str'] for p in ref]==[p['token_str'] for p in got['self_debias']], 'Batch top-k differs'
        for a,b in zip(ref,got['self_debias']):
            max_error=max(max_error,abs(a['score']-b['score']))
            assert np.isclose(a['score'],b['score'],rtol=1e-4,atol=2e-6)
    write(out/'implementation_check.json',{'samples':len(samples),'maximum_probability_error':max_error,'identical_top3':True})
    print(f'Validated against original predict(): max error {max_error}',flush=True)
    missing=[s for s in needed if s not in cache]
    start=time.monotonic()
    for offset in range(0,len(missing),args.batch_size):
        texts=missing[offset:offset+args.batch_size]
        cache.update(zip(texts,infer(sd,texts)))
        if offset% (args.batch_size*10)==0:
            write(cachepath,cache)
            print(f'Predictions {len(cache)}/{len(needed)}; elapsed {time.monotonic()-start:.0f}s',flush=True)
    write(cachepath,cache)
    all_results={}
    fullpairs=list(zip(names['male'],names['female']))
    for key,t in sets.items():
        full={m:evaluate(cache,t,fullpairs,'MF',m) for m in METHODS}
        controls=[]
        for seed in range(5):
            runs=pairs(names,seed)
            methods={}
            for m in METHODS:
                detail={label:evaluate(cache,t,nps,label,m) for label,nps in runs.items()}
                scores={label:r['score'] for label,r in detail.items()}
                same=(scores['MM']+scores['FF'])/2
                methods[m]={'scores':scores,'same_gender_average':same,'gender_effect':scores['MF']-same,'details':detail}
            control={'seed':seed,'name_pairs':len(runs['MF']),'methods':methods}
            controls.append(control)
            write(out/f'control_{key}_seed{seed}.json',control)
        all_results[key]={'full_baseline':full,'controls':controls}
        print(key, {m:full[m]['score'] for m in METHODS},flush=True)
    write(out/'scores.json',all_results)
    print('Scoring complete. Run python -m src.extension.analyze_self_debias',flush=True)

if __name__=='__main__':main()
