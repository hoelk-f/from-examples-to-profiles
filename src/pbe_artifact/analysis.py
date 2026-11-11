from collections import defaultdict
from fractions import Fraction
from itertools import combinations, product
from statistics import mean, stdev
import math

from pbe.scoring import assertion_key, cells, score
from .common import ROOT, ORDER, OPS, read, rows, write, table, task, cases, passed, observations
from .programs import index, is_new, design


def main_results(out, source=None):
    programs = index('main', source)
    fresh = is_new(source)
    available = defaultdict(set)
    for p in programs:
        available[p['condition'], p['repeat']].add(p['task_id'])
    expected_groups = {(c, r) for c, r, n in design('main')}
    if set(available) != expected_groups:
        raise ValueError('Main analysis requires all 25 condition/repetition groups.')
    study_cohort = read(ROOT / 'data/cohort.json')['task_ids']
    cohort = sorted(set.intersection(*available.values()) & set(study_cohort))
    if not cohort or (not fresh and cohort != study_cohort):
        raise ValueError('The common task set differs from the recorded study.')
    write(out/'main_cohort.json', dict(task_ids=cohort, mode='new' if fresh else 'frozen',
        excluded_from_published_comparison=sorted(set(study_cohort)-set(cohort)),
        scope='Published comparison tasks with an eligible program in every condition and repetition.'))
    tasks = {tid: task(tid) for tid in cohort}
    obs = observations('main', source)
    metrics, profiles, operators, failed = {}, {}, {}, {}
    main_rows, profile_rows = [], []
    records = {}
    for p in programs:
        c, r, tid, pid = p['condition'], p['repeat'], p['task_id'], p['id']
        if tid not in tasks:
            continue
        key = c, r, tid
        records[key] = p
        verdicts, base_rows = {}, {}
        for x in cases('main', tid):
            raw = obs[pid, x['suite'], x['case_id']]
            value = passed(raw, x['expected'])
            verdicts[x['suite'], x['case_id']] = value
            if x['suite'] == 'training':
                if not value:
                    raise ValueError('A recorded program fails its demonstrations.')
                base_rows[x['case_id']] = dict(raw, expected=x['expected'])
        for suite in ['heldout', 'behavioral']:
            values = [v for (s, _), v in verdicts.items() if s == suite]
            metrics[*key, suite] = Fraction(sum(values), len(values))
        h, b = metrics[*key, 'heldout'], metrics[*key, 'behavioral']
        main_rows.append(dict(condition=c, program_repeat=r, task_id=tid,
            holdout_accuracy=float(h), behavioral_accuracy=float(b),
            holdout_fully_passed=h == 1, targeted_failed=b < 1))
        buckets, ops = defaultdict(dict), defaultdict(set)
        for ob in tasks[tid]['behavioral']['obligations']:
            if ob['status'] != 'planned':
                continue
            cid = ob['case_id']
            ops[ob['operator_id']].add(cid)
            for assertion in ob['assertions']:
                verdict = score(assertion, obs[pid, 'behavioral', cid], base_rows.get(assertion.get('base_id')))
                for cell in cells(ob, assertion):
                    akey = assertion_key(ob, assertion)
                    if akey in buckets[cell] and buckets[cell][akey] != verdict:
                        raise ValueError('Conflicting duplicate assertion.')
                    buckets[cell][akey] = verdict
        profiles[key] = {cell: (sum(v.values()), len(v)) for cell, v in buckets.items()}
        operators[key] = {op: Fraction(sum(verdicts['behavioral', cid] for cid in ids), len(ids)) for op, ids in ops.items()}
        failed[key] = {cid for (s, cid), value in verdicts.items() if s == 'behavioral' and not value}
        for cell, (n, total) in profiles[key].items():
            profile_rows.append(dict(condition=c, repeat=r, task_id=tid, dimension=cell[0],
                regime_family=cell[1], regime=cell[2], expectation=cell[3], passed=n, total=total, accuracy=n/total))
    results, operator_rows = [], []
    for c in ORDER:
        repeats = [1] if c in ORDER[:5] else list(range(1, 6))
        runs = []
        for r in repeats:
            h = [metrics[c, r, t, 'heldout'] for t in cohort]
            b = [metrics[c, r, t, 'behavioral'] for t in cohort]
            runs.append(dict(holdout_pct=float(mean(h)*100), behavioral_pct=float(mean(b)*100),
                holdout_full=sum(x == 1 for x in h), new_failures=sum(x == 1 and y < 1 for x, y in zip(h, b))))
        summary = dict(condition=c, tasks=len(cohort))
        for metric in runs[0]:
            values = [x[metric] for x in runs]
            summary[metric] = mean(values)
            summary[metric+'_sd'] = stdev(values) if len(values) > 1 else None
        results.append(summary)
        for op in OPS:
            tids = [t for t in cohort if op in operators[c, 1, t]]
            if not tids:
                continue
            h = float(mean(metrics[c, r, t, 'heldout'] for r in repeats for t in tids)*100)
            b = float(mean(operators[c, r, t][op] for r in repeats for t in tids)*100)
            operator_rows.append(dict(condition=c, operator=op, tasks=len(tids), heldout_pct=h, behavioral_pct=b, difference_pp=b-h))
    overlaps = []
    for a, b in combinations(ORDER, 2):
        for level in ['tasks', 'inputs']:
            values = []
            for ra, rb in product([1] if a in ORDER[:5] else range(1,6), [1] if b in ORDER[:5] else range(1,6)):
                if level == 'tasks':
                    x, y = ({t for t in cohort if failed[c,r,t]} for c,r in [(a,ra),(b,rb)])
                else:
                    x, y = ({(t,cid) for t in cohort for cid in failed[c,r,t]} for c,r in [(a,ra),(b,rb)])
                values.append(len(x & y)/len(x | y) if x | y else 1.0)
            overlaps.append(dict(level=level, condition_a=a, condition_b=b, jaccard=mean(values), min=min(values), max=max(values), repeat_pairs=len(values)))
    profile_counts = defaultdict(int)
    for tid in cohort:
        for control in [False, True]:
            eligible = [(c,r,tid) for c in ORDER for r in ([1] if c in ORDER[:5] or control else range(1,6))
                        if metrics[c,r,tid,'heldout'] == 1]
            differing, equal = False, False
            for a,b in combinations(eligible, 2):
                if a[0] == b[0]:
                    continue
                differs = any(Fraction(*profiles[a][cell]) != Fraction(*profiles[b][cell]) for cell in profiles[a].keys() & profiles[b].keys())
                differing |= differs
                equal |= differs and metrics[*a,'behavioral'] == metrics[*b,'behavioral']
            prefix = 'first_repeat_' if control else ''
            profile_counts[prefix+'different_profiles'] += differing
            profile_counts[prefix+'equal_accuracy_different_profiles'] += equal
    table(out/'main.csv', results)
    table(out/'main_tasks.csv', main_rows)
    table(out/'operators.csv', operator_rows)
    table(out/'overlap.csv', overlaps)
    table(out/'profiles.csv', profile_rows)
    write(out/'profile_counts.json', dict(profile_counts))
    common = set.intersection(*[{(t,cid) for t in cohort for cid in failed[c,r,t]}
                              for c,r in available])
    all_holdout = [x for x in sorted(common) if all(metrics[c,r,x[0],'heldout']==1 for c,r in available)]
    write(out/'shared_failures.json',dict(cases=sorted(common),all_holdout_pass_cases=all_holdout))
    examples=[]
    for c,r in available:
        for tid,cid in sorted(common):
            case=next(x for x in tasks[tid]['behavioral']['cases'] if x['case_id']==cid)
            observed=obs[records[c,r,tid]['id'],'behavioral',cid]
            examples.append(dict(condition=c,repeat=r,task_id=tid,case_id=cid,input=case['input'],
                                 expected=case['expected_output'],status=observed['status'],actual=observed['actual']))
    table(out/'shared_failure_outputs.csv',examples)
    print('Main results and profiles reproduced on',len(cohort),'tasks.',flush=True)
    return dict(tasks=tasks, cohort=cohort, records=records, metrics=metrics, profiles=profiles,
                operators=operators, failed=failed, observations=obs, main_rows=main_rows, fresh=fresh)


def random_results(out, data, source=None):
    programs = {p['id']:p for p in data['records'].values()}
    definitions = {tid: {c['case_id']:c for c in cases('random', tid)} for tid in data['cohort']}
    counts = defaultdict(lambda: [0, 0])
    for row in rows((source or ROOT/'records')/'random.jsonl.gz'):
        if row['program_id'] not in programs:
            continue
        p = programs[row['program_id']]
        case = definitions[p['task_id']][row['case_id']]
        key = p['condition'],p['repeat'],p['task_id'],case['suite'],case['sampling_repeat']
        counts[key][0] += passed(row, case['expected'])
        counts[key][1] += 1
    result = []
    for (c,r,t,g,d),(ok,total) in sorted(counts.items()):
        if total != len(data['tasks'][t]['behavioral']['cases']):
            raise ValueError('Random test budget mismatch.')
        result.append(dict(condition=c,program_repeat=r,task_id=t,generator=g,sampling_repeat=d,
            random_accuracy=ok/total,holdout_fully_passed=data['metrics'][c,r,t,'heldout']==1,
            targeted_failed=data['metrics'][c,r,t,'behavioral']<1,random_failed=ok<total))
    if len(result) != 25*len(data['cohort'])*20:
        raise ValueError('Incomplete random observations.')
    table(out/'random_tasks.csv',result)
    print('Random results reproduced.',flush=True)
    return result


def intervals(out, data, random_rows):
    from .bootstrap import build_vectors, bootstrap_vectors
    import numpy as np
    values, metadata, variation = build_vectors(data['main_rows'],random_rows,ORDER,data['cohort'])
    lo,hi,percentile,distribution,messages = bootstrap_vectors(values,20000,20261103)
    results=[]
    for i,meta in enumerate(metadata):
        results.append(dict(**meta,estimate_pp=float(values[i].mean()*100),
            ci95_low_pp=float(lo[i]*100) if math.isfinite(lo[i]) else None,
            ci95_high_pp=float(hi[i]*100) if math.isfinite(hi[i]) else None,
            percentile95_low_pp=float(percentile[0,i]*100),percentile95_high_pp=float(percentile[1,i]*100)))
    table(out/'intervals.csv',results)
    write(out/'variation.json',variation)
    lookup={(x['condition'],x['metric'],x['generator']):x for x in results}
    spread={(x['condition'],x['metric'],x['generator']):x for x in variation}
    random_summary=[]
    scale=len(data['cohort'])/100
    for c in ORDER:
        row=dict(condition=c,targeted=lookup[c,'targeted_additional_failures','']['estimate_pp']*scale)
        for g in ['nominal','broad']:
            row[g]=lookup[c,'random_additional_failures',g]['estimate_pp']*scale
            row[g+'_draw_sd']=spread[c,'random_additional_failures',g]['draw_sd_pp']*scale
        delta=lookup[c,'random_minus_targeted','broad']
        row.update(delta=row['broad']-row['targeted'],
                   ci95_low=None if delta['ci95_low_pp'] is None else delta['ci95_low_pp']*scale,
                   ci95_high=None if delta['ci95_high_pp'] is None else delta['ci95_high_pp']*scale,
                   nonzero_tasks=delta['nonzero_tasks'])
        random_summary.append(row)
    table(out/'random.csv',random_summary)
    sensitivity=[]
    groups=[' + '.join(sorted(data['tasks'][t]['collections'])) for t in data['cohort']]
    for group in sorted(set(groups)):
        mask=np.array([g!=group for g in groups])
        for meta,estimate in zip(metadata,values[:,mask].mean(axis=1)):
            sensitivity.append(dict(**meta,excluded_source=group,tasks=int(mask.sum()),estimate_pp=float(estimate*100)))
    table(out/'leave_source_out.csv',sensitivity)
    print('117 paired bootstrap intervals reproduced.',flush=True)


def sensitivity_results(out, source=None):
    programs=index('sensitivity',source)
    obs=observations('sensitivity',source)
    by_task=defaultdict(list)
    scores={}
    for p in programs:
        counts=defaultdict(list)
        for case in cases('sensitivity',p['task_id']):
            row=obs[p['id'],case['suite'],case['case_id']]
            counts[case['suite']].append(passed(row,case['expected']))
        scores[p['condition'],p['repeat'],p['examples'],p['task_id']]={s:mean(v) for s,v in counts.items()}
        by_task[p['task_id']].append(p)
    cohort=sorted(t for t,ps in by_task.items() if {(p['condition'],p['repeat'],p['examples']) for p in ps}==design('sensitivity'))
    if not cohort or (not is_new(source,'sensitivity') and len(cohort)!=8):
        raise ValueError('Sensitivity cohort differs.')
    result=[]
    for c in ORDER:
        for n in range(1,6):
            repeats=range(1,4) if c.startswith('hysynth') else range(1,6) if c.startswith('direct') else [1]
            for suite in ['heldout','behavioral']:
                means=[mean(scores[c,r,n,t][suite] for t in cohort)*100 for r in repeats]
                result.append(dict(condition=c,examples=n,metric=suite,tasks=len(cohort),runs=len(means),
                    mean_pct=mean(means),sample_sd_pp=stdev(means) if len(means)>1 else None))
    table(out/'sensitivity.csv',result)
    write(out/'sensitivity_cohort.json',cohort)
    print('Sensitivity results computed on',len(cohort),'tasks.',flush=True)


def selection_results(out, data, source=None):
    import hashlib
    import numpy as np
    from .bootstrap import bootstrap_vectors
    policies=['H','G','O','O_plus','P']
    aliases=read(ROOT/'data/selection/instance_to_group.json')
    inputs={t:read(ROOT/'data/selection/inputs'/f'{t}.json') for t in data['cohort']}
    memberships={}
    for t,doc in inputs.items():
        groups=defaultdict(set)
        for row in doc['memberships']:
            if row['eligible']:
                groups[row['scenario'],row['draw']].add(row['case_id'])
        memberships[t]=groups
    obs=observations('selection',source)
    group_scores={}
    for p in index('selection',source):
        tid=p['task_id']
        if tid not in inputs:
            continue
        verdicts={c['case_id']:passed(obs[p['id'],'new',c['case_id']],c['expected'])
                  for c in inputs[tid]['execution_cases']}
        group_scores[p['id']]={k:Fraction(sum(verdicts[cid] for cid in ids),len(ids)) for k,ids in memberships[tid].items()}
    templates={(x['task_id'],x['scenario']):x for x in read(ROOT/'data/selection/generation_templates.json')}
    values,pure=defaultdict(list),defaultdict(list)
    context_rows=[]
    checked=0
    changed_policies=0
    for reference in rows(ROOT/'data/selection/policies.jsonl.gz'):
        t,s,b=reference['task_id'],reference['scenario'],reference['block']
        if t not in inputs:
            continue
        template=templates[t,s]
        cell=tuple(template['profile_cell'])
        ids={x['case_id'] for x in template['templates']}
        op_counts=defaultdict(int)
        group_counts=defaultdict(int)
        all_groups=defaultdict(set)
        for ob in data['tasks'][t]['behavioral']['obligations']:
            if ob['status']=='planned':
                group=(ob['operator_id'],ob['parameter']['side'] if ob['operator_id']=='S01' else 'all')
                all_groups[group].add(ob['case_id'])
        for x in template['templates']:
            op_counts[x['operator']]+=1
            group_counts[x['operator'],x['side']]+=1
        scores={p:{} for p in policies}
        available={}
        for c in ORDER:
            r=1 if c in ORDER[:5] else b
            key=c,r,t
            rec=data['records'][key]
            scores['H'][c]=data['metrics'][*key,'heldout']
            scores['G'][c]=data['metrics'][*key,'behavioral']
            scores['O'][c]=sum(Fraction(n,len(ids))*data['operators'][key][op] for op,n in op_counts.items())
            scores['P'][c]=Fraction(*data['profiles'][key][cell])
            by_case={x['case_id']:x for x in data['tasks'][t]['behavioral']['cases']}
            scores['O_plus'][c]=sum(Fraction(n,len(ids))*Fraction(sum(
                passed(data['observations'][rec['id'],'behavioral',cid],by_case[cid]['expected_output'])
                for cid in all_groups[g]),len(all_groups[g])) for g,n in group_counts.items())
            old_repeat=0 if c in ORDER[:5] else b
            alias=c.replace('/','__')+f'__r{old_repeat}__{t}'
            available[c]=group_scores[rec['id'] if data['fresh'] else aliases[alias]]
        raw={p:[c for c in ORDER if scores[p][c]==max(scores[p].values())] for p in policies}
        selected={p:(raw[p] if p=='H' else [c for c in raw[p] if scores['G'][c]==max(scores['G'][x] for x in raw[p])]) for p in policies}
        for p in policies:
            if selected[p]!=reference['policies'][p]['maximizers'] or raw[p]!=reference['policies'][p]['raw_maximizers']:
                if not data['fresh']:
                    raise ValueError('Selection policy differs from the recorded design.')
                changed_policies+=1
            for d in range(1,6):
                values[t,s,p].append(mean(available[c][s,d] for c in selected[p]))
                pure[t,s,p].append(mean(available[c][s,d] for c in raw[p]))
        context_rows.append(dict(task_id=t,scenario=s,block=b,
            **{p+'_selected':'|'.join(selected[p]) for p in policies}))
        checked+=1
    def task_means(source):
        return {t:{p:mean(mean(source[t,s,p]) for s in sorted({k[0] for k in memberships[t]})) for p in policies} for t in data['cohort']}
    full,raw_scores=task_means(values),task_means(pure)
    delta=np.array([float(full[t]['P']-full[t]['G']) for t in data['cohort']])
    namespace=read(ROOT/'data/selection/analysis_design.json')['seed_namespace']
    seed=int(hashlib.sha256(namespace.encode()).hexdigest(),16)
    lo,hi,percentile,distribution,messages=bootstrap_vectors(delta[None,:],20000,seed)
    result=dict(tasks=len(full),selection_decisions=checked,
        accuracy_percent={p:float(mean(full[t][p] for t in full)*100) for p in policies},
        pure_score_accuracy_percent={p:float(mean(raw_scores[t][p] for t in full)*100) for p in policies},
        profile_minus_overall_pp=float(delta.mean()*100),
        ci95_low_pp=float(lo[0]*100) if math.isfinite(lo[0]) else None,
        ci95_high_pp=float(hi[0]*100) if math.isfinite(hi[0]) else None,
        positive_tasks=int(sum(delta>0)),negative_tasks=int(sum(delta<0)),equal_tasks=int(sum(delta==0)),
        operator_profile_different_selections=sum(x['O_selected']!=x['P_selected'] for x in context_rows),
        policy_comparisons_changed_from_reference=changed_policies)
    write(out/'selection.json',result)
    table(out/'selection.csv',[dict(policy=p,accuracy_pct=result['accuracy_percent'][p],
          delta_vs_overall_pp=result['accuracy_percent'][p]-result['accuracy_percent']['G']) for p in ['H','G','O','P']])
    table(out/'selection_tasks.csv',[dict(task_id=t,**{p:float(full[t][p]) for p in policies}) for t in full])
    table(out/'selection_decisions.csv',context_rows)
    scenario_rows=[]
    for s in sorted({key[1] for key in values}):
        tids=sorted({t for t,scenario,p in values if scenario==s})
        scores={p:float(mean(mean(values[t,s,p]) for t in tids)*100) for p in policies}
        scenario_rows.extend(dict(scenario=s,tasks=len(tids),policy=p,accuracy_pct=scores[p],
                                 delta_vs_overall_pp=scores[p]-scores['G']) for p in policies)
    table(out/'selection_scenarios.csv',scenario_rows)
    print('Program selection reproduced across',checked,'decisions.',flush=True)


def validate(out, fresh=False):
    from .common import csv_rows
    if fresh:
        differences=[]
        for name,reference_name,keys,fields in [
            ('main.csv','comparison.csv',['condition'],['holdout_pct','behavioral_pct']),
            ('operators.csv','operators.csv',['condition','operator'],['heldout_pct','behavioral_pct']),
            ('intervals.csv',None,['condition','metric','generator'],['estimate_pp','ci95_low_pp','ci95_high_pp'])]:
            expected=csv_rows(ROOT/'reference'/reference_name) if reference_name else read(ROOT/'reference/uncertainty/summary.json')['results']
            lookup={tuple(x[k] for k in keys):x for x in expected}
            for row in csv_rows(out/name):
                old=lookup[tuple(row[k] for k in keys)]
                for field in fields:
                    a=None if row[field]=='' else float(row[field])
                    b=None if old[field] in ('',None) else float(old[field])
                    if a!=b and (a is None or b is None or abs(a-b)>1e-9):
                        differences.append(dict(result=name,**{k:row[k] for k in keys},field=field,value=a,reference=b))
        sensitivity={(r['condition'],r['example_count']):r for r in read(ROOT/'reference/sensitivity.json')['combined']['conditions']}
        for row in csv_rows(out/'sensitivity.csv'):
            old=sensitivity[row['condition'],int(row['examples'])][row['metric']]
            for field,key in [('mean_pct','mean'),('sample_sd_pp','sample_sd')]:
                a=None if row[field]=='' else float(row[field])
                b=None if old[key] is None else old[key]*100
                if a!=b and (a is None or b is None or abs(a-b)>1e-9):
                    differences.append(dict(result='sensitivity.csv',condition=row['condition'],
                        examples=row['examples'],metric=row['metric'],field=field,value=a,reference=b))
        table(out/'reference_differences.csv',differences)
        selection=read(out/'selection.json')
        old_selection=read(ROOT/'reference/selection.json')
        write(out/'validation.json',dict(passed=True,mode='new',exact_study_agreement_required=False,
            main_cohort=read(out/'main_cohort.json'),sensitivity_cohort=read(out/'sensitivity_cohort.json'),
            changed_reference_values=len(differences),selection_decisions=selection['selection_decisions'],
            changed_policy_comparisons=selection['policy_comparisons_changed_from_reference'],
            selection_accuracy_change_pp={p:value-old_selection['overall_accuracy_percent'][p]
                                          for p,value in selection['accuracy_percent'].items()},
            pure_selection_accuracy_change_pp={p:value-old_selection['pure_score_control']['accuracy_percent'][p]
                                              for p,value in selection['pure_score_accuracy_percent'].items()}))
        print('New-program analysis completed. See validation.json and reference_differences.csv.',flush=True)
        return
    def close(actual,expected):
        if abs(float(actual)-float(expected))>1e-9:
            raise ValueError(f'Reference mismatch: {actual} versus {expected}')
    reference=ROOT/'reference'
    for name,keys,fields in [
        ('main.csv',['condition'],['holdout_pct','behavioral_pct']),
        ('operators.csv',['condition','operator'],['heldout_pct','behavioral_pct','difference_pp']),
        ('overlap.csv',['level','condition_a','condition_b'],['jaccard','min','max'])]:
        expected={tuple(x[k] for k in keys):x for x in csv_rows(reference/('comparison.csv' if name=='main.csv' else name))}
        for row in csv_rows(out/name):
            old=expected[tuple(row[k] for k in keys)]
            for field in fields:
                close(row[field],old[field])
    expected=read(reference/'uncertainty/summary.json')['results']
    actual=csv_rows(out/'intervals.csv')
    if len(actual)!=len(expected):
        raise ValueError('Interval count mismatch.')
    for a,b in zip(actual,expected):
        if (a['condition'],a['metric'],a['generator'])!=(b['condition'],b['metric'],b['generator']):
            raise ValueError('Interval order mismatch.')
        for field in ['estimate_pp','ci95_low_pp','ci95_high_pp','percentile95_low_pp','percentile95_high_pp']:
            if b[field] is None:
                if a[field]!='':
                    raise ValueError('A constant vector received an informative interval.')
            else:
                close(a[field],b[field])
    if read(out/'shared_failures.json') != read(reference/'shared_failures.json'):
        raise ValueError('Shared failures differ from the reference.')
    counts=read(reference/'profiles.json')['task_level_counts']
    expected_counts={prefix+name:counts[control][field] for prefix,control in [('', 'all_'),('first_repeat_','first_repeat_')]
                     for name,field in [('different_profiles','different_profile_pairs'),
                                        ('equal_accuracy_different_profiles','equal_total_different_profile_pairs')]}
    if read(out/'profile_counts.json') != expected_counts:
        raise ValueError('Profile comparison counts differ.')
    actual=read(out/'selection.json')
    expected=read(reference/'selection.json')
    for p,value in actual['accuracy_percent'].items():
        close(value,expected['overall_accuracy_percent'][p])
        close(actual['pure_score_accuracy_percent'][p],expected['pure_score_control']['accuracy_percent'][p])
    close(actual['positive_tasks'],expected['primary_P_minus_G']['positive_tasks'])
    close(actual['negative_tasks'],expected['primary_P_minus_G']['negative_tasks'])
    close(actual['operator_profile_different_selections'],expected['policy_choice_differences']['P-O']['contexts'])
    close(actual['profile_minus_overall_pp'],expected['primary_P_minus_G']['point_pp'])
    close(actual['ci95_low_pp'],expected['primary_P_minus_G']['bca_pp'][0])
    close(actual['ci95_high_pp'],expected['primary_P_minus_G']['bca_pp'][1])
    expected={(r['condition'],r['example_count']):r for r in read(reference/'sensitivity.json')['combined']['conditions']}
    for row in csv_rows(out/'sensitivity.csv'):
        old=expected[row['condition'],int(row['examples'])][row['metric']]
        close(row['mean_pct'],old['mean']*100)
        if old['sample_sd'] is not None:
            close(row['sample_sd_pp'],old['sample_sd']*100)
    expected={(r['mode'],r['operator']):r for r in read(reference/'operator_profiles.json')}
    actual_rows=csv_rows(out/'operator_profile_counts.csv')
    if len(actual_rows)!=len(expected):
        raise ValueError('Operator comparison coverage differs.')
    for row in actual_rows:
        old=expected[row['mode'],row['operator']]
        for field,value in old.items():
            if str(value)!=row[field]:
                raise ValueError('Local operator comparison differs: '+field)
    scenarios=read(reference/'selection.json')['scenario_results']
    for row in csv_rows(out/'selection_scenarios.csv'):
        close(row['accuracy_pct'],scenarios[row['scenario']]['accuracy_percent'][row['policy']])
    write(out/'validation.json',dict(passed=True,main_tasks=168,intervals=len(actual) if isinstance(actual,list) else 117,
                                   selection_decisions=2990,sensitivity_tasks=8,tolerance=1e-9))
    print('All reported numerical checks passed.',flush=True)
