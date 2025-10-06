#!/usr/bin/env python3
"""
地图和场景偏移校准工作流 - 主运行脚本
完整的 pipeline，从偏移计算到最终输出

工作流程:
  Step 0: 解密原始数据 (如果有 raw.json)
  Step 1: 计算偏移量
  Step 2: 可视化验证
  Step 3: 应用偏移 (场景 + 地图)
  Step 4: 组织输出为 Ready-to-Use 格式
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path


def print_step(step_num: int, title: str):
    """打印步骤标题"""
    print("\n" + "="*70)
    print(f"步骤 {step_num}: {title}")
    print("="*70 + "\n")


def run_command(cmd: list, description: str):
    """运行命令并检查结果"""
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"\n❌ 错误: {description} 失败")
        return False

    print(f"\n✅ {description} 完成")
    return True


def check_files_exist(*files):
    """检查文件是否存在"""
    missing = []
    for f in files:
        if not Path(f).exists():
            missing.append(f)

    if missing:
        print("❌ 缺少以下必需文件:")
        for f in missing:
            print(f"  - {f}")
        return False
    return True


def extract_map_info_from_scenario(scenario_file: str) -> tuple:
    """
    从 scenarios.json 提取地图信息

    返回: (scenario_id, map_path)
    """
    try:
        with open(scenario_file, 'r') as f:
            scenario_data = json.load(f)

        # 提取场景 ID
        scenario_id = scenario_data.get('id', 'unknown')

        # 提取地图路径
        map_path = scenario_data.get('scenario', {}).get(
            'roadNetwork', {}
        ).get('logicFile', {}).get('filepath', '')

        if not map_path:
            return scenario_id, None

        # 构造完整路径
        base_path = Path('/apollo_workspace') / map_path

        # 尝试几种可能的地图文件名
        for map_filename in ['base_map.bin', 'base_map.xml', 'base_map.txt']:
            full_path = base_path / map_filename
            if full_path.exists():
                return scenario_id, str(full_path)

        # 如果没找到具体文件，但目录存在，返回目录
        if base_path.exists():
            return scenario_id, str(base_path)

        return scenario_id, None

    except Exception as e:
        print(f"⚠️  警告: 无法从 scenarios.json 提取信息: {e}")
        return 'unknown', None


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='地图和场景偏移校准工作流',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自动模式 - 从 scenarios.json 自动检测地图
  python3 run_pipeline.py

  # 指定地图文件
  python3 run_pipeline.py --map-file /path/to/base_map.bin

  # 跳过地图处理，只处理场景
  python3 run_pipeline.py --skip-map

  # 场景包含所有障碍物（默认只包含匹配的）
  python3 run_pipeline.py --all-objects
        """
    )

    parser.add_argument(
        '--map-file',
        type=str,
        help='地图文件路径 (默认: 自动从 scenarios.json 提取)'
    )

    parser.add_argument(
        '--skip-map',
        action='store_true',
        help='跳过地图处理，只处理场景'
    )

    parser.add_argument(
        '--all-objects',
        action='store_true',
        help='场景包含所有障碍物 (默认: 只包含匹配的障碍物)'
    )

    parser.add_argument(
        '--skip-decrypt',
        action='store_true',
        help='跳过解密步骤 (即使 raw.json 存在)'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    print("""
╔═══════════════════════════════════════════════════════════════════╗
║         地图和场景偏移校准工作流 (Map Offset Pipeline)            ║
║                                                                   ║
║  自动化执行从偏移计算到地图/场景生成的完整流程                      ║
║                                                                   ║
║  处理流程:                                                        ║
║    Step 0: 解密原始数据 (可选)                                    ║
║    Step 1: 计算偏移量                                             ║
║    Step 2: 生成可视化图表                                         ║
║    Step 3: 应用偏移 (场景 + 地图)                                 ║
║    Step 4: 组织输出为 Ready-to-Use 格式                           ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    # Step 0: 解密原始数据 (如果 raw.json 存在)
    if not args.skip_decrypt and Path('input/raw.json').exists() and not Path('input/data.json').exists():
        print_step(0, "解密原始数据")
        if not run_command(
            ['python3', 'src/step0_decrypt_raw_data.py'],
            "解密 raw.json"
        ):
            return 1

    # 检查必需文件
    print("检查必需文件...")
    if not check_files_exist('input/scenarios.json', 'input/data.json'):
        print("\n请确保以下文件存在于 input/ 目录:")
        print("  - input/scenarios.json (原始场景)")
        print("  - input/data.json (障碍物数据)")
        print("\n或者提供:")
        print("  - input/raw.json (加密的原始数据, 将自动解密)")
        return 1

    # 提取场景 ID 和地图信息
    print("\n正在从 scenarios.json 提取信息...")
    scenario_id, auto_map_path = extract_map_info_from_scenario('input/scenarios.json')
    print(f"✅ 场景 ID: {scenario_id}")

    # 确定地图路径
    has_map = not args.skip_map
    map_file = None
    map_dir = None
    map_name = None

    if has_map:
        if args.map_file:
            # 用户指定的地图文件
            map_file = args.map_file
            if not Path(map_file).exists():
                print(f"❌ 指定的地图文件不存在: {map_file}")
                return 1
            map_dir = str(Path(map_file).parent)
            map_name = Path(map_dir).name
            print(f"✅ 使用指定地图: {map_file}")
        elif auto_map_path:
            # 自动检测的地图
            map_path_obj = Path(auto_map_path)
            if map_path_obj.is_file():
                map_file = auto_map_path
                map_dir = str(map_path_obj.parent)
                map_name = Path(map_dir).name
                print(f"✅ 自动检测到地图: {map_file}")
            elif map_path_obj.is_dir():
                # 目录 - 查找地图文件
                map_files = list(map_path_obj.glob('base_map.*'))
                if map_files:
                    map_file = str(map_files[0])
                    map_dir = str(map_path_obj)
                    map_name = map_path_obj.name
                    print(f"✅ 自动检测到地图: {map_file}")
                else:
                    print(f"⚠️  地图目录中未找到 base_map 文件: {auto_map_path}")
                    has_map = False
            else:
                print(f"⚠️  地图路径不存在: {auto_map_path}")
                has_map = False
        else:
            print("⚠️  未能从 scenarios.json 提取地图路径，跳过地图处理")
            has_map = False

    # Step 1: 计算偏移量
    print_step(1, "计算偏移量（匈牙利算法）")
    if not run_command(
        ['python3', 'src/step1_calculate_offset.py'],
        "计算偏移量"
    ):
        return 1

    # Step 2: 生成可视化
    print_step(2, "生成可视化图表")
    if not run_command(
        ['python3', 'src/visualize.py'],
        "生成所有可视化图表"
    ):
        return 1

    # Step 3: 应用偏移
    print_step(3, "应用偏移 (场景 + 地图)")

    # ===== 场景处理 =====
    print("\n" + "─"*70)
    print("🔸 生成偏移后的场景")
    print("─"*70 + "\n")

    # 构建场景生成命令
    cmd = ['python3', 'src/step3_create_scenario.py']

    # 如果有地图，传递 map_name 参数
    if has_map:
        offset_map_name = f'{map_name}_offset'
        cmd.extend(['--map-name', offset_map_name])
        print(f"ℹ️  场景将指向偏移后的地图: {offset_map_name}")

    if args.all_objects:
        cmd.append('--all-objects')
        print("ℹ️  场景将包含所有障碍物")
    else:
        print("ℹ️  场景只包含匹配的障碍物")

    if not run_command(cmd, "创建新场景"):
        return 1

    # 获取生成的场景ID（从输出文件中读取）
    import glob
    scenario_files = sorted(glob.glob('output/*.json'), key=lambda x: Path(x).stat().st_mtime, reverse=True)
    if scenario_files:
        scenario_output = scenario_files[0]
        print(f"\n📄 场景文件: {scenario_output}")
    else:
        scenario_output = None
        print("\n⚠️  未找到生成的场景文件")

    # ===== 地图处理 =====
    if has_map:
        print("\n" + "─"*70)
        print("🔸 应用偏移到地图")
        print("─"*70 + "\n")

        # 地图输出到 output/{map_name}_offset/
        output_map_dir = Path(f'output/{map_name}_offset')
        output_map_dir.mkdir(parents=True, exist_ok=True)
        output_map_file = output_map_dir / 'base_map.bin'

        if not run_command(
            ['python3', 'src/step2_apply_offset_to_map.py',
             map_file, str(output_map_file), '--format', 'binary'],
            "应用偏移到地图"
        ):
            return 1
        print(f"\n🗺️  地图目录: {output_map_dir}/")
    else:
        print("\n" + "─"*70)
        print("🔸 跳过地图处理")
        print("─"*70 + "\n")

    # Step 4: 生成辅助地图文件
    if has_map:
        print_step(4, "生成辅助地图文件 (sim_map, routing_map)")

        if not run_command(
            ['python3', 'src/map_generator.py', '--map_dir', str(output_map_dir)],
            "生成辅助地图文件"
        ):
            print("⚠️  警告: 辅助地图生成失败，但主地图文件仍然可用")

    # 完成
    print("\n" + "="*70)
    print("✅ 工作流完成！")
    print("="*70)

    print("\n📊 生成的文件:")

    print("\n计算结果:")
    print("  - results/offset_results.json")

    print("\n可视化图表:")
    viz_dir = Path('visualizations')
    if viz_dir.exists():
        for viz_file in sorted(viz_dir.glob('*.png')):
            print(f"  - {viz_file}")

    print("\n📦 Ready-to-Use 输出:")

    # 显示场景文件
    if scenario_output:
        scenario_filename = Path(scenario_output).name
        print(f"\n  📄 场景文件: {scenario_output}")
        # 读取场景ID
        try:
            with open(scenario_output, 'r') as f:
                scenario_data = json.load(f)
                actual_scenario_id = scenario_data.get('id', 'unknown')
                print(f"       场景 ID: {actual_scenario_id}")
        except:
            pass

    if has_map:
        print(f"\n  🗺️  地图目录: output/{map_name}_offset/")
        output_map_dir_path = Path(f'output/{map_name}_offset')
        if (output_map_dir_path / 'base_map.bin').exists():
            print("       ├── base_map.bin (必需)")
        if (output_map_dir_path / 'sim_map.bin').exists():
            print("       ├── sim_map.bin (Dreamview显示)")
        if (output_map_dir_path / 'routing_map.bin').exists():
            print("       ├── routing_map.bin (路径规划)")

    print("\n💡 使用方法:")
    print("  1. 查看 visualizations/ 目录验证偏移效果")
    if has_map:
        print(f"  2. 复制地图到 Apollo:")
        print(f"     cp -r output/{map_name}_offset /apollo_workspace/modules/map/data/")
        print(f"  3. 在 Dreamview 中:")
        print(f"     - 选择地图: {map_name}_offset")
        if scenario_output:
            print(f"     - 加载场景: {Path(scenario_output).name}")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
