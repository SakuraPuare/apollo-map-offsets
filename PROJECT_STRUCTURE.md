# 项目结构 (Project Structure)

## 最终整理后的目录结构

```
apollo-map-offsets/
├── README.md                    # 主文档 - 快速开始、完整指南
├── run_pipeline.py              # 主入口 - 一键运行完整流程
├── requirements.txt             # Python 依赖
│
├── src/                         # 核心脚本 (5个步骤脚本 + 2个模块)
│   ├── step0_decrypt_raw_data.py       # Step 0: 解密原始数据 (可选)
│   ├── step1_calculate_offset.py       # Step 1: 计算偏移量
│   ├── step2_apply_offset_to_map.py    # Step 2: 应用偏移到地图
│   ├── step3_create_scenario.py        # Step 3: 创建新场景
│   ├── step4_organize_outputs.py       # Step 4: 组织输出
│   ├── visualize.py                    # 统一可视化模块
│   ├── map_generator.py                # 地图辅助文件生成模块
│   └── font_helper.py                  # 字体辅助
│
├── utils/                       # 工具文件
│   ├── simhei.ttf              # 中文字体
│   └── test_font.py            # 字体测试工具
│
├── docs/                        # 文档目录
│   ├── CHANGELOG_v2.md         # 更新日志
│   ├── INSTALL.md              # 安装说明
│   ├── PIPELINE_FLOW.md        # 详细流程说明
│   ├── QUICK_REFERENCE.md      # 快速参考
│   ├── README_FONT.md          # 字体配置说明
│   └── REFACTORING_NOTES.md    # 重构说明
│
├── input/                       # 输入数据目录
│   ├── scenarios.json          # 原始场景文件
│   ├── raw.json                # 加密原始数据 (可选)
│   └── data.json               # 解密后的障碍物数据
│
├── results/                     # 计算结果目录
│   └── offset_results.json     # 偏移量和匹配结果
│
├── visualizations/              # 可视化图表目录
│   ├── 01_matching_overview.png      # 匹配总览 (6子图)
│   ├── 02_vector_field.png           # 向量场
│   └── 03_obstacles_comparison.png   # 障碍物对比 (3子图)
│
└── output/                      # 最终输出目录 (Ready-to-Use)
    ├── scenario/
    │   └── scenarios_offset.json     # 偏移后的场景
    └── map/
        └── <map_name>_offset/        # 偏移后的地图目录
            ├── base_map.bin          # 偏移后的地图
            ├── sim_map.bin           # Dreamview 显示用
            ├── routing_map.bin       # 路由地图
            └── metaInfo.json         # 元信息
```

## Pipeline 流程

```
┌─────────────────────────────────────────────────────────────┐
│  Step 0: 解密原始数据 (可选)                                 │
│  input/raw.json → input/data.json                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 计算偏移量                                          │
│  匈牙利算法匹配障碍物 → results/offset_results.json          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: 生成可视化图表                                      │
│  visualizations/*.png (3个高质量图表)                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: 应用偏移 (并行处理)                                 │
│  ┌────────────────────┐  ┌─────────────────────┐            │
│  │ 场景处理线         │  │ 地图处理线          │            │
│  │ step3_create       │  │ step2_apply_offset  │            │
│  │ _scenario.py       │  │ _to_map.py          │            │
│  └────────────────────┘  └─────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 4: 组织输出为 Ready-to-Use 格式                        │
│  生成 sim_map, routing_map 并整理到 output/                 │
└─────────────────────────────────────────────────────────────┘
```

## 文件编号说明

### Step 文件 (连续编号 0-4)

- **step0**: 数据预处理 (解密)
- **step1**: 核心计算 (偏移计算)
- **step2**: 地图变换 (应用偏移到地图)
- **step3**: 场景生成 (创建新场景)
- **step4**: 输出整理 (组织为最终格式)

### 独立模块

- **visualize.py**: 在 Step 1 和 Step 2 之间运行，生成可视化
- **map_generator.py**: 被 Step 4 调用，生成 sim_map 和 routing_map

## 重构成果

### 代码优化
- ✅ 合并可视化模块: 25KB → 16KB (-36%)
- ✅ 合并地图生成: 14KB → 8KB (-43%)
- ✅ 总代码量: ~85KB → ~65KB (-24%)

### 目录整理
- ✅ 根目录文件: 15+ → 3 (-80%)
- ✅ 总文件数: 32 → 24 (-25%)
- ✅ Python 脚本: 12 → 8 (-33%)

### 流程简化
- ✅ Pipeline 步骤: 9步 → 5步 (0-4)
- ✅ 编号连续，逻辑清晰
- ✅ 并行处理，提高效率

---

**最后更新**: 2025-10-07
