# Delivery contract audit and report

This standard-library Python interface packages existing finite-grid comparisons. It reports comparisons from frozen aggregate inputs. No model weights, raw answers or evaluator references are included.

Run in this directory, selecting a new output directory each time:

```
python3 delivery_contract_audit.py --contract inputs/contract.json --scores inputs/scores.csv --resources inputs/resources.csv --out replay_report
python3 -m unittest -v test_delivery_contract_audit.py
```

Expected: 156 contexts, 49 same-path best-set changes, 67 changes when the separate profile-known preflight control is included. The full comparison has 936 rows. example_nine_methods.csv shows the 1200B multicast/raw/H0 case with both same-path rules and nine configurations, including negative compute-matching results in example_interpretation.txt. Inputs are genuine frozen aggregate records, not new labels or generated model answers. All new packaging/selection outputs are post_freeze_exploratory.

SOURCE_BOUNDARY: contract metadata makes assumptions visible; running this report does not independently replay messages or score against gold. The scientific replay code, sealed policy cache and task-level audit remain in the separate internal package. The raw task-level audit remains restricted; the separate statistics/ directory supplies only anonymous derived metrics and statistical refitting code.

Aggregate inputs validate the declared task counts and coverage only; they do not verify unique task identities or establish task-level completeness. Statistical refitting is provided separately in statistics/.
