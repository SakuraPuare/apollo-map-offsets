# 安装指南

## 快速开始

### 1. 安装 Python 依赖

```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 uv（推荐，更快）
uv pip install -r requirements.txt
```

### 2. 准备输入文件

将以下文件放到 `input/` 目录:

**选项 A: 使用加密数据**
```
input/
  ├── raw.json          # 加密的原始数据
  └── scenarios.json    # 场景文件
```

**选项 B: 使用已解密数据**
```
input/
  ├── data.json         # 解密后的障碍物数据
  └── scenarios.json    # 场景文件
```

### 3. 运行 Pipeline

```bash
# 一键运行完整 pipeline
python3 run_pipeline.py
```

## 单步运行

如果需要单独运行某个步骤：

```bash
# Step 0: 解密（如果有 raw.json）
python3 step0_decrypt_raw_data.py

# Step 1: 计算偏移
python3 step1_calculate_offset.py

# Step 2a: 匹配可视化
python3 step2a_visualize_matching.py

# Step 2b: 障碍物可视化
python3 step2b_visualize_obstacles.py

# Step 3: 应用偏移到地图（可选）
python3 step3_apply_offset_to_map.py <input_map> <output_map>

# Step 4: 创建新场景
python3 step4_create_scenario.py -o output/scenarios_new.json

# Step 5: 生成 sim_map（可选）
python3 step5_generate_sim_map.py --map_dir output
```

## 输出文件

运行完成后会生成：

```
results/
  └── offset_results.json       # 偏移计算结果

visualizations/
  ├── 01_matching_overview.png
  ├── 02_detailed_matching.png
  ├── 03_vector_field.png
  ├── 04_obstacles_detailed.png
  └── 05_obstacles_boxes.png

output/
  ├── offset_map.bin            # 偏移后的地图
  ├── scenarios_new.json        # 新场景文件
  └── sim_map/
      ├── sim_map.bin           # Dreamview 显示用
      └── sim_map.txt           # 调试用
```

## 依赖说明

- **pycryptodome**: 用于解密 raw.json（AES-CBC 解密）
- **numpy**: 数值计算和矩阵运算
- **scipy**: 匈牙利算法实现
- **matplotlib**: 可视化图表生成
- **protobuf**: 地图文件处理（可选）

## 故障排除

### 问题：找不到 Crypto 模块

```bash
pip install pycryptodome
```

### 问题：解密失败

确保 `raw.json` 文件是正确的 Base64 + AES-CBC 加密格式。

### 问题：matplotlib 显示问题

如果在无图形界面环境运行，matplotlib 会自动使用 Agg 后端保存图片。

### 问题：sim_map_generator 未找到

需要先编译 Apollo 的 sim_map_generator 工具：

```bash
cd /apollo_workspace
bazel build //modules/map/tools:sim_map_generator
```

编译完成后，二进制文件位于：
`/apollo_workspace/bazel-bin/modules/map/tools/sim_map_generator`
