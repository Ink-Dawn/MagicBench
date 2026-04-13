# MagicBench

*Accepted at ACL.*

MagicBench is a benchmark for diagnosing visual agency loss and semantic dependency in multimodal LLMs through magic videos. The project studies whether current models truly reason over visual evidence, or whether they over-rely on spoken language even when that language is deceptive.

![MagicBench intervention figure](docs/assets/figures/figure4_final.png)

## Quick Links

- [Paper PDF](docs/assets/paper/final.pdf)
- [Dataset Download (Baidu Netdisk)](https://pan.baidu.com/s/13veWd4WVU0rN8vpkmnbfiw?pwd=y36t)
- [Project Homepage Source](docs/index.html)
- [Supplementary Evaluation Code](MagicBench_Supplementary/evaluation_code)
- [License](LICENSE)

## Overview

MagicBench turns magic videos into semantically adversarial multimodal reasoning tasks. Each clip pairs visual evidence with one of four linguistic conditions:

- `Type A`: direct lie
- `Type B`: misdirection
- `Type C`: patter
- `Type D`: no audio

We evaluate whether a model can recover the physical mechanism behind the illusion instead of repeating the magician's false narrative. The benchmark uses three main axes:

- `VTG`: visual-temporal grounding
- `CPA`: causal-physical accuracy
- `CFR`: counterfactual resilience

## Main Findings

1. Deceptive language can still act as a spotlight. On deceptive clips, multimodal skeptical prompting remains competitive with or slightly above vision-only on average causal reasoning:

| Model | Deceptive Avg CPA: Multimodal | Deceptive Avg CPA: Vision-Only |
| --- | ---: | ---: |
| GPT-4o | 37.45 | 34.03 |
| Gemini-2.5 | 48.26 | 47.12 |
| Qwen2.5-VL | 33.79 | 32.83 |

2. The same models collapse when audio disappears. On `Type D` clips, removing audio consistently improves causal reasoning:

| Model | Type D CPA: Multimodal | Type D CPA: Vision-Only |
| --- | ---: | ---: |
| GPT-4o | 10.37 | 28.15 |
| Gemini-2.5 | 39.63 | 50.74 |
| Qwen2.5-VL | 6.15 | 30.62 |

3. This pattern supports the paper's central diagnosis:

- `Spotlight effect`: language can anchor attention to relevant entities even when the narration is false.
- `Crutch effect`: once language disappears, visual agency degrades sharply in multimodal setups.
- `Causal intervention`: manually restoring attention with visual prompts helps recover correct reasoning.

## Dataset Snapshot

- `302` annotated magic clips in total
- Linguistic split: `146` direct lies, `37` misdirection clips, `91` patter clips, `28` no-audio clips
- Difficulty split: `96` beginner, `127` basic, `71` intermediate, `8` advanced
- Frequent challenge types include `Fast Motion`, `Occlusion`, `Tiny Object`, `Logic Puzzle`, and `Physics Defy`

## Dataset Files

The shared archive contains multiple JSON variants. The most useful ones are:

- `magic_bench_dataset_with_timestamps.json`: the original `302`-clip release with `transcript`, `audio_timeline`, `visual_timeline`, and legacy `linguistic_type`
- `magic_bench_dataset_pro.json`: the expanded JSON file used for later extension experiments
- `magic_bench_dataset_with_timestamps_full.json`: generated locally after adding timestamps to the newly added clips
- `magic_bench_dataset_linguistic_balanced.json`: generated locally after assigning `linguistic_type` to the new clips while freezing old labels

If you only want to evaluate models on the released benchmark, you usually only need:

- the dataset archive from Baidu Netdisk
- the JSON file you want to evaluate
- the extracted frame folders
- `MagicBench_Supplementary/evaluation_code/run_experiment.py`
- `MagicBench_Supplementary/evaluation_code/auto_judge.py`

You do not need to run `merge_transcripts_with_timestamps.py` or `annotate_linguistics.py` unless you are extending MagicBench with new videos.

## Key Figures

### Performance Across Linguistic Types

![Performance comparison](docs/assets/figures/performance_comparison_bar.png)

### Robustness Trend From Type A to Type D

![Robustness trend](docs/assets/figures/robustness_trend_line.png)

## Repository Structure

```text
.
|- docs/                              # GitHub Pages homepage and public assets
|- MagicBench_Supplementary/          # Supplementary release materials
|- final_clips_dataset/               # Local video assets (do not push directly to GitHub)
|- merge_transcripts_with_timestamps.py # Add audio timestamps to newly added clips
|- results/                           # Model outputs and judged results
|- roi_results/                       # ROI annotation assets for intervention analysis
|- annotate_linguistics.py            # Linguistic type annotation and balancing pipeline
|- auto_cut.py                        # Scene splitting and clip preparation
|- figure.py / figure3.py             # Public plotting scripts
|- magic_bench_dataset*.json          # Dataset JSON files
|- *_overall_stats.json               # Aggregated benchmark statistics
```

## Public Code Scope

This repository is intentionally filtered for public release. Only the core scripts are intended to be committed:

- `annotate_linguistics.py`
- `auto_cut.py`
- `figure.py`
- `figure3.py`
- `ROI.py`
- `sampling.py`
- `MagicBench_Supplementary/evaluation_code/*.py`

Most local helper scripts, debugging files, and one-off tooling are excluded through `.gitignore`.

## Public Release Advice

If you plan to publish this project on GitHub, keep the repository lightweight and put large assets elsewhere:

- Keep on GitHub: `README.md`, `docs/`, aggregated `.json` results, figures, cleaned scripts, supplementary code
- Host externally: raw videos, extracted frames, checkpoints, wheels, offline packages
- Recommended external storage: Hugging Face dataset repo, GitHub Releases, Google Drive, or institutional storage

This repository already includes a GitHub Pages homepage under [`docs/`](docs). After pushing to GitHub, enable Pages with the `main` branch and `/docs` folder.

## How To Use MagicBench

### 1. Download the dataset

Download the full MagicBench package from Baidu Netdisk:

- Link: [https://pan.baidu.com/s/13veWd4WVU0rN8vpkmnbfiw?pwd=y36t](https://pan.baidu.com/s/13veWd4WVU0rN8vpkmnbfiw?pwd=y36t)
- Extraction code: `y36t`

The safest choice is to keep the extracted folder structure unchanged. A recommended local layout is:

```text
MagicBench/
|- MagicBench_Supplementary/
|- docs/
|- frames/
|  |- final_clips_dataset/
|- final_clips_dataset/
|- magic_bench_dataset_with_timestamps.json
|- magic_bench_dataset_pro.json
|- README.md
```

If you extract the data to a different location, you must update the path variables listed below.

### 2. Install dependencies

For the public evaluation code:

```bash
pip install -r MagicBench_Supplementary/evaluation_code/requirements.txt
```

If you want to extend the dataset with new clips and regenerate timestamps, also install:

```bash
pip install openai-whisper torch tqdm
```

If you use `merge_transcripts_with_timestamps.py`, make sure `ffmpeg` is installed and accessible on your machine.

### 3. Fill in your API key

There are two different configuration styles in this repository.

For [`annotate_linguistics.py`](annotate_linguistics.py), the script reads environment variables:

- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`

PowerShell example:

```powershell
$env:OPENROUTER_API_KEY="your_openrouter_key"
$env:OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
python annotate_linguistics.py
```

The file [`.env.example`](.env.example) shows the variable names, but the script does not automatically load `.env`. You still need to set the environment variables in your shell or runtime environment.

For the public evaluation scripts, fill the key directly in the file header:

- [`MagicBench_Supplementary/evaluation_code/run_experiment.py`](MagicBench_Supplementary/evaluation_code/run_experiment.py): set `API_KEY = ""`
- [`MagicBench_Supplementary/evaluation_code/auto_judge.py`](MagicBench_Supplementary/evaluation_code/auto_judge.py): set `API_KEY = ""`

In both files, you can usually keep:

```python
BASE_URL = "https://openrouter.ai/api/v1"
```

unless you are using a different provider endpoint.

### 4. Replace the local paths

The following variables usually need to be edited before running the scripts:

| File | Variables to edit | What they should point to |
| --- | --- | --- |
| `merge_transcripts_with_timestamps.py` | `FFMPEG_DIR`, `INPUT_JSON`, `BASE_JSON`, `OUTPUT_JSON`, `MODEL_PATH` | Your local `ffmpeg` directory, the expanded dataset JSON, the old timestamped JSON, the output JSON, and your Whisper checkpoint |
| `MagicBench_Supplementary/evaluation_code/run_experiment.py` | `INPUT_JSON`, `FRAMES_ROOT`, `OUTPUT_DIR` | The JSON you want to evaluate, the extracted frame root, and the directory for saving model outputs |
| `MagicBench_Supplementary/evaluation_code/auto_judge.py` | `INPUT_FILES` | A list of result JSON files produced by `run_experiment.py` |
| `ROI.py` | `INPUT_IMAGE_DIR` | The local directory containing images for ROI annotation |
| `sampling.py` | hardcoded result JSON paths near the top of the file | The result files you want to sample from |

Recommended values for the evaluation pipeline:

- In [`MagicBench_Supplementary/evaluation_code/run_experiment.py`](MagicBench_Supplementary/evaluation_code/run_experiment.py), set `INPUT_JSON` to a dataset JSON such as `magic_bench_dataset_with_timestamps.json`
- Set `FRAMES_ROOT` to the directory that contains the extracted frame subfolders, for example `D:\\MagicBench\\frames\\final_clips_dataset`
- `OUTPUT_DIR` can usually stay as `results`

Example:

```python
API_KEY = "your_openrouter_key"
INPUT_JSON = r"D:\MagicBench\magic_bench_dataset_with_timestamps.json"
FRAMES_ROOT = r"D:\MagicBench\frames\final_clips_dataset"
OUTPUT_DIR = "results"
```

For [`MagicBench_Supplementary/evaluation_code/auto_judge.py`](MagicBench_Supplementary/evaluation_code/auto_judge.py), add the generated result files to `INPUT_FILES`, for example:

```python
INPUT_FILES = [
    r"results/gemini-2.5-flash_multimodal_Forensic_v4.json",
    r"results/gpt-4o_multimodal_Forensic_v4.json",
    r"results/qwen-2.5-vl_multimodal_Forensic_v4.json",
]
```

### 5. Run the benchmark

Run model inference first:

```bash
python MagicBench_Supplementary/evaluation_code/run_experiment.py
```

This writes result files such as:

- `results/gemini-2.5-flash_multimodal_Forensic_v4.json`
- `results/gpt-4o_multimodal_Forensic_v4.json`
- `results/qwen-2.5-vl_multimodal_Forensic_v4.json`

Then run the automatic judge:

```bash
python MagicBench_Supplementary/evaluation_code/auto_judge.py
```

This writes judged files with the suffix `_judged_v2.json`.

### 6. Extend the dataset with new clips

If you add new videos and want to regenerate timestamps and linguistic labels, use the following order:

1. Run [`merge_transcripts_with_timestamps.py`](merge_transcripts_with_timestamps.py) to append `audio_timeline` and `transcript` for the new items.
2. Run [`annotate_linguistics.py`](annotate_linguistics.py) to classify the new clips and rebalance `linguistic_type`.

`annotate_linguistics.py` assumes:

- `magic_bench_dataset_with_timestamps.json` is the frozen legacy base file
- `magic_bench_dataset_with_timestamps_full.json` is the merged full dataset containing the new items

Outputs generated by that script:

- `magic_bench_dataset_linguistic_balanced.json`
- `linguistic_type_cache.json`
- `linguistic_type_balance_report.json`

## Reproducibility Notes

Use environment variables whenever possible instead of committing secrets into scripts:

```bash
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Public supplementary code with sanitized configuration lives in [`MagicBench_Supplementary/evaluation_code`](MagicBench_Supplementary/evaluation_code).

## Citation

```bibtex
@inproceedings{anonymous2026magicbench,
  title={MagicBench: Diagnosing Visual Agency Loss and Semantic Dependency in Multimodal {LLM}s},
  author={Anonymous},
  booktitle={The 64th Annual Meeting of the Association for Computational Linguistics},
  year={2026},
  url={https://openreview.net/forum?id=JeJEgZoXPm}
}
```

## License

This project is released under the terms of the [MIT License](LICENSE).
