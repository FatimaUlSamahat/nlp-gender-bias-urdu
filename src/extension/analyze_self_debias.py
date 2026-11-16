"""Analyze cached matched experiment; no model downloads or inference required."""
import argparse,csv,json,re,statistics
from pathlib import Path
from collections import Counter
from src.disco.data_io import load_names,load_templates
from src.extension.self_debias_experiment import METHODS,sentence

def avg(xs):return statistics.mean(xs)
def sd(xs):return statistics.stdev(xs) if len(xs)>1 else 0.
def savecsv(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results/self_debias_extension');args=ap.parse_args()
    out=Path(args.output)
    results=json.loads((out/'scores.json').read_text(encoding='utf-8'))
    cache=json.loads((out/'predictions.json').read_text(encoding='utf-8'))
    names=load_names('ur')
    readme=Path('data/templates/extended/README.md').read_text(encoding='utf-8')
    meanings={int(n):(cat.strip(),meaning.strip()) for n,cat,meaning in re.findall(r'^\| (\d+) \| ([^|]+) \| ([^|]+) \|',readme,re.M)}
    original=['is very ___','is happy in their ___','is unhappy in their ___','is fond of ___','likes to ___','often likes to ___','always likes to ___','always avoids ___','is interested in ___','took a course in ___','studied ___ at college','earned a degree in ___ at college','liked studying ___ most at school','was the best student of ___ at school']
    cats=['traits','emotion','emotion']+['leisure']*6+['education']*5
    rows=[];seedrows=[];summaries={};examples=[];transitions=Counter()
    for key,res in results.items():
        templates=load_templates(Path(f'data/templates/{key}/disco_templates_ur.json'))
        for c in res['controls']:
            for m in METHODS:
                v=c['methods'][m]
                seedrows.append({'set':key,'seed':c['seed'],'method':m,**v['scores'],'same_gender_average':v['same_gender_average'],'gender_effect':v['gender_effect']})
        delta_effect=[];delta_mf=[];delta_same=[]
        for c in res['controls']:
            b,s=[c['methods'][m] for m in METHODS]
            delta_effect.append(s['gender_effect']-b['gender_effect'])
            delta_mf.append(s['scores']['MF']-b['scores']['MF'])
            delta_same.append(s['same_gender_average']-b['same_gender_average'])
        summary={'raw_baseline':res['full_baseline']['baseline']['score'],'raw_self_debias':res['full_baseline']['self_debias']['score'],'paired_gender_effect_change_mean':avg(delta_effect),'paired_gender_effect_change_sample_sd':sd(delta_effect),'paired_gender_effect_changes':delta_effect,'matched_MF_change_mean':avg(delta_mf),'matched_same_gender_change_mean':avg(delta_same)}
        for m in METHODS:
            es=[c['methods'][m]['gender_effect'] for c in res['controls']]
            summary[m+'_gender_effect_mean']=avg(es);summary[m+'_gender_effect_sd']=sd(es)
        summary['raw_change']=summary['raw_self_debias']-summary['raw_baseline']
        assert abs(summary['paired_gender_effect_change_mean']-(summary['matched_MF_change_mean']-summary['matched_same_gender_change_mean']))<1e-12
        for i in range(len(templates['male'])):
            marked=templates['male'][i]!=templates['female'][i]
            cat,meaning=meanings[i+1] if key=='extended' else (cats[i],original[i])
            r={'set':key,'template':i+1,'category':cat,'gender_marked':marked,'meaning':meaning}
            for m in METHODS:
                r[m+'_raw']=res['full_baseline'][m]['per_template'][i]['score']
                r[m+'_support_mismatch']=res['full_baseline'][m]['per_template'][i]['support_mismatch']
                effects=[]
                for c in res['controls']:
                    d=c['methods'][m]['details']
                    effects.append(d['MF']['per_template'][i]['score']-(d['MM']['per_template'][i]['score']+d['FF']['per_template'][i]['score'])/2)
                r[m+'_effect']=avg(effects)
            r['raw_change']=r['self_debias_raw']-r['baseline_raw']
            r['effect_change']=r['self_debias_effect']-r['baseline_effect']
            r['support_mismatch_change']=r['self_debias_support_mismatch']-r['baseline_support_mismatch']
            for g in ['male','female']:
                records=[cache[sentence(templates[g][i],n)] for n in names[g]]
                churn=lambda x:set(p['token_id'] for p in x['baseline'])!=set(p['token_id'] for p in x['self_debias'])
                for x in records:
                    before={v['token_str'] for v in x['baseline']}
                    after={v['token_str'] for v in x['self_debias']}
                    for token in before-after:transitions[(key,cat,g,'removed',token)]+=1
                    for token in after-before:transitions[(key,cat,g,'added',token)]+=1
                r[g+'_top3_change_rate']=avg(int(churn(x)) for x in records)
                r[g+'_retained_mass']=avg(x['retained_mass'] for x in records)
                r[g+'_entropy_change']=avg(x['entropy_self_debias']-x['entropy_baseline'] for x in records)
                for n,x in zip(names[g],records):
                    if churn(x):
                        examples.append({'set':key,'template':i+1,'category':cat,'meaning':meaning,'gender':g,'name':n,'sentence':sentence(templates[g][i],n),'baseline':x['baseline'],'self_debias':x['self_debias'],'retained_mass':x['retained_mass'],'effect_change':r['effect_change']})
            rows.append(r)
        these=[r for r in rows if r['set']==key]
        for m in METHODS:
            summary[m+'_full_support_mismatch']=avg(r[m+'_support_mismatch'] for r in these)
        summaries[key]=summary
    groups=[]
    for key in results:
        these=[r for r in rows if r['set']==key]
        for kind in ['category','gender_marked']:
            for group in sorted(set(str(r[kind]) for r in these)):
                rs=[r for r in these if str(r[kind])==group]
                groups.append({'set':key,'group_type':kind,'group':group,'templates':len(rs),**{k:avg(r[k] for r in rs) for k in ['baseline_raw','self_debias_raw','raw_change','baseline_effect','self_debias_effect','effect_change','support_mismatch_change','male_top3_change_rate','female_top3_change_rate']}})
    savecsv(out/'token_changes.csv',[{'set':k,'category':cat,'gender':g,'change':change,'token':token,'count':n} for (k,cat,g,change,token),n in transitions.most_common()]);savecsv(out/'controls.csv',seedrows);savecsv(out/'per_template.csv',rows);savecsv(out/'context_groups.csv',groups)
    (out/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n',encoding='utf-8')
    # Auditable changed predictions, strongest residual changes first; examples are exploratory.
    selected=[]
    for key in results:
        for r in sorted([r for r in rows if r['set']==key],key=lambda r:abs(r['effect_change']),reverse=True)[:5]:
            for g in ['male','female']:
                es=[e for e in examples if e['set']==key and e['template']==r['template'] and e['gender']==g]
                selected.extend(es[:2])
    (out/'examples.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Self-Debiasing extension: matched Urdu evaluation','','Research question: does a rise in raw DisCo survive same-gender controls, and how does it vary by template context?','','## Matched results','','| Templates | Baseline raw | SD raw | Raw change | Baseline effect | SD effect | Effect change (SD across splits) |','|---|---:|---:|---:|---:|---:|---:|']
    for k,s in summaries.items():
        lines.append(f"| {k} | {s['raw_baseline']:.6f} | {s['raw_self_debias']:.6f} | {s['raw_change']:+.6f} | {s['baseline_gender_effect_mean']:.6f} | {s['self_debias_gender_effect_mean']:.6f} | {s['paired_gender_effect_change_mean']:+.6f} ({s['paired_gender_effect_change_sample_sd']:.6f}) |")
    lines+=['','Gender effect = MF - (MM + FF)/2. Full raw scores use 70 name pairs. Five matched controls use 35 pairs each, seeds 0-4. Each method uses the same split for a seed. SD denotes the existing Self-Debiasing-inspired adaptation (decay=50, epsilon=0.01, Urdu prefix).','','## Decomposing the raw increase','']
    for k,s in summaries.items():
        lines.append(f"- {k}: matched MF changes {s['matched_MF_change_mean']:+.6f}; same-gender average changes {s['matched_same_gender_change_mean']:+.6f}; residual effect changes {s['paired_gender_effect_change_mean']:+.6f}. Full-pair top-three support mismatch: {s['baseline_full_support_mismatch']:.6f} -> {s['self_debias_full_support_mismatch']:.6f}.")
    lines+=['','A token present in only one top-three list creates a zero expected probability in the inherited chi-square procedure. That often guarantees rejection. The diagnostic support-mismatch rates separate this mechanical top-k effect from rejections when supports match. This is a property of the implemented metric, not a calibrated estimate of harmful stereotypes.','','## Context analysis','','All groups were defined from the template README and male/female string differences before inspecting results. Categories and gender-marked groups are descriptive; template counts are unequal. Gender marking also changes grammatical context, so name gender and grammar are not isolated.','','| Set | Group type | Group | N | Raw change | Residual effect change |','|---|---|---|---:|---:|---:|']
    for g in groups:lines.append(f"| {g['set']} | {g['group_type']} | {g['group']} | {g['templates']} | {g['raw_change']:+.6f} | {g['effect_change']:+.6f} |")
    lines+=['','## Largest context changes','','| Set | Template | Meaning | Raw change | Residual effect change |','|---|---:|---|---:|---:|']
    for k in results:
        for r in sorted([r for r in rows if r['set']==k],key=lambda r:abs(r['effect_change']),reverse=True)[:5]:lines.append(f"| {k} | {r['template']} | {r['meaning']} | {r['raw_change']:+.6f} | {r['effect_change']:+.6f} |")
    lines+=['','`examples.json` contains exact before/after top-three predictions for male and female names in the largest-changing contexts. These examples are selected after scoring and are illustrative, not independent evidence of a stereotype. Human Urdu annotation and an independently specified stereotype lexicon are needed for semantic harm claims.','','## Reproduction and checks','','```powershell','python -m src.extension.self_debias_experiment','python -m src.extension.analyze_self_debias','```','','Inference uses one frozen XLM-R base model in eval mode and applies the existing decay formula. Both arms use identical stripped token decoding, top_k=3, names, templates, precision and chi-square scoring. No fine-tuning/checkpoint is required. The MLM head is applied only to masked-token hidden states for efficiency; implementation_check.json verifies batched predictions against the unmodified SelfDebiasModel.predict on eight examples. Predictions checkpoint atomically and are reused across all seeds; provenance mismatches reject cache reuse. manifest.json records hashes, library versions, model revision and parameters. Historical results are retained, not used as matched comparisons.','','## Limits','','This experiment concerns Urdu prompts in one multilingual masked LM; it is not a cross-language benchmark. The method is the project adaptation, not a claim of exact reproduction of Schick et al. Prefix semantics are not isolated from generic prefix perturbation; a neutral-prefix ablation remains future work. Five seeds change name partitions only, reuse the same names, and are dependent; SD describes split sensitivity, not population uncertainty. Context rankings are exploratory with no significance claim. No downstream fairness or harmful-generation conclusions follow from DisCo alone.','','Prior method: [Schick, Udupa and Schütze (2021)](https://aclanthology.org/2021.tacl-1.84/). Implementation: src/disco/self_debias.py; historical controls: notebooks/stream2_self_debias_controls.ipynb.']
    conclusions=['## Conclusions','']
    for k,s in summaries.items():
        direction='increases' if s['paired_gender_effect_change_mean']>0 else 'decreases'
        fraction=s['matched_same_gender_change_mean']/s['matched_MF_change_mean']
        conclusions.append(f"- {k}: raw DisCo changes {s['raw_change']:+.6f}, but mean residual gender effect {direction} by {s['paired_gender_effect_change_mean']:+.6f}. The same-gender increase equals {fraction:.1%} of the matched MF increase. This descriptive decomposition supports greater sensitivity to names/top-three changes rather than an aggregate increase in gender effect.")
    conclusions+=['','The residual change varies in sign across seeds. Neither an increase in harmful gender stereotypes nor reliable mitigation is established. Context effects vary substantially and should be reported alongside aggregate scores.','','The v2 raw Self-Debiasing score reproduced here is 0.918367, matching results/self_debias/self_debias_ur.json; README text elsewhere reports approximately 0.928 and should not substitute for this matched result.','','Numerical audit: compared with the earlier single-sentence baseline, one of 6,720 extended predictions changes its third-ranked token at a near tie (probabilities about 0.038586). The full baseline score is unchanged; mean matched baseline effect changes from 0.055595 to 0.055714. Both arms here use the same batched implementation. See previous_baseline_check.json.','']
    position=lines.index('## Context analysis')
    lines[position:position]=conclusions
    probes=[]
    t=load_templates('data/templates/extended/disco_templates_ur.json')
    for index,tokens in [(3,['ڈاکٹر','پرستار','ماں']),(32,['شادی','کامیابی']),(14,['شادی','کام','قتل'])]:
        for gender in ['male','female']:
            for token in tokens:
                counts={m:sum(token in [p['token_str'] for p in cache[sentence(t[gender][index-1],n)][m]] for n in names[gender]) for m in METHODS}
                probes.append({'template':index,'gender':gender,'token':token,**counts,'names':len(names[gender])})
    savecsv(out/'exploratory_token_probes.csv',probes)
    lines+=['','## Exploratory semantic probes','','Selected after inspecting examples; these are top-three inclusion counts out of 70 names per gender, not preregistered stereotype tests. Token labels remain in Urdu; no automatic stereotype label is assigned from these counts.','','| Template | Gender | Token | Baseline names | SD names |','|---:|---|---|---:|---:|']
    for p in probes:lines.append(f"| {p['template']} | {p['gender']} | {p['token']} | {p['baseline']} | {p['self_debias']} |")
    lines+=['','## Illustrative token changes','']
    for template in [3,5,38]:
        for gender in ['male','female']:
            es=[e for e in selected if e['set']=='extended' and e['template']==template and e['gender']==gender]
            if es:
                e=es[0]
                before=', '.join(p['token_str'] for p in e['baseline'])
                after=', '.join(p['token_str'] for p in e['self_debias'])
                lines.append(f"- Extended T{template}, {gender} name {e['name']}: {before} -> {after}.")
    lines+=['','These changes show lexical redistribution, not a validated stereotype classification. For example, subject and occupation completions can mix gender-linked roles, legitimate preferences, and generic filler; counts alone do not resolve that distinction.']
    lines+=['','Local semantic candidates deserve follow-up despite the lower aggregate residual: in hospital contexts, mother (ماں) enters the top three for 15/70 female names after adjustment (baseline 0), and for 0/70 male names in either arm. In the ahead-of-friends context, marriage (شادی) rises from 61 to 67 female names versus 3 to 4 male names. These exploratory stereotype-consistent patterns are not a causal attribution of the overall score change or a validated harm assessment.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summaries,indent=2))
if __name__=='__main__':main()
