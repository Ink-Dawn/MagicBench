import cv2
import json
import os
import numpy as np

# ================= 配置区域 =================
# 存放待标注图片的文件夹
INPUT_IMAGE_DIR = r"D:\visual_studio_code\VScode_Project\魔术视频\case"

# 存放结果的文件夹
OUTPUT_DIR = "roi_results"
LABELED_DIR = os.path.join(OUTPUT_DIR, "labeled_images")
JSON_PATH = os.path.join(OUTPUT_DIR, "roi_annotations.json")

# 如果文件夹不存在则创建
os.makedirs(LABELED_DIR, exist_ok=True)


# --- 兼容中文路径的读取函数 ---
def cv_imread(file_path):
    # 使用 numpy 读取 raw 数据，再解码，避开 opencv 不支持中文路径的问题
    cv_img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
    return cv_img


# --- 兼容中文路径的保存函数 ---
def cv_imwrite(file_path, img):
    # 先编码成图片格式，再用 numpy 写入文件
    ext = os.path.splitext(file_path)[1]
    result, n = cv2.imencode(ext, img)
    if result:
        with open(file_path, mode="wb") as f:
            n.tofile(f)


def batch_annotate_roi():
    # 获取文件夹内所有图片
    valid_extensions = (".jpg", ".jpeg", ".png", ".bmp")
    if not os.path.exists(INPUT_IMAGE_DIR):
        print(f" 错误：找不到输入文件夹 {INPUT_IMAGE_DIR}")
        return

    image_files = [
        f for f in os.listdir(INPUT_IMAGE_DIR) if f.lower().endswith(valid_extensions)
    ]

    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            all_results = json.load(f)
    else:
        all_results = {}

    print(f" 开始批量标注，共 {len(image_files)} 张图片")
    print(" 操作提示：鼠标拖拽画框，【空格】确认，【ESC】退出")

    for filename in image_files:
        if filename in all_results:
            print(f" 跳过已标注: {filename}")
            continue

        img_path = os.path.join(INPUT_IMAGE_DIR, filename)

        # 使用新定义的中文兼容读取函数
        img = cv_imread(img_path)

        if img is None:
            print(f" 读取失败，请检查文件: {img_path}")
            continue

        h, w, _ = img.shape
        window_title = f"Annotating: {filename}"

        # selectROI 弹窗
        roi = cv2.selectROI(window_title, img, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(window_title)

        x, y, rw, rh = roi
        if rw == 0 or rh == 0:
            print(f" 未选框，跳过: {filename}")
            continue

        # 1. 归一化坐标
        x1, y1, x2, y2 = x / w, y / h, (x + rw) / w, (y + rh) / h
        roi_coords = [round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4)]

        # 2. 保存带红框的图（使用中文兼容保存函数）
        labeled_img = img.copy()
        cv2.rectangle(labeled_img, (x, y), (x + rw, y + rh), (0, 0, 255), 3)
        labeled_path = os.path.join(LABELED_DIR, f"labeled_{filename}")
        cv_imwrite(labeled_path, labeled_img)

        # 3. 记录数据
        all_results[filename] = {
            "original_path": img_path,
            "labeled_path": labeled_path,
            "roi_normalized": roi_coords,
            "image_size": [w, h],
        }

        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=4, ensure_ascii=False)

        print(f" 已保存: {filename} -> ROI: {roi_coords}")

    print(f"\n 标注任务完成！结果已保存至: {OUTPUT_DIR}")


if __name__ == "__main__":
    batch_annotate_roi()
# "magic_115"
