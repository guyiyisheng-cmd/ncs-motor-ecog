"""Analysis entry point. Writes only a NEW output directory, never source data."""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import json
import numpy as np
from . import __version__
from .core import MethodError
from .data import read_json, validate_config, load_subject, resolve_input
from .analysis import bootstrap_subject
from .auxiliary import quantify_native_cst, summarize_spatial
from .io import write_csv, write_json, sha256, environment


def run(config_path: Path, output: Path):
    config_path = config_path.resolve(strict=True)
    config = validate_config(read_json(config_path))
    basedir = config_path.parent
    output = output.resolve()
    if output.exists():
        raise MethodError("output exists; use a new directory to preserve earlier results")
    # Validate input contracts before creating a success-looking report.
    subjects = [load_subject(item, basedir, config) for item in config["subjects"]]
    ids = [s.subject for s in subjects]
    if len(set(ids)) != len(ids):
        raise MethodError("multiple records per subject need a declared additional level; do not count them as new patients")
    if len({s.dataset_kind for s in subjects}) != 1:
        raise MethodError("clinical and synthetic software-test data may not be mixed")
    if any(s.actions != subjects[0].actions for s in subjects):
        raise MethodError("actions/order differ between records; explicitly reconcile before equal-patient summaries")
    kind = subjects[0].dataset_kind
    output.mkdir(parents=True)
    (output / "PRIVATE_LOCAL").mkdir(mode=0o700)
    write_json(output / "RUN_STATUS.json", {"status": "RUNNING", "dataset_kind": kind})
    try:
        all_stats, all_channels, all_pairs, all_combined, infos = [], [], [], [], []
        inputs = [config_path]
        for s in subjects:
            print(f"Computing {s.subject}: {len(s.channels)} channels, {len(s.rounds)} rounds", flush=True)
            stats, channels, pairs, combined, draws, info = bootstrap_subject(s, config)
            all_stats.extend(stats); all_channels.extend(channels); all_pairs.extend(pairs); all_combined.extend(combined); infos.append(info)
            np.save(output / "PRIVATE_LOCAL" / (s.subject + "_bootstrap_indices.npy"), draws, allow_pickle=False)
            inputs.extend(s.input_paths)
        write_csv(output / "tables/channel_conditions.csv", all_channels)
        write_csv(output / "tables/channel_action_differences.csv", all_pairs)
        write_csv(output / "tables/combined_channel_conditions.csv", all_combined)
        write_csv(output / "tables/hierarchical_statistics.csv", all_stats)
        grouped = defaultdict(list)
        for row in all_stats:
            if row["category"] == "subject":
                key = tuple(row[k] for k in ("contrast", "beta_definition", "pac_grid", "metric"))
                grouped[key].append(row["estimate"])
        equal = []
        for key, values in sorted(grouped.items()):
            valid = np.isfinite(values)
            equal.append(dict(zip(["contrast", "beta_definition", "pac_grid", "metric"], key)) |
                         {"n_patients": len(subjects), "n_defined": int(valid.sum()),
                          "equal_patient_mean": float(np.mean(values)) if valid.all() else np.nan,
                          "inference": "descriptive_no_population_test"})
        write_csv(output / "tables/equal_patient_descriptions.csv", equal)
        structures = []
        for item in config.get("structure", []):
            path = resolve_input(item["arrays"], basedir)
            if item.get("native_geometry_reviewed") is not True or item.get("dataset_kind") != kind:
                raise MethodError("structure native geometry/source kind must be explicitly reviewed")
            structures.extend(quantify_native_cst(path, item["subject"]))
            inputs.append(path)
        write_csv(output / "tables/structure.csv", structures,
                  fieldnames=list(dict.fromkeys(k for r in structures for k in r)) or ["subject", "side", "volume_mm3"])
        write_json(output / "structure_status.json", {"status": "native_grid_description" if structures else "not_supplied",
                   "n_masks": len(structures), "note": "Native mask descriptions are not task-fMRI/ECoG validation."})
        spatial_path = resolve_input(config["spatial_pairs"], basedir) if config.get("spatial_pairs") else None
        spatial, spatial_status = summarize_spatial(spatial_path)
        if spatial_path:
            inputs.append(spatial_path)
        write_csv(output / "tables/spatial_descriptions.csv", spatial,
                  fieldnames=list(dict.fromkeys(k for r in spatial for k in r)) or ["subject", "record", "action", "contrast", "space_id", "n_locations", "rho_image_beta", "rho_image_pac"])
        write_json(output / "spatial_status.json", spatial_status)
        # Source paths are private. Public-run metadata contains tokens/digests only.
        entries = [{"input_token": f"INPUT_{i:04d}", "path": str(path), "sha256": sha256(path)} for i, path in enumerate(dict.fromkeys(inputs), 1)]
        write_json(output / "PRIVATE_LOCAL/input_paths.json", entries)
        write_json(output / "PRIVATE_LOCAL/executed_config.json", config)
        write_json(output / "run_manifest.json", {"package_version": __version__, "dataset_kind": kind,
                   "environment": environment(), "subjects": infos,
                   "numerical_code": {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
                   "inputs": [{k: e[k] for k in ("input_token", "sha256")} for e in entries],
                   "tables": {p.name: sha256(p) for p in sorted((output / "tables").glob("*.csv"))},
                   "method_reference": config["method_reference"],
                   "note": "Reproducing values does not alone establish method superiority or clinical validity."})
        (output / "RESULTS_CN.md").write_text(chinese_report(subjects, infos, equal, structures, spatial_status, kind), encoding="utf-8")
        write_json(output / "RUN_STATUS.json", {"status": "COMPLETED_DECLARED_NUMERICAL_SCOPE", "dataset_kind": kind,
                   "n_electrical_patients": len(subjects), "spatial_status": spatial_status["status"],
                   "raw_signal_preprocessing_run_by_this_command": False,
                   "full_manuscript_generated_by_this_command": False})
    except Exception as exc:
        write_json(output / "RUN_STATUS.json", {"status": "FAILED", "error_type": type(exc).__name__, "dataset_kind": kind})
        raise
    print("Completed declared numerical scope. Spatial availability is reported separately.", flush=True)
    return output


def chinese_report(subjects, infos, equal, structures, spatial_status, kind):
    label = "真实临床数组的本次计算" if kind == "clinical" else "软件测试专用合成数据（不是患者结果）"
    lines = ["# NCS：可复现计算结果", "", "数据性质：" + label, "",
             "本命令从已提供的有效数组重新计算；不声称重新完成了EDF滤波、BOLD建模或临床验证。", "",
             f"电生理：{len(subjects)}名患者/测试对象；{sum(len(s.channels) for s in subjects)}个通道；{sum(len(s.event_ids) for s in subjects)}个事件。",
             "保留原对数摘要与同尺度基线差两种明确的估计对象，不根据结果方向选择其一。",
             "不确定性为完整轮次同步重抽样的条件范围，不是患者总体置信区间。", "",
             "## 功率—PAC关系：患者等权描述", "",
             "|β定义|PAC网格|指标|有效患者|等权均值|", "|---|---|---|---:|---:|"]
    for row in equal:
        if row["contrast"] == "comparison_minus_reference" and row["metric"] in ("rho", "partial_rho"):
            val = row["equal_patient_mean"]
            text = f"{val:.6g}" if np.isfinite(val) else "不可估计/未提供"
            lines.append(f"|{row['beta_definition']}|{row['pac_grid']}|{row['metric']}|{row['n_defined']}|{text}|")
    lines += ["", "相关值、符号或条件范围不能单独证明独立机制、无关系或方法优效。全部动作结果在机器可读表中。", "",
              "## 影像", f"结构定量包含{len(structures)}侧掩膜。空间配对状态：{spatial_status['status']}；完整位置数：{spatial_status['n_complete_pairs']}。",
              "缺少空间数据不记为影像相关系数0，也不通过CST侧差代替任务空间配对。", "",
              "## 本版交付", "tables/：通道条件、动作差值、分层统计、等权描述、结构及真实空间配对（有资料时）。",
              "PRIVATE_LOCAL/：输入路径、完整配置和实际重抽样索引，仅本地。",
              "run_manifest.json：数值来源摘要；不能单凭此文件公开未获许可的数据。", "",
              "这份自动报告不是全要素投稿稿；中文主文和补充材料由本地Codex用实际结果与既有方法记录同步完成。", ""]
    return "\n".join(lines)
