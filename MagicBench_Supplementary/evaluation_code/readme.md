# MagicBench: Supplementary Materials (Anonymous)

## Overview
This package contains sample data and core evaluation scripts for **MagicBench**, a diagnostic benchmark for Multimodal LLMs under semantic adversarial scenarios.

**Note:** Due to the large size of the full video dataset and copyright considerations, we provide **representative samples** and **core logic scripts** here for review purposes. The full dataset and codebase will be publicly released upon acceptance.

## 1. Dataset Structure (`dataset_samples/`)
We provide samples representing different linguistic interference types (Type A: Lie, Type B: Misdirection, Type D: Silence).

Each entry in `samples.json` contains:
- `id`: Unique identifier.
- `visual_timeline`: Keyframes with timestamps (simulating the video input).
- `transcript`: The audio narrative (contains lies or silence).
- `ground_truth`: The Physical Constraint Set (PCS) derived from human annotation.
- `linguistic_type`: The interference category.

## 2. Evaluation Logic (`evaluation_code/`)
- `prompts.py`: Contains the system prompts for Vision-Only and Multimodal settings.
- `calc_metrics.py`: Demonstrates the logic for calculating **CPA** (Causal-Physical Accuracy) and **VTG** (Visual-Temporal Grounding) based on the judge's output.

## 3. Reproduction
The full benchmark relies on OpenAI/Google APIs. The provided scripts demonstrate the **data processing flow** and **scoring mechanism** without requiring API keys.