"""統一設定 matplotlib 中文字型，避免圖表裡的中文顯示成方塊。"""

import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
