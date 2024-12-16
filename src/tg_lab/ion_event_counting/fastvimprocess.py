import concurrent.futures
import os
import time

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from numba import jit
from PIL import Image


@jit(nopython=True)
def event_counting(
    input_buffer, threshold, mode, nxnarea, multiply_factor, int_offset, event_size=1
):
    maxrow, maxcol = input_buffer.shape
    event_count = np.zeros_like(input_buffer, dtype=np.int32)
    N = 0

    half_nxn = nxnarea // 2
    half_event_size = event_size // 2

    for y in range(half_nxn, maxrow - half_nxn):
        for x in range(half_nxn, maxcol - half_nxn):
            value = input_buffer[y, x] - int_offset
            if value >= threshold:
                is_peak = True
                for dy in range(-half_nxn, half_nxn + 1):
                    for dx in range(-half_nxn, half_nxn + 1):
                        if (dy, dx) != (0, 0) and input_buffer[
                            y + dy, x + dx
                        ] - int_offset > value:
                            is_peak = False
                            break
                    if not is_peak:
                        break

                if is_peak:
                    adjusted_value = (
                        value * multiply_factor if mode >= 10 else multiply_factor
                    )
                    for ey in range(-half_event_size, half_event_size + 1):
                        for ex in range(-half_event_size, half_event_size + 1):
                            event_count[y + ey, x + ex] = adjusted_value
                    N += 1

    return event_count, N


def image_to_array(image_path):
    try:
        with Image.open(image_path) as img:
            img = img.convert("L")
            return np.array(img, dtype=np.int64), None
    except Exception as e:
        return None, str(e)


def array_to_img(array):
    return Image.fromarray(np.uint8(array))


def process_single_image(file_path):
    threshold = 70
    mode = 5
    nxnarea = 5
    multiply_factor = 5
    int_offset = 10
    current_image_array, error = image_to_array(file_path)
    if error:
        return None, error
    event_map, num_events = event_counting(
        current_image_array, threshold, mode, nxnarea, multiply_factor, int_offset
    )
    print("num_events:", num_events)
    # result_image = array_to_img(event_map * 255)
    return event_map, None


def process_images_in_folder(folder_path):
    all_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(folder_path)
        for file in files
        if file.endswith(".bmp")
    ]

    sum_array = None
    skipped_files = 0
    num_images = 0

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for current_array, error in executor.map(process_single_image, all_files):
            if error:
                skipped_files += 1
                continue

            if sum_array is None:
                sum_array = current_array
            else:
                sum_array += current_array
            num_images += 1

    print(f"Total processed images: {num_images}")
    print(f"Total skipped files: {skipped_files}")
    return sum_array, num_images


def save_array_to_csv(array, folder_path, file_name):
    if array is not None:
        file_path = os.path.join(folder_path, file_name)
        np.savetxt(file_path, array, delimiter=",", fmt="%d")
        print(f"Array saved to {file_path}")
    else:
        print("No array to save.")


def read_array_from_csv(file_path):
    return np.loadtxt(file_path, delimiter=",")


def subtract_arrays(array_a, array_b):
    return array_a - array_b


if __name__ == "__main__":
    time_start = time.time()
    folder_path_a = "D:/Experimental_Data/20240918/VMI-3000V-4.78us-25ns-Opened-MCP1175-15000-1"  # 替换为你的文件夹路径
    folder_path_b = "D:/Experimental_Data/20240918/VMI-3000V-4.78us-25ns-Closed-MCP1175-15000-1"  # 替换为你的文件夹路径

    sum_array_a, num_image_a = process_images_in_folder(folder_path_a)
    save_array_to_csv(sum_array_a, folder_path_a, "sum_array_a.csv")
    save_array_to_csv(sum_array_a / num_image_a, folder_path_a, "avg_array_a.csv")
    sum_array_b, num_image_b = process_images_in_folder(folder_path_b)
    save_array_to_csv(sum_array_b, folder_path_b, "sum_array_b.csv")
    save_array_to_csv(sum_array_b / num_image_b, folder_path_b, "avg_array_b.csv")
    Magnification = 1
    result_array = subtract_arrays(sum_array_a, sum_array_b * Magnification)

    save_array_to_csv(result_array, folder_path_a, "result array.csv")

    plt.figure(figsize=(16, 10))
    # 定义一个从蓝色到红色的渐变颜色映射
    # 创建一个从深蓝色到红色的自定义colormap

    # 定义颜色
    colors = ["blue", "cyan", "lawngreen", "yellow", "red"]  # 蓝 靛 绿 黄 红
    n_bins = [0.0, 0.25, 0.5, 0.75, 1.0]  # 定义颜色在色表中的位置
    # 创建颜色映射对象
    cmap_name = "my_list"
    cm = mcolors.LinearSegmentedColormap.from_list(cmap_name, list(zip(n_bins, colors)))
    # 可以调整这些值来针对你的数据进行定制
    vmin = 0
    vmax = result_array.max()

    threshold = 0.05
    vcenter = threshold * vmax  # 设置更多数据映射到蓝色部分

    # 创建TwoSlopeNorm实例
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)

    # 绘制图像
    cax = plt.imshow(result_array, cmap=cm, norm=norm)
    plt.colorbar(cax, shrink=0.8)
    time_end = time.time()
    print(f"Total processing time: {time_end - time_start} seconds")

    plt.axis("off")
    plt.savefig(folder_path_a + "/result.png", dpi=300, bbox_inches="tight")
    plt.show()
