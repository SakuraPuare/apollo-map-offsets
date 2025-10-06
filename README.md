# Apollo Map Offsets - 地图和场景偏移校准工具

自动化计算两个场景之间的坐标偏移，并应用到地图和场景文件。

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [工作流程](#工作流程)
- [使用说明](#使用说明)
- [配置选项](#配置选项)
- [常见问题](#常见问题)

---

## 概述

本工具链用于处理 Apollo 自动驾驶场景数据的坐标对齐问题。

### 核心功能

1. **偏移计算**: 使用匈牙利算法自动匹配障碍物并计算坐标偏移
2. **可视化验证**: 生成多种图表验证匹配质量
3. **地图变换**: 将偏移应用到 Apollo HD Map
4. **场景生成**: 创建新的 OpenSCENARIO 场景文件
5. **地图辅助**: 自动生成 sim_map 和 routing_map

### 核心算法

**匈牙利算法（Hungarian Algorithm）**
- 用于解决二分图最优匹配问题
- 成本函数 = 坐标距离 + 尺寸差异惩罚
- 自动找到全局最优的障碍物配对

---

## 快速开始

### 前置要求

```bash
# Python 3.7+
python3 --version

# 安装依赖
pip install -r requirements.txt
```

### 准备输入文件

1. **必需文件**:
   - `input/scenarios.json` - OpenSCENARIO 格式的场景文件（包含地图路径）

2. **数据源（二选一）**:
   - `input/raw.json` - 加密的原始数据（推荐）
   - `input/data.json` - 已解密的障碍物数据

### 一键运行

```bash
python3 run_pipeline.py
```

Pipeline 会自动执行所有步骤：
- **Step 0**: 检测并解密 `raw.json`（如果存在）
- **Step 1**: 计算偏移量
- **Step 2**: 生成可视化图表
- **Step 3**: 应用偏移到地图和场景（并行处理）
- **Step 4**: 生成 sim_map、routing_map 并组织为 ready-to-use 格式

---

## 项目结构

```
apollo-map-offsets/
├── README.md                    # 本文档
├── requirements.txt             # Python 依赖
├── run_pipeline.py              # 主运行脚本
│
├── src/                         # 核心脚本
│   ├── step0_decrypt_raw_data.py       # 解密原始数据
│   ├── step1_calculate_offset.py       # 计算偏移量
│   ├── step2_apply_offset_to_map.py    # 应用偏移到地图
│   ├── step3_create_scenario.py        # 创建新场景
│   ├── step4_organize_outputs.py       # 组织输出
│   ├── visualize.py                    # 统一可视化模块
│   ├── map_generator.py                # 地图辅助文件生成
│   └── font_helper.py                  # 字体辅助
│
├── utils/                       # 工具文件
│   ├── simhei.ttf              # 中文字体
│   └── test_font.py            # 字体测试
│
├── docs/                        # 文档
│   ├── CHANGELOG_v2.md         # 更新日志
│   ├── INSTALL.md              # 安装说明
│   ├── PIPELINE_FLOW.md        # 详细流程说明
│   ├── QUICK_REFERENCE.md      # 快速参考
│   └── README_FONT.md          # 字体配置说明
│
├── input/                       # 输入文件
│   ├── scenarios.json          # 原始场景
│   ├── raw.json                # 加密原始数据（可选）
│   └── data.json               # 解密后的数据
│
├── results/                     # 计算结果
│   └── offset_results.json     # 偏移量和匹配结果
│
├── visualizations/              # 可视化图表
│   ├── 01_matching_overview.png      # 匹配总览（6子图）
│   ├── 02_vector_field.png           # 向量场
│   └── 03_obstacles_comparison.png   # 障碍物对比（3子图）
│
└── output/                      # 最终输出
    ├── scenario/
    │   └── scenarios_offset.json     # 偏移后的场景
    └── map/
        └── <map_name>_offset/        # 偏移后的地图目录
            ├── base_map.bin          # 偏移后的地图
            ├── sim_map.bin           # Dreamview 显示用
            ├── routing_map.bin       # 路由地图
            └── metaInfo.json         # 元信息
```

---

## 工作流程

### Step 0: 解密原始数据（可选）

如果有加密的 `input/raw.json`：

```bash
python3 src/step0_decrypt_raw_data.py
```

**输出**: `input/data.json`

### Step 1: 计算偏移量

使用匈牙利算法匹配障碍物并计算偏移：

```bash
python3 src/step1_calculate_offset.py
```

**输出**: `results/offset_results.json`

示例结果：
```json
{
  "transformation": {
    "translation": {"x": 8993.72, "y": 8996.94},
    "rotation_degrees": -0.53
  },
  "accuracy": {
    "num_matches": 36,
    "mean_error": 3.73,
    "std_error": 1.46
  }
}
```

### Step 2: 生成可视化

```bash
python3 src/visualize.py
```

**输出**:
- `visualizations/01_matching_overview.png` - 6子图总览（原始对比、偏移后、误差热图等）
- `visualizations/02_vector_field.png` - 变换向量场
- `visualizations/03_obstacles_comparison.png` - 障碍物对比（3子图）

### Step 3a: 应用偏移到地图

```bash
python3 src/step2_apply_offset_to_map.py \
  /path/to/input/base_map.bin \
  output/base_map_offset.bin \
  --format binary
```

**处理的地图元素**:
- Lanes（车道）
- Roads（道路）
- Junctions（路口）
- Crosswalks（人行横道）
- Traffic Signals（信号灯）
- Stop Signs（停止标志）

### Step 3b: 创建新场景

```bash
# 只包含匹配的障碍物（默认）
python3 src/step3_create_scenario.py -o output/scenarios_new.json

# 包含所有障碍物
python3 src/step3_create_scenario.py -o output/scenarios_all.json --all-objects
```

**特性**:
- ✅ 连续的障碍物 ID（1, 2, 3...）
- ✅ 统一的命名（vehicle_1, object_2...）
- ✅ 保留原始 ID 在 properties 中
- ✅ 自动类型映射

### Step 4: 生成地图辅助文件并组织输出

```bash
# 自动生成 sim_map 和 routing_map，并组织为 ready-to-use 格式
python3 src/step4_organize_outputs.py
```

或使用统一的地图生成工具：

```bash
python3 src/map_generator.py --map_dir output/map/my_map
```

**输出**:
- `output/scenario/scenarios_offset.json`
- `output/map/<map_name>_offset/` - 完整的地图目录

---

## 使用说明

### 使用输出文件

#### 1. 复制地图到 Apollo

```bash
cp -r output/map/<map_name>_offset /apollo_workspace/modules/map/data/
```

#### 2. 在 Dreamview 中使用

1. 启动 Dreamview: `bash scripts/bootstrap.sh`
2. 打开浏览器: http://localhost:8888
3. 选择地图: `<map_name>_offset`
4. 加载场景: `scenarios_offset.json`

### 单独运行某个步骤

```bash
# 只计算偏移
python3 src/step1_calculate_offset.py

# 只生成可视化
python3 src/visualize.py

# 只生成 sim_map
python3 src/map_generator.py --map_dir output/map/my_map --no-routing
```

### 手动指定偏移量

```bash
python3 src/step2_apply_offset_to_map.py \
  input.bin output.bin \
  --offset-x 9000.0 \
  --offset-y 9000.0 \
  --rotation 0.0 \
  --format binary
```

---

## 配置选项

### 偏移计算参数

编辑 `src/step1_calculate_offset.py`:

```python
matches = match_obstacles_hungarian(
    scenarios_obs, data_obs,
    initial_offset=(dx_init, dy_init),
    max_distance=50.0,      # 最大匹配距离（米）
    dimension_weight=100.0  # 尺寸差异惩罚权重
)
```

### 可视化参数

编辑 `src/visualize.py` 或通过命令行参数：

```bash
python3 src/visualize.py \
  --results results/offset_results.json \
  --output visualizations
```

### 地图生成参数

```bash
python3 src/map_generator.py \
  --map_dir output/map/my_map \
  --map_filename base_map.bin \
  --no-sim              # 不生成 sim_map
  --no-routing          # 不生成 routing_map
```

---

## 常见问题

### Q: 如何判断匹配质量？

查看 `results/offset_results.json` 中的 `accuracy` 字段：
- `mean_error` < 5m：优秀 ✅
- `mean_error` 5-10m：良好 ⚠️
- `mean_error` > 10m：需要检查 ❌

同时查看 `visualizations/` 中的图表进行可视化验证。

### Q: 为什么有些障碍物没有匹配？

可能原因：
1. data.json 中有新增的障碍物
2. 坐标差异超过阈值（默认 50m）
3. 尺寸差异过大

检查 `results/offset_results.json` 中的 `unmatched` 字段。

### Q: sim_map 或 routing_map 生成失败？

**sim_map 失败**:
```bash
# 需要先编译
cd /apollo_workspace
bazel build //modules/map/tools:sim_map_generator
```

**routing_map 失败**:
```bash
# 需要编译 routing 模块
bazel build //modules/routing/...
```

### Q: 可视化图片中文乱码？

脚本已自动配置中文字体。如果仍有问题：

1. 检查字体文件: `utils/simhei.ttf` 是否存在
2. 测试字体: `python3 utils/test_font.py`
3. 查看详细说明: `docs/README_FONT.md`

### Q: 支持哪些地图格式？

- **输入**: Apollo HD Map (text `.txt` 或 binary `.bin`)
- **输出**: 同上（可通过 `--format` 指定）
- **版本**: Apollo 10.0+

---

## 技术细节

### 匈牙利算法实现

```python
# 1. 构建成本矩阵
cost = 坐标距离 + 100 × 尺寸差异

# 2. 初始偏移估计
offset = 目标中心 - 源中心

# 3. 最优匹配
src_indices, dst_indices = linear_sum_assignment(cost_matrix)

# 4. 变换计算（SVD求解旋转矩阵）
R, t = solve_transform(matched_points)
```

### 坐标变换

```
data_pos = R × scenarios_pos + t

其中:
  R - 旋转矩阵（2×2）
  t - 平移向量（dx, dy）
```

---

## 更新日志

详见 `docs/CHANGELOG_v2.md`

### v2.0 (2025-10)
- ✅ 重构代码，避免重复
- ✅ 统一可视化模块
- ✅ 统一地图生成模块
- ✅ 优化目录结构
- ✅ 简化文档

### v1.0 (2025-01)
- ✅ 初始版本
- ✅ 匈牙利算法匹配
- ✅ 完整可视化支持
- ✅ Apollo 10.0 地图支持

---

## 许可证

基于 Apollo 项目，遵循 Apache License 2.0

---

## 相关文档

- [详细流程说明](docs/PIPELINE_FLOW.md)
- [快速参考](docs/QUICK_REFERENCE.md)
- [安装说明](docs/INSTALL.md)
- [字体配置](docs/README_FONT.md)

---

**💡 提示**: 强烈建议先查看可视化图表验证匹配质量，再应用到实际地图！
