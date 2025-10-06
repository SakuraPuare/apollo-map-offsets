#!/usr/bin/env python3
"""
Step 6: 组织输出为 ready-to-use 格式

输出结构:
output/
├── scenario/
│   └── scenarios_offset.json  (偏移后的场景文件)
└── map/
    └── <map_name>_offset/
        ├── base_map.bin       (偏移后的地图)
        ├── sim_map.bin        (Dreamview显示用)
        ├── routing_map.bin    (从原地图复制)
        └── metaInfo.json      (从原地图复制)
"""

import json
import shutil
from pathlib import Path


def organize_outputs(
    scenarios_file: str = 'output/scenarios_new.json',
    map_file: str = 'output/base_map_offset.bin',
    original_map_dir: str = None,
    output_dir: str = 'output',
    generate_maps: bool = True
):
    """
    组织输出文件为 ready-to-use 格式

    Args:
        scenarios_file: 偏移后的场景文件
        map_file: 偏移后的地图文件
        original_map_dir: 原始地图目录（用于复制 routing_map 和 metaInfo）
        output_dir: 输出根目录
        generate_maps: 是否生成 sim_map 和 routing_map
    """
    output_path = Path(output_dir)

    print("\n" + "="*70)
    print("Step 6: 组织输出文件")
    print("="*70)

    # 创建输出目录结构
    scenario_dir = output_path / 'scenario'
    map_base_dir = output_path / 'map'

    scenario_dir.mkdir(parents=True, exist_ok=True)
    map_base_dir.mkdir(parents=True, exist_ok=True)

    # 1. 处理场景文件
    print(f"\n📦 处理场景文件...")
    scenarios_path = Path(scenarios_file)
    if scenarios_path.exists():
        target_scenario = scenario_dir / 'scenarios_offset.json'
        shutil.copy2(scenarios_path, target_scenario)
        print(f"  ✅ 场景文件: {target_scenario}")
    else:
        print(f"  ⚠️  场景文件不存在: {scenarios_path}")

    # 2. 处理地图文件
    print(f"\n🗺️  处理地图文件...")

    # 从 scenarios.json 读取原始地图路径
    if original_map_dir is None:
        with open('input/scenarios.json', 'r') as f:
            scenario_data = json.load(f)

        map_path = scenario_data.get('scenario', {}).get(
            'roadNetwork', {}
        ).get('logicFile', {}).get('filepath', '')

        if map_path:
            original_map_dir = Path('/apollo_workspace') / map_path
    else:
        original_map_dir = Path(original_map_dir)

    print(f"  原始地图目录: {original_map_dir}")

    # 确定地图名称
    if original_map_dir.exists():
        map_name = original_map_dir.name
    else:
        map_name = 'unknown_map'

    # 创建偏移后的地图目录
    offset_map_dir = map_base_dir / f'{map_name}_offset'
    offset_map_dir.mkdir(parents=True, exist_ok=True)

    print(f"  目标地图目录: {offset_map_dir}")

    # 复制 base_map.bin
    map_path = Path(map_file)
    if map_path.exists():
        target_base_map = offset_map_dir / 'base_map.bin'
        shutil.copy2(map_path, target_base_map)
        print(f"  ✅ base_map.bin ({map_path.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print(f"  ⚠️  地图文件不存在: {map_path}")

    # 生成 sim_map.bin 和 routing_map.bin（如果需要）
    if generate_maps:
        print(f"\n  🔧 生成地图文件...")

        # 使用统一的 map_generator 模块
        import subprocess
        try:
            result = subprocess.run(
                [
                    'python3', 'src/map_generator.py',
                    '--map_dir', str(offset_map_dir),
                    '--map_filename', 'base_map.bin'
                ],
                capture_output=True,
                text=True,
                timeout=600
            )

            # 检查生成的文件
            sim_map_path = offset_map_dir / 'sim_map.bin'
            routing_map_path = offset_map_dir / 'routing_map.bin'

            if sim_map_path.exists():
                print(f"  ✅ sim_map.bin ({sim_map_path.stat().st_size / 1024 / 1024:.2f} MB)")

            if routing_map_path.exists():
                print(f"  ✅ routing_map.bin ({routing_map_path.stat().st_size / 1024 / 1024:.2f} MB)")

        except Exception as e:
            print(f"  ⚠️  地图文件生成失败: {e}")
    else:
        # 不生成，从原地图复制
        sim_map_source = output_path / 'sim_map.bin'
        if sim_map_source.exists():
            target_sim_map = offset_map_dir / 'sim_map.bin'
            shutil.copy2(sim_map_source, target_sim_map)
            print(f"  ✅ sim_map.bin ({sim_map_source.stat().st_size / 1024 / 1024:.2f} MB)")

    # 复制 metaInfo.json
    if original_map_dir.exists():
        meta_info_source = original_map_dir / 'metaInfo.json'
        if meta_info_source.exists():
            target_meta = offset_map_dir / 'metaInfo.json'
            shutil.copy2(meta_info_source, target_meta)
            print(f"  ✅ metaInfo.json (从原地图复制)")

    # 3. 生成使用说明
    readme_content = f"""# Apollo Map Offsets - 输出文件

## 目录结构

```
output/
├── scenario/
│   └── scenarios_offset.json    # 偏移后的场景文件（ready to use）
└── map/
    └── {map_name}_offset/       # 偏移后的地图目录（ready to use）
        ├── base_map.bin          # 偏移后的地图文件
        ├── sim_map.bin           # Dreamview 显示用（如果已生成）
        ├── routing_map.bin       # 路由地图（从原地图复制）
        └── metaInfo.json         # 元信息（从原地图复制）
```

## 使用方法

### 1. 使用偏移后的场景

直接上传 `scenario/scenarios_offset.json` 到 Dreamview。

### 2. 使用偏移后的地图

将 `map/{map_name}_offset/` 目录复制到 Apollo 的地图目录：

```bash
# 复制到 Apollo 地图目录
cp -r output/map/{map_name}_offset /apollo_workspace/modules/map/data/

# 或者创建符号链接
ln -s $(pwd)/output/map/{map_name}_offset /apollo_workspace/modules/map/data/
```

然后在 Dreamview 中选择 `{map_name}_offset` 地图。

### 3. 完整测试流程

```bash
# 1. 启动 Dreamview
bash scripts/bootstrap.sh

# 2. 打开浏览器访问 Dreamview
http://localhost:8888

# 3. 选择地图: {map_name}_offset
# 4. 加载场景: scenarios_offset.json
# 5. 开始测试
```

## 文件说明

- **base_map.bin**: 偏移后的 OpenDRIVE 格式地图文件
- **sim_map.bin**: 简化版地图，用于 Dreamview 可视化显示
- **routing_map.bin**: 路由地图，用于路径规划
- **metaInfo.json**: 地图元信息，包含坐标范围、缩放级别等

## 注意事项

1. 确保偏移量已正确应用到地图和场景
2. 如果 sim_map.bin 不存在，Dreamview 可能无法正确显示地图
3. routing_map.bin 使用原地图的路由信息（未应用偏移）
4. 如需重新生成 routing_map，请使用 Apollo 的 routing_map_generator 工具

## 生成信息

- 原始地图: {original_map_dir}
- 输出地图: {offset_map_dir}
- 生成时间: {Path(__file__).stat().st_mtime}
"""

    readme_path = output_path / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"\n📝 使用说明: {readme_path}")

    # 4. 显示总结
    print("\n" + "="*70)
    print("✅ 输出文件组织完成!")
    print("="*70)
    print(f"\n📁 输出目录: {output_path.absolute()}")
    print(f"\n场景文件:")
    print(f"  - {scenario_dir / 'scenarios_offset.json'}")
    print(f"\n地图目录:")
    print(f"  - {offset_map_dir}/")
    print(f"    - base_map.bin")
    if (offset_map_dir / 'sim_map.bin').exists():
        print(f"    - sim_map.bin")
    if (offset_map_dir / 'routing_map.bin').exists():
        print(f"    - routing_map.bin")
    if (offset_map_dir / 'metaInfo.json').exists():
        print(f"    - metaInfo.json")

    print(f"\n💡 使用方法请查看: {readme_path}")

    return str(offset_map_dir)


def main():
    """主函数"""
    try:
        organize_outputs()
        return 0
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
