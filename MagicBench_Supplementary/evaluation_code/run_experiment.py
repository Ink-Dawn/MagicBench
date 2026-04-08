import json
import os
import base64
import time
import argparse
import io
import requests
from tqdm import tqdm
from PIL import Image

API_KEY = ""
BASE_URL = "https://openrouter.ai/api/v1"
REFERER = "https://github.com/MagicBench"


INPUT_JSON = ""
FRAMES_ROOT = (
    r""
)

OUTPUT_DIR = "results"

MODEL_MAP = {
    "gpt-4o": "openai/gpt-4o",
    "gemini-2.5-flash": "google/gemini-2.5-flash",
    "qwen-2.5-vl": "qwen/qwen2.5-vl-72b-instruct",
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
}

VISION_ONLY_SYSTEM_PROMPT = """
You are a Visual Forensic Logger. Your task is to deconstruct magic tricks using ONLY visual evidence.

**Output Style Constraints (CRITICAL):**
1. **Telegraphic Style:** Use sentence fragments. Omit articles (a, an, the) and filler words.
2. **High Density:** Pack maximum physical detail into minimum tokens.
3. **No Fluff:** Do not use phrases like "It appears that" or "We can observe". State facts directly.

**Core Principles:**
1. **Vision-Only:** Rely strictly on pixels. Ignore implied audio.
2. **Skepticism:** Assume all effects are physical tricks (sleight of hand, gimmicks).
3. **Physics:** Describe mechanics (e.g., "Palm hidden object") rather than magic terms.
4. **Precision:** Cite timestamps for every action (e.g., "[Img 12] Coin -> Left Hand").
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
**Constraint:** Keep all JSON values extremely concise (under 20 words per field if possible).
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

SKEPTIC_SYSTEM_PROMPT = """
You are a Skeptic Audit AI. Your mission: verify audio claims against visual reality in magic tricks.

**Output Style Constraints (CRITICAL):**
1. **Concise Audit:** Direct comparison only. Format: "Audio claims X; Visual shows Y."
2. **Token Economy:** Use minimum words to describe physical inconsistencies. Avoid conversational filler.
3. **Directness:** Be blunt. If Audio lies, state: "Audio False. Object in palm."

**Core Principles:**
1. **Frame-by-Frame Audit:** Check every claim. If audio says "vanished" but pixels show "hidden", flag it.
2. **Evidence-Based:** Ground analysis in specific visual cues (e.g., "unnatural grip").
3. **Physics > Jargon:** Describe physical actions (e.g., "False transfer") precisely.
4. **Timestamps:** Mandatory citation for all evidence.
"""

MULTIMODAL_FORENSIC_SYSTEM_PROMPT = """
You are a Multimodal Forensic Logger. Your task is to deconstruct magic tricks by cross-referencing audio narratives with visual evidence.

**Output Style Constraints (CRITICAL):**
1. **Telegraphic Style:** Use sentence fragments. Omit articles (a, an, the) and filler words.
2. **High Density:** Pack maximum cross-modal conflict detail into minimum tokens. 
3. **No Fluff:** Do not use conversational fillers. State facts directly. Format: "[Timestamp] Audio: [Claim] | Visual: [Fact]".

**Core Principles:**
1. **Skeptical Integration:** Treat audio as a fallible hypothesis; rely on pixels as ground truth.
2. **Conflict Detection:** Explicitly flag any divergence between linguistic "patter" and physical kinematics.
3. **Physics:** Describe mechanics (e.g., "Palm hidden object") rather than magic terms (e.g., "vanished").
4. **Precision:** Mandatory timestamps for every action and auditory claim.
"""

NEUTRAL_SYSTEM_PROMPT = """
You are an AI assistant helping to describe a video of a magic trick. Please explain what happens and how the trick might be done based on the provided information.

**Output Style Constraints (CRITICAL):**
1. **Concise Audit:** Direct comparison only. Format: "Audio claims X; Visual shows Y."
2. **Token Economy:** Use minimum words to describe physical inconsistencies. Avoid conversational filler.
3. **Directness:** Be blunt. If Audio lies, state: "Audio False. Object in palm."

**Core Principles:**
1. **Frame-by-Frame Audit:** Check every claim. If audio says "vanished" but pixels show "hidden", flag it.
2. **Evidence-Based:** Ground analysis in specific visual cues (e.g., "unnatural grip").
3. **Physics > Jargon:** Describe physical actions (e.g., "False transfer") precisely.
4. **Timestamps:** Mandatory citation for all evidence.
"""

USER_PROMPT_TEMPLATE = """
**Input Data:**

{visual_context}

{audio_context}

**Task:**
Analyze the video content. 
**WARNING:** The magician's speech typically contains lies (patter) designed to create **Cross-Modal Cognitive Conflict**. 
You must Compare what is SAID (Audio/Context) versus what is SEEN (Visual) at specific timestamps to detect the truth.
**Constraint:** Keep all JSON values extremely concise (under 20 words per field if possible).

**Output strictly in JSON format with the following keys:**
{{
  "effect_description": "Briefly describe what the audience perceives (the illusion).",
  "visual_anomalies": "List specific suspicious visual details. **MUST cite TIMESTAMPS** (e.g., '[Image 5 @ 1.2s] Left hand remains closed unnaturally').",
  "misdirection_analysis": "How is the audio trying to distract or lie to you? Compare specific audio claims with visual reality.",
  "step_by_step_deduction": "Your reasoning process to find the method. Trace the object's location over time.",
  "final_principle": "The core method. Remember: Accurate physical description is better than wrong professional jargon.",
  "confidence_score": 1 (Guessing) to 5 (Certain)
}}
"""



def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("gbk", errors="ignore").decode("gbk"))


def encode_image(image_path, max_size=1024):
    if not os.path.exists(image_path):
        return None
    try:
        with Image.open(image_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail((max_size, max_size))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        safe_print(f" 图片压缩失败 {image_path}: {e}")
        return None


def extract_json_from_response(response_text):
    text = response_text.strip()

    if "```json" in text:
        text = text.split("```json")[1].strip()
        if "```" in text:
            text = text.split("```")[0].strip()

    elif "```" in text:  
        start = text.find("{")
        if start != -1:
            text = text[start:]
            if "```" in text:
                text = text.split("```")[0].strip()

    start_idx = text.find("{")
    if start_idx == -1:
        return {"raw_output": response_text, "error": "JSON_PARSE_FAIL"}

    text = text[start_idx:]  
    try:
        return json.loads(text)
    except json.JSONDecodeError:

        pass
    try:

        clean_text = text.rstrip(",").rstrip()
        if not clean_text.endswith("}"):
            if clean_text.count('"') % 2 != 0:
                clean_text += '"'
            clean_text += "}"  

        return json.loads(clean_text)
    except:
        pass

    try:
        last_comma = text.rfind(",")
        if last_comma != -1:
            cut_text = text[:last_comma] + "}"
            return json.loads(cut_text)
    except:
        pass
    return {"raw_output": response_text, "error": "JSON_PARSE_FAIL"}


def construct_context(item, mode, template, max_frames=50):
    visual_text_str = "visual_timeline:\n"
    audio_text_str = ""

    if mode != "text_only":
        timeline = item.get("visual_timeline", [])
        if len(timeline) > max_frames:
            indices = [int(i * len(timeline) / max_frames) for i in range(max_frames)]
            sampled_timeline = [timeline[i] for i in indices]
        else:
            sampled_timeline = timeline

        for v in sampled_timeline:
            filename = v["filename"]
            candidates = [
                os.path.join(FRAMES_ROOT, filename),
                os.path.join(FRAMES_ROOT, f"labeled_{filename}"),
                os.path.join(FRAMES_ROOT, item.get("frames_folder", ""), filename),
            ]
            img_path = None
            for p in candidates:
                if os.path.exists(p):
                    img_path = p
                    break

            if img_path:
                b64_img = encode_image(img_path)
                if b64_img:
                    visual_text_str += f"- [Image {v['frame_idx']}] @ {v['timestamp']}s"
                    if "roi_normalized" in v:
                        visual_text_str += f" ROI:{v['roi_normalized']}"
                    visual_text_str += "\n"

                    yield b64_img  
    return None


def prepare_payload_data(item, mode, template, max_frames=20):
    visual_content = []
    visual_lines = []

    if mode != "text_only":
        timeline = item.get("visual_timeline", [])
        if len(timeline) > max_frames:
            indices = [int(i * len(timeline) / max_frames) for i in range(max_frames)]
            sampled = [timeline[i] for i in indices]
        else:
            sampled = timeline

        frames_found = 0

        for v in sampled:
            filename = v["filename"] 
            folder_in_json = item.get(
                "frames_folder", ""
            )  
            if "final_clips_dataset" in folder_in_json:
                sub_path = folder_in_json.split("final_clips_dataset")[-1].lstrip("/\\")
            else:
                sub_path = folder_in_json


            candidates = [
                os.path.join(FRAMES_ROOT, sub_path, filename),
                os.path.join(FRAMES_ROOT, sub_path, f"labeled_{filename}"),
                os.path.join(FRAMES_ROOT, filename),
                os.path.join(
                    "",
                    folder_in_json,
                    filename,
                ),
            ]

            img_path = None
            for p in candidates:
                if os.path.exists(p):
                    img_path = p
                    break

            if img_path:
                b64 = encode_image(img_path)
                if b64:
                    visual_content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        }
                    )
                    info = f"- [Image {v['frame_idx']}] @ {v['timestamp']}s"
                    if "roi_normalized" in v:
                        info += f" ROI:{v['roi_normalized']}"
                    visual_lines.append(info)
                    frames_found += 1
            else:

                if v["frame_idx"] == 0:
                    safe_print(f" 找不到图片! 尝试路径: {candidates[0]}")
    if mode != "text_only" and frames_found == 0:
        visual_text_str = "(ERROR: No visual frames found. Check file paths.)"
        safe_print(f" 警告: ID {item['id']} 没有加载到任何图片！")
    else:
        visual_text_str = "\n".join(visual_lines)

    if mode == "gold_context":
        principle = item.get("ground_truth", {}).get("principle", "No info")
        audio_text_str = f'**Reference Context (The Truth):**\n"{principle}"\n'
    elif mode == "vision_only":
        audio_text_str = "(Audio muted)"
    else:

        audio_text_str = "Audio Transcript:\n"
        tl = item.get("audio_timeline", [])
        if tl and len(tl) > 0:
            for seg in tl:
                audio_text_str += f"- [{seg['start']}s]: \"{seg['text']}\"\n"
        else:
            audio_text_str += "(No speech detected in this video)\n"

    if "{audio_context}" in template:
        user_prompt = template.format(
            visual_context=visual_text_str, audio_context=audio_text_str
        )
    else:
        user_prompt = template.format(visual_context=visual_text_str)

    return user_prompt, visual_content


def call_model_api(model_id, system_prompt, user_prompt, images, max_retries=5):
    api_url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": REFERER,
        "X-Title": "MagicBench",
        "Content-Type": "application/json",
    }

    messages = [{"role": "system", "content": system_prompt}]
    user_content = [{"type": "text", "text": user_prompt}]
    if images:
        user_content.extend(images)
    messages.append({"role": "user", "content": user_content})

    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 4096, 
    }

    if "gpt" in model_id:
        payload["response_format"] = {"type": "json_object"}

    for attempt in range(max_retries):
        try:
            response = requests.post(
                api_url, headers=headers, json=payload, timeout=120
            )
            if response.status_code == 200:
                data = response.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]

            elif response.status_code == 429:
                wait = 20 * (attempt + 1)
                safe_print(f" 限流 429，等待 {wait} 秒...")
                time.sleep(wait)
                continue

            else:
                safe_print(f" HTTP {response.status_code}: {response.text[:100]}")

        except Exception as e:
            safe_print(f" Request Error: {e}")

        time.sleep(5)
    return None


def run_single_experiment(config, dataset):
    model_alias = config["model"]
    mode = config["mode"]
    prompt_style = config["prompt"]
    model_id = MODEL_MAP.get(model_alias, model_alias)

    if mode == "vision_only":
        sys_prompt = (
            "You are a visual forensic analyst. Analyze visual evidence only." 
        )
        usr_template = VISION_ONLY_USER_PROMPT_TEMPLATE
    else:
        sys_prompt = (
            MULTIMODAL_FORENSIC_SYSTEM_PROMPT
            if prompt_style == "Forensic"
            else NEUTRAL_SYSTEM_PROMPT
        )
        usr_template = USER_PROMPT_TEMPLATE

    filename = f"{model_alias.replace('/', '_')}_{mode}_{prompt_style}_v4.json"
    output_filename = os.path.join(OUTPUT_DIR, filename)

    safe_print(f"\n [启动] {model_alias} | {mode}")
    safe_print(f" 保存: {output_filename}")

    results = []
    processed_ids = set()
    if os.path.exists(output_filename):
        try:
            with open(output_filename, "r", encoding="utf-8") as f:
                results = json.load(f)
                processed_ids = {item["id"] for item in results}
            safe_print(f" 跳过 {len(processed_ids)} 条记录")
        except:
            pass

    for item in tqdm(dataset, desc="Running"):
        if item["id"] in processed_ids:
            continue

        user_text, image_payload = prepare_payload_data(
            item, mode, usr_template, max_frames=20
        )

        user_text += "\n\nOutput valid JSON only:\n```json\n{"

        response_text = call_model_api(model_id, sys_prompt, user_text, image_payload)

        if response_text:

            parsed_json = extract_json_from_response(response_text)

            if "error" in parsed_json:
                status = "RAW_SAVED"
                safe_print(f" JSON Format Error {item['id']} (Saved Raw)")
            else:
                status = "SUCCESS"

            result_item = {
                "id": item["id"],
                "ground_truth": item.get("ground_truth", {}),
                "linguistic_type": item.get("linguistic_type", "Unknown"),
                "experiment_config": config,
                "model_output": parsed_json,  
                "raw_output": response_text, 
            }
            results.append(result_item)

            if len(results) % 3 == 0:
                with open(output_filename, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    safe_print(" 本组完成")


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        if isinstance(raw_data, list):
            dataset = raw_data
        else:
            print(" 警告: 输入不是列表格式，尝试直接转换 Values")
            dataset = list(raw_data.values()) if isinstance(raw_data, dict) else []

    experiments = [
        {"model": "gemini-2.5-flash", "mode": "multimodal", "prompt": "Forensic"},
        {"model": "gpt-4o", "mode": "multimodal", "prompt": "Forensic"},
        {"model": "qwen-2.5-vl", "mode": "multimodal", "prompt": "Forensic"},
        # {"model": "gemini-2.5-flash", "mode": "gold_context", "prompt": "skeptic"},
    ]

    for config in experiments:
        run_single_experiment(config, dataset)


if __name__ == "__main__":
    main()

