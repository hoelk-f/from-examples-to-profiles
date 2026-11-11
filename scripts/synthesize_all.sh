#!/usr/bin/env bash
set -euo pipefail
suite=${1:?Usage: bash scripts/synthesize_all.sh main-or-sensitivity output-directory [--resume]}
destination=${2:?Choose a new output directory}
resume=()
if [ "${3:-}" = --resume ]; then
    resume=(--resume)
elif [ "$#" -gt 2 ]; then
    exit 2
fi
case "$suite" in
    main) counts=2 ;;
    sensitivity) counts="1 2 3 4 5" ;;
    *) exit 2 ;;
esac
for n in $counts
do
    for condition in synthphonia merlin prose crossbeam bustle direct-python/gpt-oss-120b direct-python/qwen3.8-27b hysynth-string/gpt-oss-120b hysynth-string/qwen3.8-27b
    do
        repeats=1
        case "$condition" in
            direct-python/*) repeats=5 ;;
            hysynth-string/*) repeats=5
                if [ "$suite" = sensitivity ]; then repeats=3; fi ;;
        esac
        for ((repeat=1; repeat<=repeats; repeat++))
        do
            reproduce synthesize --suite "$suite" --condition "$condition" --examples "$n" --repeat "$repeat" --output "$destination/$condition/n$n/repeat-$repeat" "${resume[@]}"
        done
    done
done
