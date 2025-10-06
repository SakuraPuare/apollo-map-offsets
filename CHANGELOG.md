# 更新日志

## [1.1.0] - 2025-01-07

### ✅ 新增
- 新增 `input/` 目录用于存放所有输入文件
- 所有脚本默认从 `input/` 目录读取输入文件

### 🔄 变更
- **目录结构调整**：
  ```
  input/           # 新增：输入文件目录
  results/         # 计算结果
  visualizations/  # 可视化图表
  output/          # 最终输出
  ```

- **脚本更新**：
  - `step1_calculate_offset.py` - 默认读取 `input/scenarios.json` 和 `input/data.json`
  - `step2b_visualize_obstacles.py` - 默认读取 `input/scenarios.json` 和 `input/data.json`
  - `step4_create_scenario.py` - 默认路径更新为 `input/` 目录
  - `run_pipeline.py` - 检查 `input/` 目录下的文件

- **文档更新**：
  - `README.md` - 文件结构和使用说明更新
  - `QUICKSTART.md` - 快速开始指南更新
  - `project_structure.txt` - 目录结构更新
  - `SUMMARY.md` - 总结文档更新

### 📝 使用说明

#### 旧版本（v1.0.0）
```bash
# 文件位于项目根目录
./scenarios.json
./data.json
./base_map.bin
```

#### 新版本（v1.1.0）
```bash
# 文件位于 input/ 目录
./input/scenarios.json
./input/data.json
./input/base_map.bin
```

#### 迁移步骤

1. 创建 input 目录：
   ```bash
   mkdir -p input
   ```

2. 移动输入文件：
   ```bash
   mv scenarios.json input/
   mv data.json input/
   mv base_map.bin input/  # 如果有地图文件
   ```

3. 正常运行脚本：
   ```bash
   python3 run_pipeline.py
   ```

### ✨ 优势

- ✅ **更清晰的目录结构** - 输入、输出、结果分离
- ✅ **更好的组织** - 避免根目录文件混乱
- ✅ **更容易管理** - 输入文件集中在一个目录
- ✅ **向后兼容** - 仍可通过命令行参数指定其他路径

---

## [1.0.0] - 2025-01-07

### ✅ 初始版本

- 实现匈牙利算法匹配
- 完整的可视化支持（5张图表）
- Apollo 10.0 HD Map 支持
- 自动化 pipeline
- 完整文档
