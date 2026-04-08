from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg
import os

# ================= 配置区域 =================
# 待处理的视频文件夹 (可以是上一动下载的 raw 文件夹)
INPUT_FOLDER = "./magic_dataset_raw"
# 切片后保存的文件夹
OUTPUT_FOLDER = "./magic_dataset_split"
# ===========================================


# -----------------------------------------------------------------
# 1. 难度分级逻辑 (与爬虫代码保持一致)
# -----------------------------------------------------------------
def get_difficulty_level(filename):
    t = filename.lower()

    if any(
        k in t
        for k in ["大师", "神级", "冠军", "极限", "研讨会", "master", "god", "lecture"]
    ):
        return "Level_5_Master_大师级"
    elif any(
        k in t
        for k in [
            "高级",
            "高阶",
            "困难",
            "复杂",
            "控牌",
            "纯手法",
            "advanced",
            "hard",
            "sleight",
        ]
    ):
        return "Level_4_Advanced_高级"
    elif any(
        k in t
        for k in [
            "简单",
            "幼儿",
            "儿童",
            "趣味",
            "小魔术",
            "生活",
            "科学",
            "easy",
            "simple",
            "fun",
        ]
    ):
        return "Level_1_Beginner_简单趣味"
    elif any(
        k in t
        for k in [
            "入门",
            "新手",
            "基础",
            "初级",
            "必学",
            "第一课",
            "萌新",
            "basic",
            "beginner",
        ]
    ):
        return "Level_2_Basic_新手入门"
    elif any(k in t for k in ["进阶", "中级", "实战", "流程", "教学", "intermediate"]):
        return "Level_3_Intermediate_进阶实战"
    else:
        return "Level_0_Unsorted_未分类"


# -----------------------------------------------------------------
# 2. 视频切片核心函数
# -----------------------------------------------------------------
def split_video_into_scenes(video_path, output_base_dir, current_level_folder=None):
    filename = os.path.basename(video_path)
    video_name_no_ext = os.path.splitext(filename)[0]

    # 智能判断路径逻辑：
    # 如果传入了 current_level_folder (说明源文件已经在分类文件夹里了)，就沿用它。
    # 如果没传入 (说明源文件在根目录)，就根据文件名重新判断一次难度。
    if not current_level_folder or current_level_folder == ".":
        level_name = get_difficulty_level(video_name_no_ext)
    else:
        level_name = current_level_folder

    # 构造最终输出路径： ./输出目录/等级/视频名/
    final_output_dir = os.path.join(output_base_dir, level_name, video_name_no_ext)

    # 如果这个视频已经处理过（文件夹存在且有内容），跳过，节省时间
    if os.path.exists(final_output_dir) and os.listdir(final_output_dir):
        print(f"[跳过] 已存在: {video_name_no_ext}")
        return

    if not os.path.exists(final_output_dir):
        os.makedirs(final_output_dir)

    print(f"\n>>> 正在分析: {filename}")
    print(f"    归类为: [{level_name}]")

    # --- SceneDetect 逻辑 ---
    try:
        video = open_video(video_path)
        scene_manager = SceneManager()
        # 阈值 27.0 是经验值，针对魔术动作
        scene_manager.add_detector(ContentDetector(threshold=27.0))

        scene_manager.detect_scenes(video, show_progress=True)
        scene_list = scene_manager.get_scene_list()

        if not scene_list:
            print("    [提示] 未检测到明显场景切换，可能是单镜头视频。")
            # 如果没检测到，可以选择把整个视频复制过去，或者只切一段
            # 这里如果不切，可能无法生成文件，视需求而定。
            return

        print(f"    检测到 {len(scene_list)} 个场景，开始物理切割...")

        # 调用 ffmpeg 切割
        split_video_ffmpeg(
            video_path,
            scene_list,
            output_file_template=f"{final_output_dir}/Scene-$SCENE_NUMBER.mp4",
            show_progress=True,
        )

        print(f"    完成！保存至: {final_output_dir}")

    except Exception as e:
        print(f"    [错误] 处理失败: {e}")


# -----------------------------------------------------------------
# 3. 批量遍历处理
# -----------------------------------------------------------------
def batch_process_folder(input_folder, output_base):
    if not os.path.exists(input_folder):
        print(f"错误：找不到输入文件夹 {input_folder}")
        return

    # os.walk 会递归遍历所有子文件夹
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            # 过滤掉非视频文件，防止报错
            if file.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
                # 排除掉已经是切片的文件（防止重复切）
                if "Scene-" in file:
                    continue

                full_path = os.path.join(root, file)

                # 计算当前文件相对于输入根目录的路径
                # 比如：如果文件在 magic_dataset_raw/Level_1/video.mp4
                # rel_path 就是 "Level_1"
                rel_path = os.path.relpath(root, input_folder)

                split_video_into_scenes(full_path, output_base, rel_path)


if __name__ == "__main__":
    print("=== 魔术视频智能切片与分级工具 ===")
    print(f"源目录: {INPUT_FOLDER}")
    print(f"输出目录: {OUTPUT_FOLDER}")
    print("开始处理...\n")

    batch_process_folder(INPUT_FOLDER, OUTPUT_FOLDER)
    print("finidh!!")
