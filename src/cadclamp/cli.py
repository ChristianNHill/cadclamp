from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cadclamp.engine.score import score_file
from cadclamp.engine.types import FAIL, WARN


def _band_mark(band: str) -> str:
    return {"pass": "ok", WARN: "WARN", FAIL: "FAIL"}.get(band, band)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cadclamp")
    sub = parser.add_subparsers(dest="command", required=True)
    score = sub.add_parser("score", help="score mesh files for FDM printability")
    score.add_argument("paths", nargs="+", type=Path)
    score.add_argument("--json", type=Path, default=None, help="write full report cards to this JSON file")
    score.add_argument(
        "--nozzle", type=float, default=0.4, metavar="MM",
        help="nozzle diameter in mm (default 0.4); wall and feature thresholds scale with it",
    )
    score.add_argument(
        "--layer", type=float, default=0.2, metavar="MM",
        help="layer height in mm (default 0.2); sets the first-layer band for overhang checks",
    )
    args = parser.parse_args(argv)

    # Line width defaults to the nozzle diameter, the slicer convention.
    process = {"nozzle_mm": args.nozzle, "line_width_mm": args.nozzle, "layer_mm": args.layer}
    cards = []
    header = f"{'part':<32} {'printability':>12}  {'gates':<20} checks"
    print(header)
    print("-" * len(header))
    for path in args.paths:
        card = score_file(path, process=process)
        cards.append(card.to_dict())
        if card.gated_out:
            gate_txt = f"FAIL:{card.failure_code}"
            check_txt = "-"
            score_txt = "0.000"
        else:
            gate_txt = "all pass"
            check_txt = "  ".join(f"{c.check}={c.index:.2f}[{_band_mark(c.band)}]" for c in card.checks)
            score_txt = f"{card.printability:.3f}"
        print(f"{card.part:<32} {score_txt:>12}  {gate_txt:<20} {check_txt}")

    if args.json:
        args.json.write_text(json.dumps(cards, indent=2))
        print(f"\nfull report cards: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
