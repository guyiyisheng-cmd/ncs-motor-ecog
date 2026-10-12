#!/usr/bin/env python3
"""NCS CLI: self-test, demo, run real arrays, compare reruns, export code only."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import json

ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("self-test", help="software tests only; not a patient-data run")
    demo = sub.add_parser("demo", help="explicitly synthetic end-to-end numerical test")
    demo.add_argument("--out", type=Path, required=True)
    run = sub.add_parser("run", help="compute from source-adapted, explicitly keyed arrays")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    compare = sub.add_parser("compare", help="numeric comparison of two completed runs")
    compare.add_argument("first", type=Path); compare.add_argument("second", type=Path)
    compare.add_argument("--rtol", type=float, default=1e-10); compare.add_argument("--atol", type=float, default=1e-12)
    export = sub.add_parser("export-code", help="create code-only ZIP; never push to GitHub")
    export.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "self-test":
        return subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=False).returncode
    try:
        from ncs_method.runner import run as execute
        from ncs_method.fixtures import make_fixture
        from ncs_method.io import compare_runs, export_code, write_json
        if args.command == "demo":
            if args.out.exists():
                parser.error("demo output already exists; choose a new directory")
            cfg = make_fixture(args.out / "SYNTHETIC_TEST_INPUT", n_resamples=100)
            execute(cfg, args.out / "run_1")
            execute(cfg, args.out / "run_2")
            result = compare_runs(args.out / "run_1", args.out / "run_2")
            write_json(args.out / "REPRODUCIBILITY_TEST.json", result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["passed"] else 2
        if args.command == "run":
            execute(args.config, args.out)
            print("Output:", args.out.resolve())
        elif args.command == "compare":
            result = compare_runs(args.first, args.second, args.rtol, args.atol)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["passed"] else 2
        elif args.command == "export-code":
            print(json.dumps(export_code(ROOT, args.out), ensure_ascii=False, indent=2))
        return 0
    except ModuleNotFoundError as exc:
        print(f"缺少依赖模块 {exc.name}。请在独立环境安装 requirements.txt；不要覆盖现有科研环境。", file=sys.stderr)
        return 3
    except (ValueError, KeyError, OSError) as exc:
        # Paths/details remain on the local console; don't auto-upload this output.
        print(f"未完成本次计算：{type(exc).__name__}: {exc}\n已有输入与历史结果没有被本程序覆盖。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
