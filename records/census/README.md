# Census records

Power measurement at a named revision: patch sites, unittest asserts,
approx calls, skip markers, JS test files, runner-shaped paths.

Probes are copied from `catalog/CATALOG.json` into each record so a later
probe change cannot silently rewrite history.

A census is not a false-positive rate. It answers whether a later sweep
would have the power to see the rule it claims to measure.
