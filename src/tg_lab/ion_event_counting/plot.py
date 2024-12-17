import matplotlib as plt
import matplotlib.colors as mcolors
import tyro
from matplotlib.colors import TwoSlopeNorm

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

plt.axis("off")
plt.savefig(output_dir + "/result.png", dpi=300, bbox_inches="tight")
plt.show()
