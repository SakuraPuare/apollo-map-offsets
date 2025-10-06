# 快速开始指南

## 🚀 一键运行

```bash
python3 run_pipeline.py
```

按提示操作即可完成整个流程。

---

## 📝 分步运行

### 1️⃣ 计算偏移量
```bash
python3 step1_calculate_offset.py
```
**输出**: `results/offset_results.json`

### 2️⃣ 生成可视化
```bash
python3 step2a_visualize_matching.py
python3 step2b_visualize_obstacles.py
```
**输出**: `visualizations/*.png` (5张图)

### 3️⃣ 应用偏移到地图（可选）
```bash
python3 step3_apply_offset_to_map.py input/base_map.bin output/base_map_offset.bin --format binary
```
**输出**: `output/base_map_offset.bin`

### 4️⃣ 创建新场景
```bash
# 只包含匹配的障碍物
python3 step4_create_scenario.py -o output/scenarios_new.json

# 包含所有障碍物
python3 step4_create_scenario.py -o output/scenarios_all.json --all-objects
```
**输出**: `output/scenarios_new.json`

---

## 📂 目录结构

```
.
├── input/               # 输入文件
├── results/             # 计算结果
├── visualizations/      # 可视化图表
└── output/              # 最终输出（地图+场景）
```

---

## ⚠️ 必需文件

将以下文件放入 `input/` 目录：
- `input/scenarios.json` - 原始场景
- `input/data.json` - 障碍物数据
- `input/base_map.bin` - 地图文件（可选）

---

## 💡 验证结果

1. 查看 `results/offset_results.json` 中的 `mean_error`
   - < 5m：优秀 ✅
   - 5-10m：良好 👍
   - \> 10m：需检查 ⚠️

2. 检查可视化图表：
   - `visualizations/01_matching_overview.png`
   - `visualizations/04_obstacles_detailed.png`

---

详细文档请参阅 [README.md](README.md)
