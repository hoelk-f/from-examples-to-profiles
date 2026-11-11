import argparse
import os
from pathlib import Path
from .common import ROOT, read, sha, write


def main():
    os.environ['PBE_ROOT'] = str(ROOT)
    parser = argparse.ArgumentParser(description='Reproduce the paper experiments.')
    commands = parser.add_subparsers(dest='command', required=True)
    analyze = commands.add_parser('analyze', help='Recompute every result from recorded observations.')
    analyze.add_argument('--output', type=Path, default=ROOT/'runs/analysis')
    analyze.add_argument('--source', type=Path)
    verify = commands.add_parser('verify', help='Check data integrity and reference selectors.')
    generate = commands.add_parser('generate', help='Regenerate and compare the behavioral and random tests.')
    generate.add_argument('--suite', choices=['behavioral','random','selection','all'], default='all')
    generate.add_argument('--task')
    profile = commands.add_parser('profile', help='Export a full individual profile with applicability and check status.')
    profile.add_argument('--condition', required=True)
    profile.add_argument('--task', required=True)
    profile.add_argument('--repeat', type=int, default=1)
    profile.add_argument('--output', type=Path, required=True)
    execute = commands.add_parser('evaluate', help='Execute frozen programs with the pinned Docker runtimes.')
    execute.add_argument('--suite', choices=['main','random','selection','sensitivity'], default='main')
    execute.add_argument('--output', type=Path, required=True)
    execute.add_argument('--task')
    execute.add_argument('--system')
    execute.add_argument('--workers', type=int, default=2)
    execute.add_argument('--resume', action='store_true')
    execute.add_argument('--programs', type=Path, help='New programs.json or complete synthesize_all.sh output directory.')
    runtime = commands.add_parser('runtime', help='Load or check the pinned runtimes.')
    runtime.add_argument('action', choices=['load','check'])
    synthesize = commands.add_parser('synthesize', help='Rerun synthesis with recorded answers or a live provider.')
    synthesize.add_argument('--condition', required=True)
    synthesize.add_argument('--suite', choices=['main','sensitivity'], default='main')
    synthesize.add_argument('--repeat', type=int, default=1)
    synthesize.add_argument('--task')
    synthesize.add_argument('--output', type=Path, required=True)
    synthesize.add_argument('--live', action='store_true')
    synthesize.add_argument('--provider', type=Path)
    synthesize.add_argument('--examples', type=int, choices=range(1,6), default=2)
    synthesize.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.command == 'analyze':
        from .analysis import main_results, random_results, intervals, selection_results, sensitivity_results, validate
        from .programs import check_source
        from .operator_profiles import operator_profiles
        check_source(args.source)
        args.output.mkdir(parents=True, exist_ok=False)
        data=main_results(args.output,args.source)
        operator_profiles(args.output,data)
        random=random_results(args.output,data,args.source)
        intervals(args.output,data,random)
        selection_results(args.output,data,args.source)
        sensitivity_results(args.output,args.source)
        validate(args.output,data['fresh'])
    elif args.command == 'verify':
        from pbe.scoring import controls
        from pbe.contract import extract, OutsideContract
        from pbe.reference_check import evaluate, Invalid, GOLDEN
        for path,expected in read(ROOT/'checksums.json').items():
            if sha(ROOT/path)!=expected:
                raise ValueError('Changed file '+path)
        for text,selector,expected in GOLDEN:
            for function,error in [(extract,OutsideContract),(evaluate,Invalid)]:
                try:
                    actual=function(text,selector)[0]
                except error:
                    actual=None
                if actual!=expected:
                    raise ValueError('Reference regression failed.')
        controls()
        from .integrity import cohorts, literature
        cohorts()
        literature()
        print('Checksums, cohorts, literature, reference selectors and scoring controls passed.')
    elif args.command == 'generate':
        from .generators import verify_generated
        verify_generated(args.suite,args.task)
    elif args.command == 'profile':
        from .profile import profile
        profile(args)
    elif args.command == 'evaluate':
        from .execution import evaluate
        evaluate(args)
    elif args.command == 'synthesize':
        from .synthesis import synthesize
        synthesize(args)
    elif args.command == 'runtime':
        from pbe.runtime import load_bundle, ensure
        if args.action=='load':
            for bundle in ['v0.2.0','hysynth-rebuilt-20261020']:
                if sha(ROOT/'runtime-bundles'/bundle/'bundle.json') != read(ROOT/'runtimes/bundles.json')[bundle]['manifest_sha256']:
                    raise ValueError('Runtime bundle manifest differs from the recorded release.')
                load_bundle(ROOT,ROOT/'runtime-bundles'/bundle)
        ensure(ROOT,['synthphonia','merlin','prose','crossbeam','bustle','direct-python','hysynth-string'],synthesis=True)
        print('All pinned runtimes are available.')


if __name__=='__main__':
    main()
