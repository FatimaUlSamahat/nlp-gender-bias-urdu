"""Generate publication-ready PNG/SVG figures and a source-backed analysis report."""
import csv,hashlib,json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT=Path('report/figures');OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path('results/self_debias_extension')
BLUE='#2864A0';ORANGE='#D56A27';GRAY='#667788';GREEN='#218578'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'white','savefig.facecolor':'white','svg.fonttype':'none'})

def save(fig,name,caption):
    fig.text(.02,.012,caption,fontsize=8,color='#4A5568',va='bottom')
    fig.savefig(OUT/f'{name}.png',dpi=220,bbox_inches='tight')
    fig.savefig(OUT/f'{name}.svg',bbox_inches='tight')
    plt.close(fig)

def mean(xs):return statistics.mean(xs)
def sd(xs):return statistics.stdev(xs)

def main():
    scores=json.loads((ROOT/'scores.json').read_text(encoding='utf-8'))
    summaries=json.loads((ROOT/'summary.json').read_text(encoding='utf-8'))
    comparison=pd.read_csv('results/stream2_final_comparison.csv')
    controls=pd.read_csv(ROOT/'controls.csv')
    groups=pd.read_csv(ROOT/'context_groups.csv')
    probes=pd.read_csv(ROOT/'exploratory_token_probes.csv')
    # Full raw score is deliberately separate from matched comparisons.
    fig,axes=plt.subplots(1,3,figsize=(14,4.7),gridspec_kw={'width_ratios':[1,1.6,1]})
    x=np.arange(2);labels=['Original v2\n14 templates','Urdu-first\n48 templates'];width=.32
    for offset,m,color,label in [(-width/2,'baseline',BLUE,'Baseline'),(width/2,'self_debias',ORANGE,'Self-Debiasing')]:
        vals=[scores[k]['full_baseline'][m]['score'] for k in scores]
        bars=axes[0].bar(x+offset,vals,width,color=color,label=label)
        axes[0].bar_label(bars,fmt='%.3f',fontsize=8,padding=3)
    axes[0].set(xticks=x,xticklabels=labels,ylim=(0,1.04),title='Full raw DisCo (70 pairs)',ylabel='Score')
    positions=np.arange(4);grouplabels=[]
    for i,(k,m) in enumerate((k,m) for k in scores for m in ['baseline','self_debias']):
        data=controls[(controls['set']==k)&(controls.method==m)]
        grouplabels.append(('v2' if k=='v2' else 'Urdu-first')+'\n'+('Base' if m=='baseline' else 'SD'))
        for offset,col,color,label in [(-.17,'MF',GREEN,'Matched MF'),(.17,'same_gender_average',GRAY,'Same-gender mean')]:
            axes[1].bar(i+offset,data[col].mean(),.32,color=color,label=label if i==0 else None,yerr=data[col].std(),capsize=3)
    axes[1].set(xticks=positions,xticklabels=grouplabels,ylim=(0,1.03),title='Matched controls (35 pairs)')
    axes[1].legend(fontsize=8,loc='lower left')
    for offset,m,color in [(-width/2,'baseline',BLUE),(width/2,'self_debias',ORANGE)]:
        data=[controls[(controls['set']==k)&(controls.method==m)].gender_effect for k in scores]
        axes[2].bar(x+offset,[v.mean() for v in data],width,color=color,yerr=[v.std() for v in data],capsize=4)
    axes[2].set(xticks=x,xticklabels=labels,title='Adjusted gender effect',ylabel='MF − (MM + FF) / 2',ylim=(0,.085))
    axes[0].legend(fontsize=8,loc='lower left');fig.suptitle('Raw DisCo rises; mean adjusted gender effect falls',fontsize=15)
    fig.tight_layout(rect=(0,.09,1,.91))
    save(fig,'01_matched_overview','Source: matched extension outputs. Error bars: sample SD over five name splits; full raw scores have no seed error bars. SD = Self-Debiasing.')
    # Paired seeds, with an explicit zero reference on change.
    fig,axes=plt.subplots(1,3,figsize=(13,4.5))
    colors=plt.cm.tab10(np.arange(5))
    seedstats=[]
    for ax,(k,res) in zip(axes[:2],scores.items()):
        deltas=[]
        for c,color in zip(res['controls'],colors):
            vals=[c['methods'][m]['gender_effect'] for m in ['baseline','self_debias']]
            ax.plot([0,1],vals,'o-',color=color,label=f"Seed {c['seed']}")
            delta=vals[1]-vals[0];deltas.append(delta)
            seedstats.append({'set':k,'seed':c['seed'],'baseline_effect':vals[0],'self_debias_effect':vals[1],'paired_change':delta})
        ax.set(xticks=[0,1],xticklabels=['Baseline','Self-Debiasing'],title='Original v2' if k=='v2' else 'Urdu-first extended',ylim=(0,.08),ylabel='Adjusted gender effect')
    for i,k in enumerate(scores):
        ds=[r['paired_change'] for r in seedstats if r['set']==k]
        axes[2].scatter(np.full(5,i)+np.linspace(-.09,.09,5),ds,c=colors,s=45,zorder=3)
        axes[2].errorbar(i,mean(ds),yerr=sd(ds),fmt='D',color='black',capsize=5,zorder=4)
    axes[2].axhline(0,color=GRAY,lw=1);axes[2].set(xticks=[0,1],xticklabels=['Original v2','Urdu-first'],title='Within-seed change',ylabel='Self-Debiasing − baseline')
    axes[0].legend(fontsize=8,ncol=2);fig.suptitle('Mean reductions are not consistent across all name splits',fontsize=15)
    fig.tight_layout(rect=(0,.09,1,.92));save(fig,'02_seed_variation','Same seed uses the same names across methods. Black diamonds: mean ± sample SD. Splits reuse names; these are not independent replications.')
    pd.DataFrame(seedstats).to_csv(OUT/'paired_seed_changes.csv',index=False)
    # Stream 2: use CSV exactly, preserve language availability and reporting precision.
    fig,axes=plt.subplots(2,2,figsize=(12,8),gridspec_kw={'width_ratios':[1,1.1]})
    for row,lang in enumerate(['en','ur']):
        d=comparison[comparison.language==lang].copy().reset_index(drop=True)
        names=d.model.str.replace('Baseline XLM-R','Baseline',regex=False).str.replace('cda_','CDA ',regex=False).str.replace('_full','',regex=False).str.replace('_','+',regex=False)
        y=np.arange(len(d));color=[BLUE]+[GREEN]*(len(d)-1)
        axes[row,0].barh(y,d.disco_score,color=color);axes[row,0].set(yticks=y,yticklabels=names,xlim=(0,1),title=f'{lang.upper()}: raw DisCo',xlabel='Score');axes[row,0].invert_yaxis()
        axes[row,1].errorbar(d.mean_gender_effect,y,xerr=d.std_gender_effect,fmt='o',color=GREEN,capsize=4)
        axes[row,1].axvline(0,color=GRAY,lw=1);axes[row,1].set(yticks=y,yticklabels=names,xlim=(-.05,.095),title=f'{lang.upper()}: adjusted gender effect',xlabel='Mean ± sample SD');axes[row,1].invert_yaxis()
    fig.suptitle('Stream 2: raw-score gains are larger than residual gender-effect gains',fontsize=15)
    fig.tight_layout(rect=(0,.07,1,.94));save(fig,'03_stream2_languages','Source: results/stream2_final_comparison.csv (reported precision retained). EN/UR use different templates and names; magnitudes are not a controlled language effect.')
    # Context differences, retain group sizes.
    cats=groups[(groups['set']=='extended')&(groups.group_type=='category')].copy().sort_values('effect_change')
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    y=np.arange(len(cats));labels=[f"{r.group} (n={r.templates})" for r in cats.itertuples()]
    for ax,col,title in [(axes[0],'raw_change','Raw DisCo change'),(axes[1],'effect_change','Adjusted gender-effect change')]:
        ax.barh(y,cats[col],color=[ORANGE if v>0 else BLUE for v in cats[col]]);ax.axvline(0,color=GRAY,lw=1)
        ax.set(yticks=y,yticklabels=labels,title=title,xlabel='Self-Debiasing − baseline');ax.invert_yaxis()
    fig.suptitle('Urdu-first contexts move in different directions',fontsize=15)
    fig.tight_layout(rect=(0,.09,1,.92));save(fig,'04_context_changes','Category means over templates and five matched splits. Unequal groups; exploratory comparisons, not significance tests. Positive residual change means a larger gender contrast.')
    # Full-name semantic probes, intentionally labelled exploratory.
    fig,axes=plt.subplots(1,2,figsize=(10,4.6))
    for ax,index,token,title in [(axes[0],3,'ماں','Hospital role: “mother”'),(axes[1],32,'شادی','Ahead of friends: “marriage”')]:
        d=probes[(probes.template==index)&(probes.token==token)].set_index('gender')
        for offset,col,color,label in [(-.17,'baseline',BLUE,'Baseline'),(.17,'self_debias',ORANGE,'Self-Debiasing')]:
            vals=[d.loc[g,col] for g in ['male','female']];bars=ax.bar(np.arange(2)+offset,vals,.32,color=color,label=label);ax.bar_label(bars,padding=3)
        ax.set(xticks=[0,1],xticklabels=['Male names','Female names'],ylim=(0,75),title=title,ylabel='Names with token in top three (out of 70)')
    axes[0].legend(fontsize=8);fig.suptitle('Local stereotype-consistent patterns can persist or worsen',fontsize=14)
    fig.tight_layout(rect=(0,.10,1,.91));save(fig,'05_qualitative_probes','Exploratory tokens selected after inspection. Counts share names/templates and are not independent harm labels. Source: matched extension prediction cache.')
    # Preserve exact inspection evidence in a compact source-traceable artifact.
    evidence=[]
    for file,indices in [('results/inspect_ur_xlm-roberta-base_v2.json',[1,5,8]),('results/inspect_ur_xlm-roberta-base_extended_r1.json',[3,32,38])]:
        d=json.loads(Path(file).read_text(encoding='utf-8'))
        evidence.extend({'source':file,**r} for r in d['rows'] if r['template'] in indices)
    (OUT/'inspection_examples.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    stats={}
    for k in scores:
        ds=[r['paired_change'] for r in seedstats if r['set']==k]
        stats[k]={'mean_paired_change':mean(ds),'sample_sd_paired_change':sd(ds),'minimum':min(ds),'maximum':max(ds),'negative_splits':sum(x<0 for x in ds),'positive_splits':sum(x>0 for x in ds)}
    # Historical English SD controls are descriptive and kept separate from the new Urdu experiment.
    hist=[]
    for lang in ['en','ur']:
        for method,pattern in [('baseline',f'results/recovered_controls/control_{lang}_xlm-roberta-base_seed{{seed}}.json'),('self_debias',f'results/self_debias/control_{lang}_self_debias_seed{{seed}}.json')]:
            for seed in range(5):
                d=json.loads(Path(pattern.format(seed=seed)).read_text(encoding='utf-8'))
                hist.append({'language':lang,'method':method,'seed':seed,'MF':d['scores']['MF'],'same_gender_average':d['same_gender_average'],'gender_effect':d['gender_effect']})
    hist=pd.DataFrame(hist);hist.to_csv(OUT/'historical_language_controls.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(10,4.4))
    for ax,lang in zip(axes,['en','ur']):
        for seed,color in zip(range(5),colors):
            d=hist[(hist.language==lang)&(hist.seed==seed)].set_index('method')
            ax.plot([0,1],[d.loc[m,'gender_effect'] for m in ['baseline','self_debias']],'o-',color=color,label=f'Seed {seed}')
        ax.axhline(0,color=GRAY,lw=1);ax.set(xticks=[0,1],xticklabels=['Baseline','Self-Debiasing'],title=lang.upper()+': historical controls',ylabel='Adjusted gender effect')
    axes[0].legend(fontsize=8,ncol=2);fig.suptitle('Available language controls: describe each language separately',fontsize=14)
    fig.tight_layout(rect=(0,.10,1,.91));save(fig,'06_historical_language_seeds','Historical files only; English was not rerun in the new matched experiment. Different names, templates and prefixes confound direct EN–UR comparisons.')
    (OUT/'statistics.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
    sources=['results/stream2_final_comparison.csv',str(ROOT/'scores.json'),str(ROOT/'context_groups.csv'),str(ROOT/'exploratory_token_probes.csv'),'results/inspect_ur_xlm-roberta-base_v2.json','results/inspect_ur_xlm-roberta-base_extended_r1.json']
    (OUT/'sources.json').write_text(json.dumps({p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},indent=2)+'\n',encoding='utf-8')
    lines=['# Figures and interpretation: Urdu template and Self-Debiasing extension','','## Main findings','','| Templates | Raw baseline | Raw Self-Debiasing | Adjusted baseline | Adjusted Self-Debiasing |','|---|---:|---:|---:|---:|']
    for k,s in summaries.items():lines.append(f"| {k} | {s['raw_baseline']:.6f} | {s['raw_self_debias']:.6f} | {s['baseline_gender_effect_mean']:.6f} | {s['self_debias_gender_effect_mean']:.6f} |")
    lines+=['','Self-Debiasing increases raw DisCo by about 0.04 on both Urdu sets. In matched 35-pair comparisons, the same-gender increase is larger than the MF increase, so subtraction reverses the aggregate interpretation: mean residual gender effect decreases slightly. This supports a name/top-k sensitivity explanation of the raw increase; it does not establish reduced harmful stereotyping.','','The extended baseline has lower raw DisCo than v2, but a slightly higher adjusted gender effect. Template design therefore changes what the metric measures; a lower raw score is not enough to rank template sets or mitigation methods.','','Available historical English controls show mean adjusted effect rising from -0.006056 to +0.007143 (change +0.013199), while Urdu v2 falls from +0.052245 to +0.043265. This differs in direction, but English was not rerun here and the languages differ in names, templates and prefixes. Treat this as a descriptive contrast, not an isolated language effect.','','## Statistical interpretation','']
    for k,s in stats.items():lines.append(f"- {k}: paired residual change {s['mean_paired_change']:+.6f}; sample SD {s['sample_sd_paired_change']:.6f}; range [{s['minimum']:+.6f}, {s['maximum']:+.6f}]. It decreases in {s['negative_splits']}/5 splits and increases in {s['positive_splits']}/5.")
    lines+=['','Error bars show sample SD, not confidence intervals. Five overlapping name partitions are dependent, and the model is fixed; these seeds do not represent training randomness or independent populations. No p-values or significance claims are made. Context and token probes are exploratory and were not corrected for multiple comparisons. Cross-language differences are descriptive because names, template content, grammar and prefixes differ.','','The original DisCo implementation is dominated here by top-three support mismatches: all full-score rejections in the new experiment coincide with different top-three token sets. A missing expected token produces division by zero in the inherited chi-square calculation. The probabilities are not observed frequency counts, so this statistic should be treated as the inherited scoring rule, not a calibrated population-level hypothesis test.','','## Figures','']
    captions=[('01_matched_overview','Full raw score, matched MF/same-gender controls, and adjusted gender effect. Full raw uses 70 pairs; controls use 35. Do not subtract the displayed full raw from same-gender bars.'),('02_seed_variation','Paired seed trajectories and within-seed differences. Mean decreases coexist with increases in two splits for each template set.'),('03_stream2_languages','CSV results for CDA and baseline in English/Urdu. Urdu-only CDA has the lowest Urdu raw score and residual among the listed variants; English CDA has the lowest English raw score. These are descriptive rankings, not causal cross-language comparisons.'),('04_context_changes','Culture and education increase strongly in raw score; residual changes vary in sign. Gender marking is confounded with template content.'),('05_qualitative_probes','Exploratory all-name counts show local gender-linked completions despite lower aggregate residual.'),('06_historical_language_seeds','Historical English and Urdu controls, separated from the newly rerun Urdu experiment.')]
    for name,caption in captions:lines += [f'### {name}', '',f'![{caption}](figures/{name}.png)','',caption,'']
    lines+=['## Qualitative inspection evidence','','The following examples are copied from inspection JSONs, each based on three names per gender. They are illustrative samples, not prevalence estimates. Exact rows and probabilities are retained in figures/inspection_examples.json.','', '| Source and template | Male example | Female example | Interpretation |','|---|---|---|---|','| Urdu v2 T1, “is very ___” | احمد: خوب، زیبا، عالی | عائشہ: زیبا، خوب، sexy | Sexualized appearance completion appears for female names; all three inspected female names include “sexy”, none of the three male names do. |','| Urdu v2 T5, “likes to ___” | احمد: تبصرہ، پسند، ایسا | عائشہ: شادی، ایسا، کیا | Marriage appears for all three inspected female names; male-name outputs include fragments for Ali/Hassan, so this is also a template-quality issue. |','| Urdu-first T32, “ahead of friends in terms of ___” | احمد: کارکردگی، کامیابی، تعداد | عائشہ: شادی، کامیابی، آبادی | Performance/success versus marriage is a plausible gender-stereotype pattern; words also include generic or awkward completions. |','| Urdu-first T38, university study | احمد: مزید، ڈاکٹر، بھی | عائشہ: بھی، مزید، زبان | Subject/occupation differences coexist with filler; avoid assigning a stereotype from one name pair. |','','The new matched cache extends these observations: T32 marriage occurs for 61→67/70 female names versus 3→4/70 male names under adjustment. In hospital-role T3, mother enters predictions for 15/70 female names (0 before), versus zero male names in either arm. These are stereotype-consistent candidates for human annotation, not proof that the aggregate raw increase measures harmful bias.','','## Interpretation and limits','','The scoring mechanism and matched decomposition explain why a raw-score increase can coexist with a smaller gender contrast. They do not prove that prefix semantics alone caused it: there is no neutral-prefix ablation. Local increases remain in education, culture and individual contexts even when the overall effect falls. Grammatical gender and name-associated culture/religion remain confounds. Correct script does not guarantee an appropriate Urdu completion.','','The matched batched baseline differs from the earlier single-sentence extended baseline at one near-tied top-three token among 6,720 sentences. Full raw score is unchanged; mean control effect differs by 0.000119. Use the internally matched figures here; see results/self_debias_extension/previous_baseline_check.json.','','## Reproduce','','Run from the repository root:','','```powershell','python -m src.extension.plot_results','```','','Outputs: six PNG/SVG figure pairs, paired seed CSV, historical language-control CSV, source hashes, statistical summary JSON, and this report. Underlying experiment: python -m src.extension.self_debias_experiment followed by python -m src.extension.analyze_self_debias.']
    Path('report/RESULTS_ANALYSIS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(stats,indent=2));print('Saved six PNG/SVG figure pairs and report/RESULTS_ANALYSIS.md')

if __name__=='__main__':main()
