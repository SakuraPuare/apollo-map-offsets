# 快速参考卡片

## 📁 目录结构 (v1.1.0)

```
项目根目录/
├── input/              ← 输入文件
│   ├── raw.json        (加密数据，可选)
│   ├── scenarios.json  (必需)
│   ├── data.json       (或由 raw.json 解密得到)
│   └── base_map.bin    (可选)
│
├── results/            ← 计算结果
│   └── offset_results.json
│
├── visualizations/     ← 可视化图表
│   ├── 01_matching_overview.png
│   ├── 02_detailed_matching.png
│   ├── 03_vector_field.png
│   ├── 04_obstacles_detailed.png
│   └── 05_obstacles_boxes.png
│
└── output/             ← 最终输出
    ├── base_map_offset.bin
    └── scenarios_new.json
```

## 🚀 快速命令

### 一键运行
```bash
python3 run_pipeline.py
```

### 分步运行
```bash
# 步骤0: 解密数据（如果有 raw.json）
python3 step0_decrypt_raw_data.py

# 步骤1: 计算偏移
python3 step1_calculate_offset.py

# 步骤2: 可视化（可同时运行）
python3 step2a_visualize_matching.py
python3 step2b_visualize_obstacles.py

# 步骤3: 场景处理线
python3 step4_create_scenario.py -o output/scenarios_new.json

# 步骤3: 地图处理线（并行）
python3 step3_apply_offset_to_map.py <map_file> output/offset_map.bin --format binary
python3 step5_generate_sim_map.py --map_dir output

# 编译 sim_map_generator（仅首次）
cd /apollo_workspace
bazel build //modules/map/tools:sim_map_generator
```

## 📝 常用参数

### step4_create_scenario.py
```bash
# 只包含匹配的障碍物（默认）
python3 step4_create_scenario.py

# 包含所有障碍物
python3 step4_create_scenario.py --all-objects

# 自定义输出路径
python3 step4_create_scenario.py -o output/my_scenario.json
```

### step3_apply_offset_to_map.py
```bash
# 使用结果文件中的偏移量
python3 step3_apply_offset_to_map.py input/map.bin output/map_offset.bin

# 手动指定偏移量
python3 step3_apply_offset_to_map.py input/map.bin output/map_offset.bin \
  --offset-x 9000 --offset-y 9000 --rotation 0
```

## 🔍 检查结果

### 1. 查看偏移量
```bash
cat results/offset_results.json | jq '.transformation'
```

### 2. 查看匹配精度
```bash
cat results/offset_results.json | jq '.accuracy'
```

### 3. 查看可视化
```bash
open visualizations/01_matching_overview.png
```

## ⚠️ 问题排查

### 文件不存在
```bash
# 检查 input 目录
ls -la input/

# 应该包含：
# - scenarios.json
# - data.json
# - base_map.bin (可选)
```

### 创建缺失目录
```bash
mkdir -p input results visualizations output
```

### 移动文件到正确位置
```bash
mv scenarios.json input/
mv data.json input/
mv base_map.bin input/  # 如果有
```

## 📊 输出说明

### results/offset_results.json
- `transformation.translation` - 平移量 (Δx, Δy)
- `transformation.rotation_degrees` - 旋转角度
- `accuracy.mean_error` - 平均误差
- `matched_pairs` - 所有匹配对

### visualizations/*.png
- 高分辨率（300 DPI）
- 用于验证匹配质量
- 可直接用于报告/展示

### output/scenarios_new.json
- OpenSCENARIO 格式
- 连续 ID（1, 2, 3...）
- 原始 ID 保存在 properties 中

## 💡 最佳实践

1. **先运行可视化，验证结果再应用**
   ```bash
   python3 step1_calculate_offset.py
   python3 step2a_visualize_matching.py
   # 检查图表 → 确认无误 → 继续
   python3 step3_apply_offset_to_map.py ...
   ```

2. **检查匹配精度**
   - mean_error < 5m：优秀 ✅
   - mean_error 5-10m：良好 👍
   - mean_error > 10m：需检查 ⚠️

3. **备份原始文件**
   ```bash
   cp input/base_map.bin input/base_map.bin.backup
   ```

## 📚 文档索引

- `QUICKSTART.md` - 快速开始
- `README.md` - 完整文档
- `CHANGELOG.md` - 更新日志
- `SUMMARY.md` - 项目总结
- `project_structure.txt` - 详细结构

---

**版本**: v1.1.0 | **更新时间**: 2025-01-07
