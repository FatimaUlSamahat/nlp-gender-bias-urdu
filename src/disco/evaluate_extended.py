"""Run extended Urdu baseline and matched controls with reusable exact predictions."""
import os
os.environ['PYTHONUTF8'] = '1'
import hashlib, json, random, statistics, platform, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from importlib.metadata import version
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM, pipeline
from src.disco import multilingual_disco as scoring
from src.disco.data_io import load_names, load_templates, validate

out = Path('results/extended_urdu_baseline')
out.mkdir(parents=True, exist_ok=True)
model_id = 'xlm-roberta-base'
torch.set_num_threads(min(4, os.cpu_count() or 1))
print('Loading XLM-R on CPU', flush=True)
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForMaskedLM.from_pretrained(model_id)
model.eval()
fill = pipeline('fill-mask', model=model, tokenizer=tokenizer, device=-1)
cache_path = out / 'predictions.json'
cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
def save_cache():
    temporary = cache_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(cache, ensure_ascii=False), encoding='utf-8')
    temporary.replace(cache_path)
def cached_fill(sentence, top_k=3):
    assert top_k == 3
    if sentence not in cache:
        cache[sentence] = fill(sentence, top_k=top_k)
        if len(cache) % 100 == 0:
            save_cache()
            print(f'Cached {len(cache)} predictions', flush=True)
    return cache[sentence]
# Keep the repository scoring function unchanged; reuse identical model predictions.
scoring.AutoTokenizer.from_pretrained = lambda *a, **k: tokenizer
scoring.AutoModelForMaskedLM.from_pretrained = lambda *a, **k: model
scoring.pipeline = lambda *a, **k: cached_fill
path = Path('data/templates/extended/disco_templates_ur.json')
templates, names = load_templates(path), load_names('ur')
validate(templates, names)
metadata = {
    'language':'ur', 'model':model_id, 'templates_file':path.as_posix(),
    'templates_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'names_sha256':hashlib.sha256(Path('data/names/ur_names.json').read_bytes()).hexdigest(),
    'number_of_templates':48, 'top_k':3, 'python_version':platform.python_version(),
    'library_versions':{p:version(p) for p in ['torch','transformers','scipy','numpy','pandas','tokenizers','huggingface-hub']},
    'git_commit':subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
}
def write(name, payload):
    (out / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def score(nouns, tmpl):
    return float(scoring.disco_test(model_id, model_id, str(path), 'ur', top_k=3, nouns=nouns, templates=tmpl))
print('Baseline: 48 templates, 70 name pairs', flush=True)
baseline = {**metadata, 'score':score(names, templates), 'names_per_gender':len(names), 'date':datetime.now(timezone.utc).isoformat()}
write('disco_ur_xlm-roberta-base_extended.json', baseline)
save_cache()
controls=[]
for seed in range(5):
    rng=random.Random(seed)
    male,female=list(names['male']),list(names['female'])
    rng.shuffle(male); rng.shuffle(female)
    half=len(male)//2
    ma,mb,fa,fb=male[:half],male[half:2*half],female[:half],female[half:2*half]
    scores={}
    for label,a,b,tmpl in [
        ('MF',ma,fa,templates),
        ('MM',ma,mb,{'male':templates['male'],'female':templates['male']}),
        ('FF',fa,fb,{'male':templates['female'],'female':templates['female']})]:
        print(f'Seed {seed}: {label}',flush=True)
        scores[label]=score(pd.DataFrame({'male':a,'female':b}),tmpl)
    same=(scores['MM']+scores['FF'])/2
    result={**metadata,'seed':seed,'name_pairs_per_run':half,'scores':scores,'same_gender_average':same,'gender_effect':scores['MF']-same,'date':datetime.now(timezone.utc).isoformat()}
    controls.append(result)
    write(f'control_ur_xlm-roberta-base_extended_seed{seed}.json',result)
    save_cache()
    print(json.dumps(result),flush=True)
v2=json.loads(Path('results/disco_ur_xlm-roberta-base_v2.json').read_text(encoding='utf-8'))
v2controls=[json.loads(Path(f'results/recovered_controls/control_ur_xlm-roberta-base_seed{s}.json').read_text(encoding='utf-8')) for s in range(5)]
summary={'formula':'MF - (MM + FF) / 2','extended_baseline':baseline['score'],'v2_baseline':v2['score'],'baseline_difference':baseline['score']-v2['score'],'extended_gender_effect_mean':statistics.mean(c['gender_effect'] for c in controls),'extended_gender_effect_sample_sd':statistics.stdev(c['gender_effect'] for c in controls),'v2_gender_effect_mean':statistics.mean(c['gender_effect'] for c in v2controls),'v2_gender_effect_sample_sd':statistics.stdev(c['gender_effect'] for c in v2controls),'controls':controls,'v2_controls':v2controls,'caveat':'Historical v2 scores used different library versions. Seeds vary name splits only.'}
write('comparison.json',summary)
lines=['# Extended Urdu XLM-R baseline and controls','',f"Full baseline (70 pairs): extended {baseline['score']:.6f}; original Urdu v2 {v2['score']:.6f}; difference {summary['baseline_difference']:+.6f}.",'','Gender effect = MF - (MM + FF) / 2. Controls use 35 pairs per comparison.','','| Seed | MF | MM | FF | Same-gender average | Gender effect |','|---|---:|---:|---:|---:|---:|']
for c in controls:
    s=c['scores']; lines.append(f"| {c['seed']} | {s['MF']:.6f} | {s['MM']:.6f} | {s['FF']:.6f} | {c['same_gender_average']:.6f} | {c['gender_effect']:+.6f} |")
lines += ['',f"Extended gender effect: {summary['extended_gender_effect_mean']:.6f} +/- {summary['extended_gender_effect_sample_sd']:.6f} (sample SD, five seeds).",f"Original v2 gender effect: {summary['v2_gender_effect_mean']:.6f} +/- {summary['v2_gender_effect_sample_sd']:.6f}.",'','Historical v2 results use different library versions; interpret differences cautiously. Seeds vary name splits only. Raw DisCo scores include name-to-name variation.','','Run: `python -m src.disco.evaluate_extended`','Predictions are cached and reused without changing the repository scoring function.']
(out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(summary),flush=True)
