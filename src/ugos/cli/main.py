"""
DEPRECATED — this module is no longer the UGOS entry point.

`src/ugos/cli/main.py` duplicated functionality now consolidated into
`src/ugos/main.py` (the entry point documented in the README and Quick
Start guide). Its `status` subcommand was ported over as `--status`.

Use instead:
    python src/ugos/main.py --status
    python src/ugos/main.py --workflow <id> [--use-docker]

This file could not be deleted automatically (sandbox permissions on
this mount blocked unlink/rename of pre-existing files). Please delete
`src/ugos/cli/main.py` and the now-empty `src/ugos/cli/` directory by
hand, e.g.:

    rm -r src/ugos/cli
"""

raise SystemExit(
    "src/ugos/cli/main.py is deprecated. Run 'python src/ugos/main.py --status' instead."
)
