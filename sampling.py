import json
import random
import os

# ================= 配置区域 =================
# 1. 模型推理结果文件 (包含 judge_result)
FILES = {
    "GPT-4o": r"D:\visual_studio_code\VScode_Project\魔术视频\frames\results\gpt-4o_multimodal_skeptic_judged_v2.json",
    "Gemini": r"D:\visual_studio_code\VScode_Project\魔术视频\results\gemini-2.5-flash_multimodal_skeptic_v4_judged_v2.json",
    "Qwen": r"D:\visual_studio_code\VScode_Project\魔术视频\results\qwen-2.5-vl_multimodal_skeptic_judged_v2.json",
}

# 2. 原始数据集文件 (用于补充 video_filename, transcript 等信息)
ORIGINAL_DATASET_PATH = r"D:\visual_studio_code\VScode_Project\魔术视频\frames\magic_bench_dataset_with_timestamps.json"

# 3. 输出文件
OUTPUT_JSON = "meta_eval_50_samples.json"
# ========================================


def load_json(filepath):
    if not os.path.exists(filepath):
        print(f"⚠️ 文件不存在: {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def create_dataset_map(original_data):
    """将原始数据集转换为 id -> item 的字典，方便查询"""
    data_map = {}
    for item in original_data:
        if "id" in item:
            data_map[item["id"]] = item
    return data_map


def sample_strategy():
    print("🔄 正在加载原始数据集...")
    original_data = load_json(ORIGINAL_DATASET_PATH)
    if not original_data:
        return

    # 建立索引映射，加速查找
    original_map = create_dataset_map(original_data)
    print(f"✅ 原始数据集加载完毕，共 {len(original_map)} 条数据。")

    final_samples = []

    # 遍历每个模型的结果文件
    for model_name, filepath in FILES.items():
        print(f"Sampling from {model_name}...")
        result_data = load_json(filepath)
        if not result_data:
            continue

        # --- 分层抽样逻辑 (保持不变) ---
        type_groups = {"Type D": [], "Other": []}
        for item in result_data:
            l_type = item.get("linguistic_type", "")
            if "Type D" in l_type:
                type_groups["Type D"].append(item)
            else:
                type_groups["Other"].append(item)

        # 抽样数量配置
        n_total = 17 if model_name != "Qwen" else 16
        n_type_d = 5
        n_other = n_total - n_type_d

        random.seed(42)  # 固定种子

        # 确保不越界
        safe_n_d = min(len(type_groups["Type D"]), n_type_d)
        safe_n_other = min(len(type_groups["Other"]), n_other)

        selected_d = random.sample(type_groups["Type D"], safe_n_d)
        selected_other = random.sample(type_groups["Other"], safe_n_other)

        selected = selected_d + selected_other

        # --- 数据合并与重组 ---
        for item in selected:
            vid = item["id"]

            # 从原始数据集中获取元数据
            orig_info = original_map.get(vid, {})

            # 构造最终的评测条目
            entry = {
                "id": vid,
                "Model_Source": model_name,
                "Type": item.get("linguistic_type", "Unknown"),
                # 1. 来自原始数据集的信息 (用于人工观看和判断)
                "video_filename": orig_info.get("video_filename", "Unknown"),
                "ground_truth": orig_info.get("ground_truth", {}),  # 包含 principle
                "transcript": orig_info.get("transcript", ""),
                # 2. 来自模型推理结果的信息
                "model_output": item.get("model_output", {}),  # 解析后的 JSON
                "raw_output": item.get("raw_output", ""),  # 原始文本
                "GPT4_Judge_Result_Original": item.get(
                    "judge_result", {}
                ),  # 之前脚本跑出来的 judge 结果
                # 3. 预留打分位置 (方便填入)
                "Human_Score": None,  # 等待你人工打分 (0-10)
                "Claude_Judge_Score": None,  # 等待 Claude API 脚本填入
                "GPT4_Judge_Score_ReEval": None,  # 如果你想重新跑一遍 GPT4 验证，也可以留着
            }
            final_samples.append(entry)

    # 保存结果
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_samples, f, indent=4, ensure_ascii=False)

    print(f"🎉 抽样完成！共 {len(final_samples)} 条数据。")
    print(f"💾 结果已保存至: {OUTPUT_JSON}")
    print(
        "👉 接下来你可以使用 Claude API 脚本读取此文件并填入 'Claude_Judge_Score'，或者人工阅读此文件进行打分。"
    )


if __name__ == "__main__":
    sample_strategy()
