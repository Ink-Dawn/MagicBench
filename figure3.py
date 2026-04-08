import matplotlib.pyplot as plt
import numpy as np

# ================= 1. 数据准备 =================
cpa_data = {
    "Truth Context": [86.67, 87.03, 86.98, 86.30],
    "Vision Only": [32.99, 38.11, 34.51, 28.15],  # 能力上限 (Probe)
    "Multi (Forensic)": [43.38, 43.33, 33.64, 15.83],
    "Multi (Skeptic)": [35.75, 43.95, 29.78, 10.37],
    "Multi (Neutral)": [35.55, 34.47, 25.60, 4.44],  # 默认行为 (Default)
}

bar_labels = [
    "Type A\n(Lie)",
    "Type B\n(Misdir.)",
    "Type C\n(Chat)",
    "Type D\n(Silence)",
]

# ================= 2. 绘图全局设置 =================
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 12
plt.rcParams["figure.dpi"] = 300

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5))

color_truth = "#d62728"  # 红色
color_vision = "#ff7f0e"  # 橙色 (Vision Only)
color_forensic = "#9467bd"  # 紫色
color_skeptic = "#1f77b4"  # 蓝色
color_neutral = "#2ca02c"  # 绿色 (Neutral)

# ================= 左图：柱状图 (维持原样) =================
bar_width = 0.15
index = np.arange(len(bar_labels))

ax1.bar(
    index - 2 * bar_width,
    cpa_data["Truth Context"],
    bar_width,
    label="Truth Context",
    color=color_truth,
    edgecolor="black",
    alpha=0.7,
    hatch="//",
)
ax1.bar(
    index - 1 * bar_width,
    cpa_data["Multi (Forensic)"],
    bar_width,
    label="Multi (Forensic)",
    color=color_forensic,
    edgecolor="black",
    alpha=0.9,
)
ax1.bar(
    index,
    cpa_data["Multi (Skeptic)"],
    bar_width,
    label="Multi (Skeptic)",
    color=color_skeptic,
    edgecolor="black",
    alpha=0.9,
)
ax1.bar(
    index + 1 * bar_width,
    cpa_data["Multi (Neutral)"],
    bar_width,
    label="Multi (Neutral)",
    color=color_neutral,
    edgecolor="black",
    alpha=0.9,
)
ax1.bar(
    index + 2 * bar_width,
    cpa_data["Vision Only"],
    bar_width,
    label="Vision Only",
    color=color_vision,
    edgecolor="black",
    alpha=0.9,
)

ax1.set_title("(a) CPA Score Comparison", fontweight="bold", fontsize=15)
ax1.set_ylabel("CPA Score (%)", fontsize=13)
ax1.set_xticks(index)
ax1.set_xticklabels(bar_labels, fontsize=12)
ax1.set_ylim(0, 105)
ax1.grid(axis="y", linestyle="--", alpha=0.4)

# ================= 右图：折线图 (强化 Agency Loss 展示) =================
x_line = np.arange(4)

# 1. 绘制阴影区域：展示从 Vision Only 到 Neutral 的性能流失
# ax2.fill_between(
#     x_line,
#     cpa_data["Vision Only"],
#     cpa_data["Multi (Neutral)"],
#     color="red",
#     alpha=0.1,
#     label="Agency Loss Zone",
# )

# 2. 绘制各条折线
ax2.plot(
    x_line,
    cpa_data["Truth Context"],
    marker="*",
    linewidth=1.5,
    color=color_truth,
    linestyle="--",
    alpha=0.5,
    label="Truth Context",
)
ax2.plot(
    x_line,
    cpa_data["Vision Only"],
    marker="o",
    linewidth=4,
    color=color_vision,
    label="Vision Only (Capability)",
    zorder=10,
)
ax2.plot(
    x_line,
    cpa_data["Multi (Forensic)"],
    marker="D",
    linewidth=2,
    color=color_forensic,
    alpha=0.8,
    label="Multi (Forensic)",
)
ax2.plot(
    x_line,
    cpa_data["Multi (Skeptic)"],
    marker="^",
    linewidth=2,
    color=color_skeptic,
    alpha=0.8,
    label="Multi (Skeptic)",
)
ax2.plot(
    x_line,
    cpa_data["Multi (Neutral)"],
    marker="s",
    linewidth=4,
    color=color_neutral,
    label="Multi (Neutral Behavior)",
    zorder=10,
)

# 3. 装饰右图
ax2.set_title(
    "(b) Robustness Trend: Visual Agency Loss", fontweight="bold", fontsize=15
)
ax2.set_ylabel("CPA Score (%)", fontsize=13)
ax2.set_xticks(x_line)
ax2.set_xticklabels(bar_labels, fontsize=12)
ax2.set_ylim(0, 105)
ax2.grid(True, linestyle=":", alpha=0.6)

# 4. 关键标注：Type D 下的断崖式下跌
# 从 Vision Only (index 3) 指向 Neutral (index 3)
ax2.annotate(
    "",
    xy=(3, cpa_data["Multi (Neutral)"][3]),
    xytext=(3, cpa_data["Vision Only"][3]),
    arrowprops=dict(arrowstyle="<->", color="red", lw=2.5),
)

# 添加文本描述
ax2.text(
    3.1,
    (cpa_data["Vision Only"][3] + cpa_data["Multi (Neutral)"][3]) / 2,
    "Visual\nAgency Loss",
    color="red",
    va="center",
    fontweight="bold",
    fontsize=11,
)

# ================= 统一图例 (Legend) =================
handles, labels = ax2.get_legend_handles_labels()
# 过滤掉不需要出现在图例中的项，或重新排列
fig.legend(
    handles,
    labels,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.05),
    ncol=3,
    frameon=False,
    fontsize=11,
)

plt.tight_layout()
plt.savefig("Figure_AgencyLoss_Focus.pdf", bbox_inches="tight")
plt.show()
