"""Command line interface for running a reproducible synthetic session."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .simulator import SimulationConfig, simulate


def main() -> None:
    parser = argparse.ArgumentParser(description="Educational trading desk simulator")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=1000)
    args = parser.parse_args()
    result = simulate(SimulationConfig(seed=args.seed, steps=args.steps))
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
