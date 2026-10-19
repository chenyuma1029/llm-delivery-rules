# Task-level statistical reproduction

Derived metrics for 700 tasks support the selection and uncertainty analyses. All task identifiers are anonymous aliases. The package contains no question text, generated response, reference answer, or raw replay trace.

## Run

Use Python 3.12 with the NumPy version in requirements.txt. From this directory:

```sh
python3 scripts/run_sanity_tests.py -v
python3 scripts/reproduce_selection.py --data-root . --out reproduced
python3 scripts/reproduce_intervals.py --data-root . --selection reproduced/oof_results.npz --out reproduced/conditional_intervals.json
python3 scripts/reproduce_selection.py --data-root . --out split_reproduced --all-splits
```

Output directories must be new. The scripts never read expected/: those values are supplied only for comparison after reproduction.

schema.json documents all axes, the twice-within-task-mean encoding, equal dataset weights, and resource units. folds.csv provides the original folds and all 20 alternate partitions. Aliases cannot reconstruct the original task-name hash order; supplied fold columns reproduce selection directly.

Conditional intervals use 10,000 task-cluster resamples within datasets with seed 20261008 and fixed out-of-fold choices. They exclude selector refitting uncertainty and multiplicity correction. The 20 refitted partitions describe split sensitivity, not population confidence intervals. Full denominators are retained, including failed delivery.

This package reproduces selection and interval estimates from frozen derived metrics. It does not independently verify original gold scoring, regenerate model outputs, or reconstruct message admission. Code is MIT; included derived data and documentation are CC BY 4.0; see ../LICENSE_SCOPE.md.
