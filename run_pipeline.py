#!/usr/bin/env python3
"""
地图和场景偏移校准工作流 - 主运行脚本
完整的 pipeline，从偏移计算到最终输出
"""

import subprocess
import sys
import os
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


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║         地图和场景偏移校准工作流 (Map Offset Pipeline)            ║
║                                                                   ║
║  自动化执行从偏移计算到地图/场景生成的完整流程                      ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    # 检查必需文件
    print("检查必需文件...")
    if not check_files_exist('input/scenarios.json', 'input/data.json'):
        print("\n请确保以下文件存在于 input/ 目录:")
        print("  - input/scenarios.json (原始场景)")
        print("  - input/data.json (障碍物数据)")
        return 1

    # 询问是否有地图文件
    has_map = input("\n是否有地图文件需要处理? (y/n, 默认 n): ").lower().strip() == 'y'
    map_file = None
    if has_map:
        map_file = input("请输入地图文件路径 (例如 base_map.bin): ").strip()
        if not Path(map_file).exists():
            print(f"❌ 地图文件不存在: {map_file}")
            return 1

    # Step 1: 计算偏移量
    print_step(1, "计算偏移量（匈牙利算法）")
    if not run_command(
        ['python3', 'step1_calculate_offset.py'],
        "计算偏移量"
    ):
        return 1

    # Step 2a: 可视化匹配结果
    print_step(2, "生成可视化图表 (2a: 匹配分析)")
    if not run_command(
        ['python3', 'step2a_visualize_matching.py'],
        "生成匹配可视化"
    ):
        return 1

    # Step 2b: 可视化障碍物
    print("\n步骤 2 (续): 生成可视化图表 (2b: 障碍物分析)\n")
    if not run_command(
        ['python3', 'step2b_visualize_obstacles.py'],
        "生成障碍物可视化"
    ):
        return 1

    # Step 3: 应用偏移到地图 (如果有)
    if has_map:
        print_step(3, "应用偏移到地图")
        output_map = f"output/{Path(map_file).stem}_offset.bin"
        if not run_command(
            ['python3', 'step3_apply_offset_to_map.py',
             map_file, output_map, '--format', 'binary'],
            "应用偏移到地图"
        ):
            return 1
        print(f"\n📄 地图已保存到: {output_map}")
    else:
        print_step(3, "跳过地图处理 (未提供地图文件)")

    # Step 4: 创建新场景
    step_num = 4 if has_map else 3
    print_step(step_num, "创建新场景文件")

    # 询问是否包含所有障碍物
    all_objects = input("\n是否包含所有障碍物? (y/n, 默认 n - 只包含匹配的): ").lower().strip() == 'y'

    cmd = ['python3', 'step4_create_scenario.py', '-o', 'output/scenarios_new.json']
    if all_objects:
        cmd.append('--all-objects')

    if not run_command(cmd, "创建新场景"):
        return 1

    # 完成
    print("\n" + "="*70)
    print("✅ 工作流完成！")
    print("="*70)

    print("\n📊 生成的文件:")
    print("\n计算结果:")
    print("  - results/offset_results.json")

    print("\n可视化图表:")
    print("  - visualizations/01_matching_overview.png")
    print("  - visualizations/02_detailed_matching.png")
    print("  - visualizations/03_vector_field.png")
    print("  - visualizations/04_obstacles_detailed.png")
    print("  - visualizations/05_obstacles_boxes.png")

    print("\n最终输出:")
    if has_map:
        print(f"  - {output_map}")
    print("  - output/scenarios_new.json")

    print("\n💡 提示: 查看 visualizations/ 目录中的图表验证结果")

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
