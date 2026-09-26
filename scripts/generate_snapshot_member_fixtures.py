#!/usr/bin/env python3
"""Regenerate the golden member listings for committed firmware snapshots.

Run from any directory with::

    python scripts/generate_snapshot_member_fixtures.py

The listings are reviewable API-change diffs for the checked-in generated
modules. They are generated artifacts; update them with this script, never by
hand.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pyquadcortex.protocol.catalogs.coros_4_0_1 import models as models_401  # noqa: E402
from pyquadcortex.protocol.catalogs.coros_4_0_1 import options as options_401  # noqa: E402
from pyquadcortex.protocol.catalogs.coros_4_0_1 import params as params_401  # noqa: E402
from pyquadcortex.protocol.catalogs.coros_4_1_0 import models as models_410  # noqa: E402
from pyquadcortex.protocol.catalogs.coros_4_1_0 import options as options_410  # noqa: E402
from pyquadcortex.protocol.catalogs.coros_4_1_0 import params as params_410  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "generated"


def _members(snapshot, models, params, options):
    model_rows = [f"{name}={model_id}"
                  for name, model_id in sorted(models.ALL.items())]
    parameter_classes = sorted(set(params.BY_MODEL.values()),
                               key=lambda cls: cls.__name__)
    parameter_rows = [f"{cls.__name__}.{name}={member.value}"
                      for cls in parameter_classes
                      for name, member in cls.__members__.items()]
    option_rows = [f"{enum.__name__}.{name}={member.value}"
                   for enum in sorted(options.OPTION_LABELS,
                                      key=lambda item: item.__name__)
                   for name, member in enum.__members__.items()]
    return {
        f"model_members_{snapshot}.txt": model_rows,
        f"param_members_{snapshot}.txt": parameter_rows,
        f"option_members_{snapshot}.txt": option_rows,
    }


def main():
    snapshots = (
        ("coros_4_0_1", models_401, params_401, options_401),
        ("coros_4_1_0", models_410, params_410, options_410),
    )
    OUT.mkdir(parents=True, exist_ok=True)
    for snapshot, models, params, options in snapshots:
        for name, rows in _members(snapshot, models, params, options).items():
            (OUT / name).write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
