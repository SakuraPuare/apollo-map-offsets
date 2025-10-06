# 更新日志 v2.0

## 新功能

### 🆕 Step 0: 自动解密
- 新增 `step0_decrypt_raw_data.py`
- 自动从 `input/raw.json` 解密数据
- 使用 AES-CBC 解密算法（密钥：SHA256("明月几时有")）
- Pipeline 自动检测并执行解密

### 🆕 Step 5: sim_map 生成
- 新增 `step5_generate_sim_map.py`
- 生成 Dreamview 显示用的下采样地图
- 集成 Apollo 原生 `sim_map_generator` 工具
- 可自定义下采样参数

### 🚀 智能地图路径提取
- 自动从 `scenarios.json` 提取地图路径
- 路径位置：`scenario.roadNetwork.logicFile.filepath`
- 自动查找 `base_map.bin`、`base_map.xml` 等文件
- 无需手动输入地图路径

### ⚡ 双线并行处理
- **场景处理线**: 生成偏移后的场景文件
- **地图处理线**:
  - 应用偏移到地图
  - 生成 sim_map
- 两条线并行运行，提高效率

## 改进

### 📝 文档更新
- 新增 `PIPELINE_FLOW.md` - 详细的流程图说明
- 更新 `README.md` - 包含新步骤说明
- 更新 `INSTALL.md` - 添加安装和故障排除
- 更新 `QUICK_REFERENCE.md` - 快速命令参考

### 🔧 Pipeline 优化
- `run_pipeline.py` 全面重构
- 更清晰的步骤划分和进度显示
- 更好的错误处理和用户提示
- 支持跳过可选步骤

## 文件结构变化

### 新增文件
```
step0_decrypt_raw_data.py      # 解密脚本
step5_generate_sim_map.py      # sim_map 生成
requirements.txt               # Python 依赖管理
PIPELINE_FLOW.md               # 流程图文档
CHANGELOG_v2.md                # 本文件
INSTALL.md                     # 安装指南
```

### 修改文件
```
run_pipeline.py                # 重构，支持双线处理
README.md                      # 更新说明
QUICK_REFERENCE.md             # 更新命令
```

## 依赖变化

### 新增 Python 依赖
```
pycryptodome>=3.18.0          # 用于 AES 解密
```

### 新增系统依赖
```
sim_map_generator             # Apollo 工具（需编译）
```

## 使用变化

### v1.x 用法
```bash
# 需要手动准备 data.json 和手动指定地图路径
python3 run_pipeline.py
```

### v2.0 用法
```bash
# 只需准备 raw.json 和 scenarios.json
# Pipeline 自动解密和提取地图路径
python3 run_pipeline.py
```

## 向后兼容性

✅ **完全向后兼容**
- 仍支持直接使用 `data.json`（跳过 step0）
- 仍支持手动指定地图路径
- 所有原有脚本保持不变
- 可选择性使用新功能

## 迁移指南

### 从 v1.x 迁移到 v2.0

1. **安装新依赖**
   ```bash
   pip install pycryptodome
   ```

2. **编译 sim_map_generator**（可选）
   ```bash
   cd /apollo_workspace
   bazel build //modules/map/tools:sim_map_generator
   ```

3. **更新输入文件**（可选）
   - 使用 `raw.json` 代替 `data.json`
   - 确保 `scenarios.json` 包含地图路径

4. **运行 Pipeline**
   ```bash
   python3 run_pipeline.py
   ```

## 性能提升

- ⚡ 双线并行处理：场景和地图处理可同时进行
- 🎯 智能路径提取：减少手动输入，降低错误率
- 📊 自动解密：一步到位，无需手动解密

## 已知问题

1. sim_map_generator 需要先编译
   - 解决方案：参见 INSTALL.md

2. 地图路径提取依赖 scenarios.json 格式
   - 要求：必须包含 `scenario.roadNetwork.logicFile.filepath`

## 下一步计划

- [ ] 支持批量处理多个场景
- [ ] 添加配置文件支持
- [ ] 提供 Docker 镜像
- [ ] 添加单元测试

## 贡献者

- 感谢所有为这个项目做出贡献的人！
