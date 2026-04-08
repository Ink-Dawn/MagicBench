import json
import os
from openai import OpenAI
from tqdm import tqdm

# ================= 配置区域 =================
# 输入文件：上一阶段生成的包含 frame_folder 的文件
INPUT_JSON = "magic_bench_dataset_ready.json"

# 输出文件：包含语言学分类的新文件 (下游实验直接用这个)
OUTPUT_JSON = "magic_bench_dataset_linguistic.json"

# 通过环境变量读取 API Key 和 Base URL，避免将密钥提交到 GitHub
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
# ===========================================

if not API_KEY:
    raise RuntimeError(
        "Missing OPENROUTER_API_KEY. Set it in your environment before running this script."
    )

# 初始化客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def classify_transcript(transcript, ground_truth_principle):
    """
    使用 GPT-4o 根据 'Transcript' 和 'Ground Truth' 判定欺骗类型。
    遵循优先级：Type D (无声) > Type A (谎言) > Type B (误导) > Type C (闲聊)。
    """

    # --- 🔴 修改点 1：增加 Type D 的启发式判断 ---
    # 如果没有 Transcript，或者内容过短（例如只有噪音符号），直接归为 Type D
    # 这样既省钱，又准确
    if not transcript or len(transcript.strip()) < 5:
        return (
            "Type D: No Audio",
            "The video contains no significant speech or the transcript is empty. It serves as a visual-only baseline.",
        )

    # --- 以下是调用 LLM 进行 A/B/C 分类 ---
    system_prompt = """
    You are a linguistic expert analyzing magic trick transcripts for an ACL paper.
    Your goal is to classify the magician's speech into one of three categories based on its relationship with the Ground Truth (physical reality).

    **Classification Hierarchy (Choose the highest priority that applies):**
    
    1. **Type A: Direct Lie (Highest Priority)**
       - Criteria: The magician explicitly states a fact that contradicts the physical reality described in the Ground Truth.
       - Examples: "The coin has melted" (False), "My hand is empty" (False), "It traveled to your pocket" (False).
    
    2. **Type B: Misdirection (Medium Priority)**
       - Criteria: No direct lies, but the magician uses imperatives to manipulate attention or physical actions.
       - Examples: "Look at my eyes", "Hold this tightly", "Don't blink", "Check the card".
    
    3. **Type C: Patter (Lowest Priority)**
       - Criteria: General storytelling, humor, procedure description, or truth.
       - Examples: "I will show you a trick", "Pick a card", "This is a coin".

    **Output JSON:**
    {
        "type": "Type A" / "Type B" / "Type C",
        "reasoning": "Brief explanation..."
    }
    """

    user_prompt = f"""
    **Ground Truth Principle:** {ground_truth_principle}
    
    **Transcript:** "{transcript}"
    
    **Task:** Classify the transcript. Output strictly in JSON.
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        result = json.loads(response.choices[0].message.content)

        # 清洗返回结果
        raw_type = result.get("type", "Type C")
        if "Type A" in raw_type:
            final_type = "Type A: Direct Lie"
        elif "Type B" in raw_type:
            final_type = "Type B: Misdirection"
        else:
            final_type = "Type C: Patter"

        return final_type, result.get("reasoning", "")

    except Exception as e:
        print(f"\n⚠️ API Error: {e}")
        # 如果 API 报错，暂时归为 Patter，或者你可以设为 Error
        return "Type C: Patter", "Error during classification"


def main():
    # 1. 检查输入
    if not os.path.exists(INPUT_JSON):
        print(f"❌ 找不到输入文件: {INPUT_JSON}")
        return

    # 2. 读取数据
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"📋 正在加载 {len(dataset)} 条数据，开始语言学标注...")

    # --- 🔴 修改点 2：初始化统计字典增加 Type D ---
    stats = {
        "Type A: Direct Lie": 0,
        "Type B: Misdirection": 0,
        "Type C: Patter": 0,
        "Type D: No Audio": 0,
    }

    # 3. 循环处理
    for item in tqdm(dataset, desc="AI 分类中"):

        # === 断点续传逻辑 ===
        if item.get("linguistic_type"):
            l_type = item["linguistic_type"]
            # 简单的统计逻辑
            if "Type A" in l_type:
                stats["Type A: Direct Lie"] += 1
            elif "Type B" in l_type:
                stats["Type B: Misdirection"] += 1
            elif "Type C" in l_type:
                stats["Type C: Patter"] += 1
            elif "Type D" in l_type:
                stats["Type D: No Audio"] += 1
            continue

        # 获取输入
        transcript = item.get("transcript", "")
        gt_principle = item.get("ground_truth", {}).get("principle", "")

        # 调用分类函数
        l_type, reasoning = classify_transcript(transcript, gt_principle)

        # 写入 Item
        item["linguistic_type"] = l_type
        item["linguistic_reasoning"] = reasoning

        # --- 🔴 修改点 3：实时统计增加 Type D ---
        if "Type A" in l_type:
            stats["Type A: Direct Lie"] += 1
        elif "Type B" in l_type:
            stats["Type B: Misdirection"] += 1
        elif "Type C" in l_type:
            stats["Type C: Patter"] += 1
        elif "Type D" in l_type:
            stats["Type D: No Audio"] += 1

        # 定期保存
        if int(item.get("id", "0").split("_")[-1]) % 10 == 0:
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=4)

    # 4. 最终保存
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)

    print("\n✅ 标注完成！")
    print("📊 分类统计：")
    for k, v in stats.items():
        print(f"   {k}: {v}")

    print(f"\n📂 新的 JSON 文件已生成: {OUTPUT_JSON}")
    print(
        "💡 提示：在分析'语言误导效果'时，请剔除 Type D 的样本，因为它们没有语言输入。"
    )


if __name__ == "__main__":
    main()
