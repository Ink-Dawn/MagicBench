import os
import json
import base64
import time
import random
from tqdm import tqdm
from openai import OpenAI

# ==========================================
#  配置区域 (Configuration)
# ==========================================

# 你的 OpenRouter API Key
OPENROUTER_API_KEY = ""  #  请记得填入你的 Key

# 你的本地路径配置 (自动处理 Windows 反斜杠)
PROJECT_ROOT = r"D:\visual_studio_code\VScode_Project\魔术视频"
DATASET_JSON_PATH = os.path.join(PROJECT_ROOT, r"frames\magic_bench_dataset_pro.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, r"frames\experiment_results_vision_only_no_caption.json")

# 模型配置
MODEL_NAME = "openai/gpt-4o-2024-08-06"
EXPERIMENT_ID = "Exp2.1_Group2_Vision_Skeptic"

#  限制最大帧数，防止 Context Window 爆炸或超时 (建议 50-60)
MAX_FRAMES = 50

# ==========================================
#  Prompts 定义
# ==========================================

VISION_ONLY_SYSTEM_PROMPT = """
You are a world-class Magic Analyst specializing in visual forensic analysis.

Your task is to deconstruct magic tricks using ONLY visual evidence from video frames.

**Core Principles:**
1. **Vision-Only Constraint:** You must rely strictly on what is visually observable. Assume no access to audio, narration, or spoken explanation.
2. **Skepticism:** Do NOT believe the illusion. Every effect is caused by physical actions, sleight of hand, or hidden objects.
3. **Evidence-Based Reasoning:** Identify suspicious hand positions, object trajectories, body posture, occlusions, or timing inconsistencies.
4. **Physics over Jargon:** If you do not know a professional magic term, describe the physical action precisely.
5. **Temporal Precision:** You MUST cite visual timestamps (e.g., "[Image 12 @ 2.4s]") to support every key claim.
"""

VISION_ONLY_USER_PROMPT_TEMPLATE = """
**Visual Input (Video Frames with Timestamps):**

{visual_context}

**Task:**
Analyze the magic trick using ONLY the visual evidence provided above.

Focus on:
- hand movements
- object visibility
- timing
- occlusion
- attentional and visual misdirection

Do NOT assume any spoken explanation or narration.

**Output strictly in JSON format with the following keys:**
{{
  "effect_description": "Briefly describe what the audience visually perceives (the illusion).",
  "visual_anomalies": "List specific suspicious visual details. MUST cite TIMESTAMPS.",
  "misdirection_analysis": "Explain how visual attention is manipulated (e.g., gestures, gaze, timing, occlusion).",
  "step_by_step_deduction": "Trace the object's location over time using only visual evidence.",
  "final_principle": "The core physical method behind the illusion.",
  "confidence_score": 1 (Guessing) to 5 (Certain)
}}
"""

# ==========================================
# 辅助函数
# ==========================================


def encode_image(image_path):
    """将图片文件编码为 Base64 字符串"""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def construct_messages(entry):
    """构建发送给 API 的消息体 (多模态)"""
    visual_context_text = ""
    content_payload = []

    timeline = entry.get("visual_timeline", [])

    #  下采样策略：如果帧数超过 MAX_FRAMES，均匀抽取
    if len(timeline) > MAX_FRAMES:
        step = len(timeline) / MAX_FRAMES
        indices = [int(i * step) for i in range(MAX_FRAMES)]
        selected_items = [timeline[i] for i in indices]
    else:
        selected_items = timeline

    valid_frames = 0

    for item in selected_items:
        frame_idx = item["frame_idx"]
        timestamp = item["timestamp"]
        filename = item["filename"]

        # 路径拼接修正：使用 normpath 处理 Windows 路径
        rel_path = entry["frames_folder"]
        img_abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, rel_path, filename))

        base64_image = encode_image(img_abs_path)

        if base64_image:
            valid_frames += 1
            content_payload.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "low",
                    },
                }
            )
            visual_context_text += f"- [Image {frame_idx} @ {timestamp}s]\n"
        else:
            # 仅在调试时开启，避免刷屏
            pass

    formatted_user_prompt = VISION_ONLY_USER_PROMPT_TEMPLATE.format(
        visual_context=visual_context_text
    )

    content_payload.append({"type": "text", "text": formatted_user_prompt})

    messages = [
        {"role": "system", "content": VISION_ONLY_SYSTEM_PROMPT},
        {"role": "user", "content": content_payload},
    ]

    return messages, valid_frames


# ==========================================
#  主程序
# ==========================================


def main():
    # 初始化 OpenAI Client
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    print(f" Loading dataset from: {DATASET_JSON_PATH}")

    if not os.path.exists(DATASET_JSON_PATH):
        print(f" Critical Error: Dataset file not found at {DATASET_JSON_PATH}")
        return

    try:
        with open(DATASET_JSON_PATH, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except Exception as e:
        print(f" JSON Load Error: {e}")
        return

    print(f" Total videos to process: {len(dataset)}")

    # 读取断点
    results = []
    processed_ids = set()
    if os.path.exists(OUTPUT_FILE):
        print(" Found existing results, loading for resume...")
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
            processed_ids = {r["id"] for r in results}
            print(f" Skipping {len(processed_ids)} already processed videos.")
        except:
            print(" Could not read existing file, starting fresh.")

    # 遍历数据集
    for entry in tqdm(dataset, desc="Processing Videos"):
        video_id = entry["id"]

        if video_id in processed_ids:
            continue

        try:
            messages, frame_count = construct_messages(entry)

            if frame_count == 0:
                print(f" No frames found for {video_id}, skipping.")
                continue

            # API 调用
            start_time = time.time()
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=1000,
                    timeout=120,  # 设置超时
                )
            except Exception as api_err:
                print(f"\n API Request Error for {video_id}: {api_err}")
                continue

            duration = time.time() - start_time

            #  鲁棒的响应解析 (修复 'NoneType' object is not subscriptable)
            raw_content = ""
            try:
                # 尝试对象访问 (v1.0+)
                if hasattr(response, "choices"):
                    raw_content = response.choices[0].message.content
                # 尝试字典访问 (旧版本兼容)
                elif isinstance(response, dict):
                    raw_content = response["choices"][0]["message"]["content"]
                else:
                    print(f"\n Unknown response type: {type(response)}")
                    print(response)  # 打印出来看看是什么
                    continue
            except Exception as parse_err:
                print(f"\n Response Parsing Error for {video_id}: {parse_err}")
                # 打印 response 结构以便调试
                print(f"DEBUG Response: {response}")
                continue

            if not raw_content:
                print(f"\n Empty content received for {video_id}")
                continue

            # 解析 JSON
            try:
                parsed_json = json.loads(raw_content)
            except json.JSONDecodeError:
                parsed_json = {"raw_output": raw_content, "error": "JSON parse failed"}

            # 保存结果
            result_entry = {
                "id": video_id,
                "video_filename": entry.get("video_filename", "unknown"),
                "experiment_id": EXPERIMENT_ID,
                "ground_truth_pcs": entry.get("ground_truth", {}),
                "model_prediction": parsed_json,
                "meta": {
                    "frames_analyzed": frame_count,
                    "inference_time": round(duration, 2),
                    "model": MODEL_NAME,
                },
            }

            results.append(result_entry)

            # 实时保存
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"\n General Error processing {video_id}: {str(e)}")
            import traceback

            traceback.print_exc()

    print(f"\n Experiment completed! Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
