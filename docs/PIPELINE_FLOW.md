# Pipeline 工作流程图

## 完整流程

```
用户准备文件
  ├── input/raw.json (加密数据)
  └── input/scenarios.json (场景 + 地图路径)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 0: 解密原始数据                                     │
│   input/raw.json  →  input/data.json                    │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ 自动提取地图路径                                         │
│   scenarios.json → modules/map/data/xxx/base_map.bin    │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 1: 计算偏移量（匈牙利算法）                         │
│   input/scenarios.json + input/data.json                │
│              ↓                                          │
│   results/offset_results.json                           │
│   (Δx, Δy, θ, 匹配对)                                   │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 2: 可视化验证                                       │
│   2a. 匹配分析图表                                       │
│   2b. 障碍物详细分析                                     │
│              ↓                                          │
│   visualizations/*.png (5张图)                          │
└─────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 3: 双线并行处理                                     │
└─────────────────────────────────────────────────────────┘
        │
        ├────────────────────┬────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼

🔸 场景处理线          🔸 地图处理线 (3a)    🔸 地图处理线 (3b)

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Step 4:      │     │ Step 3:      │     │ Step 5:      │
│ 创建新场景    │     │ 应用偏移到    │     │ 生成 sim_map │
│              │     │ 地图         │     │              │
│ scenarios    │     │              │     │ (Dreamview   │
│  + data      │     │ base_map +   │     │  显示用)     │
│  + offset    │     │  offset      │     │              │
│              │     │              │     │ offset_map   │
│      ↓       │     │      ↓       │     │  + downsample│
│ scenarios_   │     │ offset_map.  │     │      ↓       │
│  new.json    │     │  bin         │     │ sim_map.bin  │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                    │
        └────────────────────┴────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  最终输出       │
                    │                │
                    │ 📄 场景:       │
                    │  scenarios_    │
                    │   new.json     │
                    │                │
                    │ 🗺️  地图:      │
                    │  offset_map.   │
                    │   bin          │
                    │  sim_map.bin   │
                    │  sim_map.txt   │
                    └────────────────┘
```

## 数据流详解

### 输入阶段
1. **raw.json** (可选)
   - 加密格式：Base64 + AES-CBC
   - 密钥：SHA256("明月几时有")
   - 解密后 → `data.json`

2. **scenarios.json**
   - 包含场景定义
   - 包含地图路径：`scenario.roadNetwork.logicFile.filepath`
   - 自动提取 → 找到 `base_map.bin`

### 处理阶段

#### Step 1: 偏移计算
- **输入**: scenarios.json, data.json
- **算法**: 匈牙利算法（Hungarian Algorithm）
- **输出**: offset_results.json
  ```json
  {
    "transformation": {
      "translation": { "x": 8993.72, "y": 8996.94 },
      "rotation_degrees": -0.53
    },
    "matches": [ ... ]
  }
  ```

#### Step 2: 可视化
- **2a - 匹配分析**:
  - 原始位置对比
  - 偏移后叠加
  - 向量场
- **2b - 障碍物分析**:
  - 尺寸分布
  - 类型统计
  - 边界框可视化

#### Step 3: 双线处理

**🔸 场景处理线 (Step 4)**
```
scenarios.json (模板)
    +
data.json (新数据)
    +
offset_results.json (偏移)
    ↓
scenarios_new.json
```

**🔸 地图处理线 (Step 3 + 5)**
```
Step 3a: 应用偏移
  base_map.bin
      +
  offset_results.json
      ↓
  offset_map.bin

Step 3b: 生成 sim_map
  offset_map.bin
      ↓
  [sim_map_generator]
      ↓
  sim_map.bin  (Dreamview 显示用)
  sim_map.txt  (调试用)
```

## 关键技术点

### 1. 自动地图路径提取
```python
# 从 scenarios.json 自动提取
scenario.roadNetwork.logicFile.filepath
  → "modules/map/data/xh_2025_gs_contest"
  → /apollo_workspace/modules/map/data/xh_2025_gs_contest/base_map.bin
```

### 2. 并行处理设计
- 场景处理线和地图处理线可并行
- 互不依赖，提高效率
- 用户可选择性运行

### 3. sim_map 生成
- 使用 Apollo 原生工具 `sim_map_generator`
- 下采样优化显示性能
- 支持自定义采样参数

## 输出文件说明

### 计算结果
- `results/offset_results.json` - 完整偏移计算结果

### 可视化
- `visualizations/01_matching_overview.png` - 6子图总览
- `visualizations/02_detailed_matching.png` - 详细匹配
- `visualizations/03_vector_field.png` - 向量场
- `visualizations/04_obstacles_detailed.png` - 障碍物分析
- `visualizations/05_obstacles_boxes.png` - 边界框可视化

### 最终输出
- `output/scenarios_new.json` - 偏移后的场景文件
- `output/offset_map.bin` - 偏移后的地图文件
- `output/sim_map/sim_map.bin` - Dreamview 显示用地图
- `output/sim_map/sim_map.txt` - 地图文本格式（调试用）

## 使用建议

### 完整运行（推荐）
```bash
python3 run_pipeline.py
```
自动处理所有步骤，智能提取地图路径。

### 只生成场景
```bash
python3 step1_calculate_offset.py
python3 step4_create_scenario.py
```

### 只处理地图
```bash
python3 step1_calculate_offset.py
python3 step3_apply_offset_to_map.py <map> output/offset_map.bin
python3 step5_generate_sim_map.py --map_dir output
```

### 调试某个步骤
每个步骤都可独立运行，便于调试和验证。
