from collections import Counter
from .common import ROOT, read, csv_rows


def cohorts():
    curation=read(ROOT/'data/provenance/curation.json')
    groups={x['historical_id']:set(x['occurrences']) for x in curation['initial_groups']}
    occurrences=read(ROOT/'data/provenance/source_occurrences.json')['occurrences']
    selected={x['occurrence_id'] for x in occurrences if x['status'] in {'included','excluded_after_semantic_review'}}
    if len(occurrences)!=1382 or len(selected)!=360 or len(groups)!=285 or set.union(*groups.values())!=selected:
        raise ValueError('Source-occurrence selection changed.')
    for excluded in curation['excluded']:
        del groups[excluded['task_id']]
    if len(groups)!=282:
        raise ValueError('Reference-interpretation exclusions changed.')
    for merge in curation['merges']:
        groups[merge['keep']].update(groups.pop(merge['absorb']))
    if len(groups)!=280:
        raise ValueError('Duplicate consolidation changed.')
    for historical,tid in curation['historical_to_current'].items():
        if groups[historical]!=set(read(ROOT/'data/tasks'/(tid+'.json'))['occurrences']):
            raise ValueError('Task relabeling changed.')
    selection=read(ROOT/'data/selection.json')
    initial=set(selection['selected_tasks'])
    excluded={x['task_id'] for x in selection['excluded']['excluded_from_this_cohort']}
    final=set(read(ROOT/'data/cohort.json')['task_ids'])
    missing={x['task_id'] for x in read(ROOT/'records/main_missing.json')}
    if len(initial)!=184 or len(excluded)!=96 or initial & excluded or initial-missing!=final or len(final)!=168:
        raise ValueError('Program-eligibility selection changed.')


def literature():
    base=ROOT/'literature/search'
    if len(csv_rows(base/'queries.csv'))!=10 or len(csv_rows(base/'hits.csv'))!=241:
        raise ValueError('Search records changed.')
    screened=csv_rows(base/'screening.csv')
    if Counter(x['query_id'] for x in screened)!=Counter({f'Q{i:02}':8 for i in range(1,11)}):
        raise ValueError('Search screening window changed.')
    statuses=Counter(x['final_status'] for x in csv_rows(base/'candidates.csv'))
    if statuses!=Counter(included_evidence=17,included_boundary=4,excluded_scope_fulltext=2,
                          fulltext_unavailable=1,deferred_budget=15):
        raise ValueError('Literature selection changed.')
    if len(csv_rows(base/'evidence.csv'))!=24 or len(csv_rows(base/'taxonomy_source_crosswalk.csv'))!=23:
        raise ValueError('Evidence mapping changed.')
