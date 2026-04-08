import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import os

# ================= 配置区域 =================
# 确保这个路径指向你刚刚生成的 GPT-4o 统计文件
JSON_FILE = "magic_Gemini-2.5_bench_overall_stats.json"

# 定义 JSON 中的 Method Key 到图例标签的映射
# 顺序决定了绘图的堆叠顺序和颜色分配
FILE_MAPPING = {
    "Truth Context (Upper Bound)": "Truth Context (Upper Bound)",
    "Vision-Only (Capability Probe)": "Vision-Only (Capability Probe)",
    "Multimodal (Forensic)": "Multimodal (Forensic)",  # <--- 新增
    "Multimodal (Skeptic)": "Multimodal (Skeptic)",
    "Multimodal (Neutral)": "Multimodal (Neutral)",
}

# 定义 JSON 中的 Type Key 到图表 X 轴标签的映射
TYPE_MAPPING = {
    "Type A: Direct Lie": "Type A",
    "Type B: Misdirection": "Type B",
    "Type C: Patter": "Type C",
    "Type D: No Audio": "Type D",
    "Total": "Total",
}

# 配色方案：蓝(Skeptic), 橙(Vision), 绿(Neutral), 红(Truth), 紫(Forensic)
# 为了突出 Forensic，我们给它一个显眼的紫色
COLORS = ["#d62728", "#ff7f0e", "#9467bd", "#1f77b4", "#2ca02c"]

# ================= 1. 数据处理函数 =================


def load_processed_data(json_path):
    if not os.path.exists(json_path):
        print(f"❌ 错误: 找不到文件 {json_path}")
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    processed_data = {}
    # 按照 FILE_MAPPING 定义的顺序加载数据
    for json_key, legend_label in FILE_MAPPING.items():
        if json_key not in raw_data:
            print(f"⚠️ 跳过: JSON 中缺少 {json_key}")
            continue

        method_data = raw_data[json_key]
        processed_data[legend_label] = {}

        for long_type, short_type in TYPE_MAPPING.items():
            if long_type in method_data:
                m = method_data[long_type]
                # 提取 VTG, CPA, CFR 分数
                processed_data[legend_label][short_type] = [
                    m.get("VTG", 0),
                    m.get("CPA", 0),
                    m.get("CFR", 0),
                ]
    return processed_data


# ================= 2. 绘图执行 =================

data = load_processed_data(JSON_FILE)
if not data:
    exit()

plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 12
plt.rcParams["axes.linewidth"] = 1.0
plt.rcParams["grid.alpha"] = 0.3
plt.rcParams["figure.dpi"] = 300

metrics = ["VTG", "CPA", "CFR"]
types = ["Type A", "Type B", "Type C", "Type D", "Total"]
line_types = ["Type A", "Type B", "Type C", "Type D"]

# --- 图一：柱状图 (Performance Breakdown) ---
fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=True)
fig.suptitle(
    "GPT-4o Performance Breakdown by Linguistic Interference",
    fontsize=16,
    fontweight="bold",
    y=1.05,
)

for i, metric in enumerate(metrics):
    ax = axes[i]
    x = np.arange(len(types))
    width = 0.15  # 5个柱子，宽度调窄一点

    for j, (label, categories) in enumerate(data.items()):
        values = [categories[t][i] for t in types]
        ax.bar(
            x + j * width,
            values,
            width,
            label=label,
            color=COLORS[j],
            edgecolor="black",
            linewidth=0.5,
        )

    ax.set_title(f"{metric}", fontsize=14, fontweight="bold")
    ax.set_xticks(x + width * 2)
    ax.set_xticklabels(types, rotation=45)
    ax.set_ylabel("Percentage (%)" if i == 0 else "")
    ax.set_ylim(0, 105)
    ax.grid(axis="y", linestyle="--")

# 图例放在底部
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.1),
    ncol=3,
    frameon=False,
)

plt.tight_layout()
plt.savefig("Gemini-2.5_performance_bar_final.png", bbox_inches="tight")
plt.show()

# --- 图二：折线图 (Agency Loss Trend) ---
fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=True)
fig.suptitle(
    "Diagnostic Trend: Type A → Type D (Agency Loss Identification)",
    fontsize=16,
    fontweight="bold",
    y=1.05,
)

for i, metric in enumerate(metrics):
    ax = axes[i]
    for j, (label, categories) in enumerate(data.items()):
        values = [categories[t][i] for t in line_types]

        # 特殊处理：如果是 Truth Context，用虚线
        ls = "--" if "Truth" in label else "-"
        # 特殊处理：如果是 Forensic，加粗显示
        lw = 4 if "Forensic" in label else 2.5

        ax.plot(
            line_types,
            values,
            marker="o",
            markersize=8,
            linewidth=lw,
            linestyle=ls,
            label=label,
            color=COLORS[j],
            markeredgecolor="white",
        )

    ax.set_title(f"{metric}", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.grid(True, linestyle=":")
    ax.set_ylabel("Percentage (%)" if i == 0 else "")

    # 在 Type D 处画一个大箭头突出 Agency Loss (仅在 CPA 图中)
    if metric == "CPA":
        # 获取 Vision-Only 和 Forensic 在 Type D 的值
        v_val = data["Vision-Only (Capability Probe)"]["Type D"][1]
        f_val = data["Multimodal (Forensic)"]["Type D"][1]
        ax.annotate(
            "",
            xy=("Type D", f_val),
            xytext=("Type D", v_val),
            arrowprops=dict(facecolor="red", shrink=0.05, width=2, headwidth=8),
        )
        ax.text(
            "Type D",
            (v_val + f_val) / 2 + 5,
            "Agency Loss",
            color="red",
            fontweight="bold",
            ha="center",
        )

fig.legend(
    handles,
    labels,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.1),
    ncol=3,
    frameon=False,
)
plt.tight_layout()
plt.savefig("Gemini-2.5_agency_loss_line_final.png", bbox_inches="tight")
plt.show()
