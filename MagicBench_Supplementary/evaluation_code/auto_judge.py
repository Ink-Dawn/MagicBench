import json
import os
import argparse
from tqdm import tqdm
from openai import OpenAI


API_KEY = ""
BASE_URL = "https://openrouter.ai/api/v1"
REFERER = "https://github.com/MagicBench"

JUDGE_MODEL = "openai/gpt-4o"


INPUT_FILES = [
    
]


client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    default_headers={"HTTP-Referer": REFERER, "X-Title": "MagicBench Judge"},
)

JUDGE_SYSTEM_PROMPT = """
You are a strict scientific auditor evaluating AI reasoning on MagicBench.
You are provided with a **Physical Constraint Set (PCS)** (derived from the Ground Truth tutorial) and the **Model Prediction**.

**Your Goal:** Check if the prediction **satisfies the physical constraints**, NOT if it matches the text word-for-word.

**Evaluation Protocol:**
Evaluate on three dimensions using an **integer scale from 0 to 10**.
Before scoring, perform the **Hard Failure Check**.

**Step 1: Constraint Violation Check (The Veto Phase - Hard Failures)**
If any VIOLATION is found, the **CPA score is AUTOMATICALLY 0**, regardless of other merits:
1.  **Prop Hallucination (Observability Rule):** The model hypothesizes a prop (Magnet, Thread, Mirror) whose **Required Observable Signal** is ABSENT in the PCS description.
    *   *Magnet requires:* Unnatural attraction/sticking.
    *   *Thread requires:* Tension/suspension.
    *   *Mirror requires:* Reflection/Visual discontinuity.
    *   *If PCS says "Sleight of Hand", proposing these props is a strict violation.*
2.  **State Checkpoint Violation:** The model claims an object is in Location A at a critical moment, but PCS mandates Location B (e.g., claiming coin is in Left Hand when PCS says Right Hand).
3.  **Magical Thinking:** The model accepts the illusion as reality (e.g., "it actually melted", "it teleported") without a physical explanation.

**Step 2: Scoring Dimensions (0–10 integer scale)**

**1. Visual-Temporal Grounding (VTG)**
*   **7–10 (Precise):** Correctly identifies:
    *   The **Body Part/Location** involved.
    *   The **Specific Action** (e.g., transfer, reach, close, open).
    *   **Temporal Ordering:** Correctly sequences the events (e.g., "Action A happens before Reveal B").
*   **4–6 (Partial):** Identifies Body Part but is vague on Action or Timing. Or identifies the moment but gets the location wrong.
*   **0–3 (Fail):** Wrong location, hallucinates visual events, or completely vague ("something happened").

**2. Causal-Physical Accuracy (CPA)** (Subject to Hard Failure Veto)
*   **7–10 (Entailed):** The explanation is **Physically Entailed** by the PCS. (i.e., The mechanism described successfully achieves the effect without violating any PCS rules).
    *   *NOTE:* **Terminology Agnostic.** If the model describes the correct physical action (e.g., "False Take") without using the specific term (e.g., "French Drop"), give it **7–10**.
*   **4–6 (Plausible):** Identifies the general category (e.g., "Sleight of Hand") but misses a key mechanical step or is slightly inaccurate.
*   **0–3 (Fail):** Hard Failure triggered OR explains a completely wrong mechanism.

**3. Counterfactual Resilience (CFR)**
*   **7–10 (Resilient):** The model successfully resists the false narrative. This is achieved if:
    *   **Scenario A (Explicit Rejection):** It explicitly refutes the audio claim (e.g., "The magician claims it vanished, but it is actually hidden").
    *   **Scenario B (Implicit Immunity):** It provides a correct physical explanation that logically contradicts the lie, **WITHOUT** repeating the lie as fact. (e.g., Simply stating "The coin is palmed" counts as Resilient).
*   **4–6 (Skeptical):** Expresses doubt ("This is unlikely", "Misdirection used") but fails to provide the definite physical alternative.
*   **0–3 (Fooled):** Accepts the illusion/lie as fact (e.g., "The coin vanished into thin air") or invents props to justify the lie.

**Output strictly in JSON format:**
{
  "scores": { "VTG": 0, "CPA": 0, "CFR": 0 },
  "hard_failure_triggered": true, // or false
  "failure_reason": "None" or description of violation...,
  "reasoning": "Explain score based on constraint satisfaction..."
}
"""

JUDGE_USER_PROMPT_TEMPLATE = """
**Physical Constraint Set (PCS / Ground Truth):**
{pcs}

**Model Prediction:**
{prediction}

**Task:** Perform the strict audit and scoring.
"""


def call_judge_api(pcs, prediction):
    user_content = JUDGE_USER_PROMPT_TEMPLATE.format(pcs=pcs, prediction=prediction)
    try:
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f" Judge Error: {e}")
        return None


def process_single_file(input_path):
    output_path = input_path.replace(".json", "_judged_v2.json")
    file_name = os.path.basename(input_path)
    print(f"\n--- 正在处理: {file_name} ---")

    with open(input_path, "r", encoding="utf-8") as f:
        results_data = json.load(f)

    processed_map = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                for item in existing_data:
                    if item.get("judge_result"):
                        processed_map[item["id"]] = item
        except:
            print(f" {file_name} 的输出文件损坏，将重新打分")

    judged_results = []
    to_process = []

    for item in results_data:
        if item["id"] in processed_map:
            judged_results.append(processed_map[item["id"]])
        else:
            to_process.append(item)

    if processed_map:
        print(
            f" 已恢复 {len(processed_map)} 条记录，剩余 {len(to_process)} 条待处理..."
        )
    else:
        print(f" 开始全新打分，共 {len(to_process)} 条数据")

    if to_process:
        for item in tqdm(to_process, desc=f"Judging {file_name[:15]}..."):
            gt_text = item.get("PCS_source", "")
            if not gt_text and "ground_truth" in item:
                gt_text = item["ground_truth"].get("principle", "")

            model_pred = item.get("model_output", "")
            if isinstance(model_pred, dict):
                model_pred = json.dumps(model_pred, ensure_ascii=False)

            if not gt_text or not model_pred:
                item["judge_result"] = None
                judged_results.append(item)
                continue

            judge_output = None
            for _ in range(3):
                judge_output = call_judge_api(gt_text, model_pred)
                if judge_output:
                    break

            item["judge_result"] = judge_output
            judged_results.append(item)

            if len(judged_results) % 5 == 0:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(judged_results, f, ensure_ascii=False, indent=4)
    else:
        print(f" {file_name} 已经全部处理完毕，跳过。")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(judged_results, f, ensure_ascii=False, indent=4)


    print_stats(judged_results, file_name)


def print_stats(judged_results, file_name):
    valid_results = [i for i in judged_results if i.get("judge_result")]
    total = len(valid_results)
    if total == 0:
        print(f" {file_name}: 无有效打分数据")
        return

    vtg_sum = sum([i["judge_result"]["scores"]["VTG"] for i in valid_results])
    cpa_sum = sum([i["judge_result"]["scores"]["CPA"] for i in valid_results])
    cfr_sum = sum([i["judge_result"]["scores"]["CFR"] for i in valid_results])

    print("-" * 30)
    print(f" 文件统计: {file_name} (N={total})")
    print(f" VTG (Visual): {vtg_sum/total*10:.2f}%")
    print(f" CPA (Physical): {cpa_sum/total*10:.2f}%")
    print(f" CFR (Resilience): {cfr_sum/total*10:.2f}%")
    print("-" * 30)


def main():
    print(f" 启动多文件裁判系统")

    for input_file_path in INPUT_FILES:
        process_single_file(input_file_path)

    print("\n 所有文件打分任务已完成！")


if __name__ == "__main__":
    main()


