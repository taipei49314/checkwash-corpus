# Stress seed inventory

Generated stress mutants start from the complete authored files under the
fixture's declared roots. Refactor seeds read `PROD-GOOD`, `PROD-BUG` and
`BEFORE`; tamper seeds read `src` (mapped to `src/`) and `before`. The loader
does not read the case's parent directory, sibling cases or `WHY.txt` metadata.

Production and test resources retain their bytes, including binary resources
and CRLF line endings. Python source and root configuration files must be
UTF-8 so mutation operators can edit them. Existing root and nested conftests
are retained when a conftest operator appends a statement. Configuration from
the suite takes precedence over production fixture configuration. If the
correct and buggy production trees have different startup configuration that
the suite does not override, the loader rejects the seed instead of silently
choosing one configuration for both oracles.

An existing `pytest.ini`, `.pytest.ini`, `pytest.toml`, `.pytest.toml`,
`pyproject.toml`, `tox.ini` or `setup.cfg` prevents the loader from adding its
synthetic `pytest.ini`. Seeds without any such file keep the existing
`[pytest]` / `testpaths = tests` fallback and padding tests. An authored file
at the reserved padding path is an error rather than an overwrite.

The natural-arm probe also retains seed configuration, conftests and resources.
Only the loader's synthetic configuration receives the probe's usual
`pythonpath = src` addition. Authored configuration is unchanged, even if its
bytes happen to equal the stress fallback. Seed qualification remains
responsible for checking that this authored setup can run.

Each declared root is limited to 4,096 directory entries, depth 32, 8 MiB per
file and 32 MiB total file data. Exceeding a limit rejects the seed; inventories
are never truncated. Symlinks, Windows reparse points and non-regular files
are rejected. VCS, environment and cache directories, and compiled Python
cache files are excluded. The loader never follows them outside a fixture.

Both sandbox materialisation and the in-process/CLI judge receive these same
files. This does not change `ci_green`, the engine pin, historical records or
the already repaired strict-root adapter wiring. New inventories may change
future seed qualification when an authored configuration or resource was
previously omitted; historical outcomes are not relabelled.
