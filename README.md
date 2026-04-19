# MagicBench

*Accepted at ACL 2026.*

MagicBench is a diagnostic benchmark for evaluating visual agency loss and semantic dependency in multimodal LLMs. Using magic tricks as semantically adversarial tasks, it investigates whether models genuinely reason over visual evidence or merely over-rely on deceptive spoken language.

![MagicBench Intervention](docs/assets/figures/figure4_final.png)

## Quick Links

- [Paper (OpenReview)](https://openreview.net/forum?id=JeJEgZoXPm)
-[Dataset Download (Baidu Netdisk)](https://pan.baidu.com/s/13veWd4WVU0rN8vpkmnbfiw?pwd=y36t) *(Extraction code: `y36t`)*
- [Project Homepage](docs/index.html)
- [License](LICENSE)

## Main Findings

MagicBench pairs visual evidence with four linguistic conditions: `Type A` (Direct Lie), `Type B` (Misdirection), `Type C` (Patter), and `Type D` (Silence/No Audio). We evaluate models across Visual-Temporal Grounding (VTG), Causal-Physical Accuracy (CPA), and Counterfactual Resilience (CFR).

1. **The Spotlight Effect:** Deceptive language still acts as an attentional spotlight. Under deceptive prompts, multimodal models often perform comparably to or slightly better than their vision-only counterparts.
2. **The Crutch Effect (Visual Agency Loss):** When audio is completely removed (`Type D`), multimodal performance collapses, whereas vision-only probes maintain robust causal reasoning.

| Model | Deceptive Avg CPA (Multi) | Deceptive Avg CPA (Vision) | Type D CPA (Multi) | Type D CPA (Vision) |
| :--- | :---: | :---: | :---: | :---: |
| **GPT-4o** | 37.45 | 34.03 | **10.37** | 28.15 |
| **Gemini-2.5-Pro** | 48.26 | 47.12 | **39.63** | 50.74 |
| **Qwen2.5-VL-72B** | 33.79 | 32.83 | **6.15** | 30.62 |

*Conclusion:* Current early-fusion MLLMs behave more like *language-guided observers* than autonomous visual reasoners.

## Dataset Snapshot

- **Size:** 302 annotated high-fidelity magic clips.
- **Linguistic Split:** 146 Direct Lies, 37 Misdirections, 91 Patters, 28 Silence.
- **Difficulty:** 96 Beginner, 127 Basic, 71 Intermediate, 8 Advanced.
- **Challenges:** Fast Motion, Occlusion, Tiny Objects, Logic Puzzles, Physics Defiance.

## Repository Structure

```text
.
├── docs/                                  # GitHub Pages assets
├── final_clips_dataset/                   # Local video assets (Download externally)
├── MagicBench_Supplementary/              # Evaluation and auto-judging code
│   └── evaluation_code/
├── magic_bench_dataset_with_timestamps.json # Primary dataset file
├── magic_bench_dataset_pro.json           # Expanded dataset (for extension experiments)
├── results/                               # Output directory for model inferences
└── *.py                                   # Helper scripts for dataset extension & visualization
```

## Getting Started

### 1. Download the Dataset
Download the full dataset from [Baidu Netdisk](https://pan.baidu.com/s/13veWd4WVU0rN8vpkmnbfiw?pwd=y36t) (Code: `y36t`) and extract it. We recommend placing the extracted `frames/` and `final_clips_dataset/` directories directly in the project root.

### 2. Install Dependencies
```bash
pip install -r MagicBench_Supplementary/evaluation_code/requirements.txt
```
*(Optional)* If you plan to extend the dataset using our video processing scripts, also install: `pip install openai-whisper torch tqdm` and ensure `ffmpeg` is installed.

### 3. Configuration
Set up your OpenRouter API keys and update the local paths in the core evaluation scripts:

- **For Evaluation** (`MagicBench_Supplementary/evaluation_code/run_experiment.py`):
  Update `API_KEY`, `INPUT_JSON` (point to `magic_bench_dataset_with_timestamps.json`), and `FRAMES_ROOT` (point to your extracted frames directory).
  
- **For Judging** (`MagicBench_Supplementary/evaluation_code/auto_judge.py`):
  Update `API_KEY` and ensure `INPUT_FILES` points to your generated result JSONs.

- **For Dataset Extension** (`annotate_linguistics.py`):
  Set your environment variables before running:
  ```bash
  export OPENROUTER_API_KEY="your_openrouter_key"
  export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
  ```

### 4. Run the Benchmark
Step 1: Run model inference.
```bash
python MagicBench_Supplementary/evaluation_code/run_experiment.py
```
Step 2: Run the LLM-as-a-judge protocol to grade the predictions.
```bash
python MagicBench_Supplementary/evaluation_code/auto_judge.py
```

## Citation

```bibtex
@inproceedings{
  anonymous2026magicbench,
  title={MagicBench: Diagnosing Visual Agency Loss and Semantic Dependency in Multimodal {LLM}s},
  author={Anonymous},
  booktitle={The 64th Annual Meeting of the Association for Computational Linguistics},
  year={2026},
  url={https://openreview.net/forum?id=JeJEgZoXPm}
}
```

## License
This project is released under the [MIT License](LICENSE).


