# 地图和场景偏移校准工作流

自动化计算两个场景之间的坐标偏移，并应用到地图和场景文件。

## 📋 目录

- [概述](#概述)
- [文件结构](#文件结构)
- [快速开始](#快速开始)
- [详细步骤](#详细步骤)
- [输出说明](#输出说明)
- [常见问题](#常见问题)

---

## 概述

本工具链用于处理 Apollo 自动驾驶场景数据的坐标对齐问题。主要功能：

1. **计算偏移量**：使用匈牙利算法匹配两个场景中的障碍物，计算坐标偏移
2. **可视化验证**：生成多种可视化图表验证匹配质量
3. **应用偏移**：将计算的偏移应用到地图文件
4. **生成场景**：根据新数据创建 OpenSCENARIO 格式的场景文件

### 核心算法

**匈牙利算法（Hungarian Algorithm）**
- 用于解决二分图最优匹配问题
- 成本函数 = 坐标距离 + 尺寸差异惩罚
- 自动找到全局最优的障碍物配对

---

## 文件结构

```
.
├── step1_calculate_offset.py      # 步骤1: 计算偏移量
├── step2a_visualize_matching.py   # 步骤2a: 匹配可视化
├── step2b_visualize_obstacles.py  # 步骤2b: 障碍物可视化
├── step3_apply_offset_to_map.py   # 步骤3: 应用偏移到地图
├── step4_create_scenario.py       # 步骤4: 创建新场景
├── run_pipeline.py                # 主运行脚本（推荐）
│
├── input/                         # 输入文件目录
│   ├── scenarios.json             # 原始场景文件
│   ├── data.json                  # 障碍物数据
│   └── base_map.bin               # 地图文件（可选）
│
├── results/                       # 计算结果
│   └── offset_results.json        # 偏移量和匹配结果
│
├── visualizations/                # 可视化图表
│   ├── 01_matching_overview.png   # 匹配总览
│   ├── 02_detailed_matching.png   # 详细匹配
│   ├── 03_vector_field.png        # 向量场
│   ├── 04_obstacles_detailed.png  # 障碍物详细分析
│   └── 05_obstacles_boxes.png     # 障碍物边界框
│
└── output/                        # 最终输出
    ├── base_map_offset.bin        # 偏移后的地图
    └── scenarios_new.json         # 新场景文件
```

---

## 快速开始

### 前置要求

```bash
# Python 3.7+
python3 --version

# 安装依赖
uv venv
uv pip install numpy scipy matplotlib
```

### 一键运行（推荐）

```bash
python3 run_pipeline.py
```

这会：
1. 检查必需文件
2. 依次执行所有步骤
3. 生成完整的输出

### 输入文件准备

确保 `input/` 目录有以下文件：
- `input/scenarios.json` - OpenSCENARIO 格式的场景文件
- `input/data.json` - 包含障碍物数据的 JSON 文件
- `input/base_map.bin` - Apollo HD Map 文件（可选）

---

## 详细步骤

### 步骤 1: 计算偏移量

使用匈牙利算法匹配障碍物并计算偏移。

```bash
python3 step1_calculate_offset.py
```

**输出：**
- `results/offset_results.json` - 包含：
  - 偏移量 (Δx, Δy)
  - 旋转角度 (θ)
  - 匹配对列表
  - 精度统计

**示例结果：**
```json
{
  "transformation": {
    "translation": {
      "x": 8993.72,
      "y": 8996.94
    },
    "rotation_degrees": -0.53
  },
  "accuracy": {
    "num_matches": 36,
    "mean_error": 3.73,
    "std_error": 1.46
  }
}
```

---

### 步骤 2: 生成可视化

#### 2a. 匹配可视化

```bash
python3 step2a_visualize_matching.py
```

**生成图表：**
- `visualizations/01_matching_overview.png` - 6子图总览
  - 原始位置对比
  - 偏移后对比
  - 误差热图
  - 误差直方图
  - 向量分布
  - 统计信息

- `visualizations/02_detailed_matching.png` - 前10个匹配点详细视图
- `visualizations/03_vector_field.png` - 变换向量场

#### 2b. 障碍物可视化

```bash
python3 step2b_visualize_obstacles.py
```

**生成图表：**
- `visualizations/04_obstacles_detailed.png` - 障碍物详细分析
  - Scenarios 原始场景
  - Data 场景
  - 偏移后叠加对比
  - 尺寸分布
  - 类型统计
  - 详细信息

- `visualizations/05_obstacles_boxes.png` - 带边界框和朝向箭头

---

### 步骤 3: 应用偏移到地图

将计算的偏移应用到 Apollo HD Map。

```bash
python3 step3_apply_offset_to_map.py input/base_map.bin output/base_map_offset.bin --format binary
```

**参数：**
- `input_map` - 输入地图文件路径
- `output_map` - 输出地图文件路径
- `--format` - 输出格式 (text/binary)
- `--offset-file` - 偏移结果文件（默认: results/offset_results.json）
- `--offset-x`, `--offset-y`, `--rotation` - 手动指定偏移量（可选）

**处理的地图元素：**
- Lanes（车道）
- Roads（道路）
- Junctions（路口）
- Crosswalks（人行横道）
- Traffic Signals（信号灯）
- Stop Signs（停止标志）
- 其他地图元素...

---

### 步骤 4: 创建新场景

根据 data.json 创建新的 OpenSCENARIO 场景文件。

```bash
# 只包含匹配的障碍物（默认）
python3 step4_create_scenario.py -o output/scenarios_new.json

# 包含所有障碍物
python3 step4_create_scenario.py -o output/scenarios_all.json --all-objects
```

**参数：**
- `--template`, `-t` - 场景模板（默认: scenarios.json）
- `--data`, `-d` - 障碍物数据（默认: data.json）
- `--output`, `-o` - 输出文件（默认: scenarios_new.json）
- `--match-results`, `-m` - 匹配结果文件
- `--all-objects` - 包含所有障碍物

**特性：**
- ✅ 连续的障碍物 ID（1, 2, 3...）
- ✅ 统一的命名（vehicle_1, object_2...）
- ✅ 保留原始 ID 在 properties 中
- ✅ 自动类型映射（VEHICLE → vehicle）

---

## 输出说明

### results/offset_results.json

完整的偏移计算结果：

```json
{
  "transformation": {
    "translation": { "x": 8993.72, "y": 8996.94 },
    "rotation_radians": -0.009190,
    "rotation_degrees": -0.53,
    "rotation_matrix": [[...], [...]]
  },
  "accuracy": {
    "num_matches": 36,
    "mean_error": 3.73,
    "median_error": 3.45,
    "max_error": 6.40,
    "std_error": 1.46
  },
  "simple_offset_stats": {
    "dx_mean": 8993.72,
    "dx_std": 2.79,
    "dy_mean": 8996.94,
    "dy_std": 2.90
  },
  "matched_pairs": [
    {
      "src_index": 0,
      "dst_index": 1,
      "src_id": "8396",
      "dst_id": "8523",
      "matching_cost": 10.73,
      "transform_error": 5.49
    },
    ...
  ]
}
```

### visualizations/*.png

5张高分辨率（300 DPI）可视化图表，用于验证匹配质量和偏移计算结果。

### output/scenarios_new.json

新的 OpenSCENARIO 场景文件：

```json
{
  "scenario": {
    "entities": {
      "scenarioObjects": [
        {
          "name": "vehicle_1",
          "id": "1",
          "entityObject": {
            "vehicle": {
              "boundingBox": {
                "dimensions": {
                  "length": 0.2,
                  "width": 3.0,
                  "height": 1.0
                }
              },
              "properties": {
                "property": [
                  { "name": "original_id", "value": "8523" }
                ]
              }
            }
          }
        }
      ]
    },
    "storyboard": {
      "init": {
        "actions": {
          "privates": [
            {
              "entityRef": { "entityRef": "1" },
              "privateActions": [
                {
                  "teleportAction": {
                    "position": {
                      "worldPosition": {
                        "x": 432422.39,
                        "y": 4447970.22,
                        "h": 3.14159
                      }
                    }
                  }
                }
              ]
            }
          ]
        }
      }
    }
  }
}
```

---

## 常见问题

### Q: 如何只运行某一步？

直接运行对应的脚本：
```bash
python3 step1_calculate_offset.py
python3 step2a_visualize_matching.py
# ... 等
```

### Q: 匹配精度如何？

查看 `results/offset_results.json` 中的 `accuracy` 字段：
- `mean_error` < 5m：优秀
- `mean_error` 5-10m：良好
- `mean_error` > 10m：需要检查

### Q: 如何手动指定偏移量？

```bash
python3 step3_apply_offset_to_map.py \
  input.bin output.bin \
  --offset-x 9000.0 \
  --offset-y 9000.0 \
  --rotation 0.0 \
  --format binary
```

### Q: 为什么有些障碍物没有匹配？

可能原因：
1. data.json 中有新增的障碍物
2. 坐标差异超过阈值（默认 50m）
3. 尺寸差异过大

检查 `results/offset_results.json` 中的 `unmatched` 字段。

### Q: 支持哪些地图格式？

- **输入**：Apollo HD Map (text .txt 或 binary .bin)
- **输出**：同上（可指定格式）
- **版本**：Apollo 10.0+

### Q: 可视化图片中文乱码怎么办？

脚本已配置 Mac 中文字体（Arial Unicode MS）。如果仍有问题，编辑脚本：
```python
plt.rcParams['font.sans-serif'] = ['你的字体名称']
```

---

## 技术细节

### 匈牙利算法

使用 `scipy.optimize.linear_sum_assignment` 实现：

1. **成本矩阵构建**：
   ```python
   cost = 坐标距离 + 100 × 尺寸差异
   ```

2. **初始偏移估计**：
   ```python
   offset = 目标中心 - 源中心
   ```

3. **最优匹配**：
   找到使总成本最小的一对一匹配

4. **变换计算**：
   使用 SVD 求解旋转矩阵

### 坐标系统

- **scenarios.json**: 原始坐标系
- **data.json**: 偏移后的坐标系
- **变换**: data = R × scenarios + t
  - R: 旋转矩阵
  - t: 平移向量

---

## 许可证

基于 Apollo 项目，遵循 Apache License 2.0

---

## 更新日志

### v1.0.0 (2025-01)
- ✅ 初始版本
- ✅ 匈牙利算法匹配
- ✅ 完整的可视化支持
- ✅ Apollo 10.0 地图支持
- ✅ 自动化 pipeline

---

**💡 提示**: 强烈建议先查看可视化图表验证匹配质量，再应用到实际地图！
