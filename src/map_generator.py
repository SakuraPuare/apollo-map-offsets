#!/usr/bin/env python3
"""
地图辅助文件生成模块
统一处理 sim_map 和 routing_map 的生成
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional
import shutil


def check_sim_map_generator() -> Optional[str]:
    """检查 sim_map_generator 二进制文件是否存在"""
    binary_path = Path(
        "/apollo_workspace/bazel-bin/modules/map/tools/sim_map_generator"
    )

    if not binary_path.exists():
        return None
    return str(binary_path)


def check_topo_creator() -> Optional[str]:
    """检查 topo_creator 工具是否存在"""
    topo_creator = shutil.which("topo_creator")
    if topo_creator:
        return topo_creator

    # 尝试几个常见位置
    possible_paths = [
        "/opt/apollo/neo/bin/topo_creator",
        "/apollo_workspace/bazel-bin/modules/routing/topo_creator/topo_creator",
    ]
    for path in possible_paths:
        if Path(path).exists():
            return path

    return None


def generate_sim_map(
    map_dir: str,
    map_filename: str = "base_map.bin",
    output_dir: Optional[str] = None,
    downsample_distance: int = 5,
    steep_turn_downsample_distance: int = 1,
) -> bool:
    """
    生成 sim_map

    Args:
        map_dir: 地图所在目录
        map_filename: 地图文件名（默认 base_map.bin）
        output_dir: 输出目录（默认与map_dir相同）
        downsample_distance: 普通路径的下采样距离
        steep_turn_downsample_distance: 急转弯的下采样距离

    Returns:
        是否成功
    """
    # 检查二进制文件
    sim_map_gen = check_sim_map_generator()
    if not sim_map_gen:
        print("⚠️  sim_map_generator 未编译，跳过 sim_map 生成")
        print("   编译命令: bazel build //modules/map/tools:sim_map_generator")
        return False

    # 检查输入地图
    map_path = Path(map_dir) / map_filename
    if not map_path.exists():
        print(f"❌ 地图文件不存在: {map_path}")
        return False

    # 设置输出目录
    if output_dir is None:
        output_dir = map_dir
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("  📍 生成 sim_map.bin...")
    print(f"     输入: {map_path}")
    print(f"     输出: {output_path}/sim_map.bin")

    # 构建命令
    cmd = [
        sim_map_gen,
        f"--map_dir={map_dir}",
        f"--test_base_map_filename={map_filename}",
        f"--output_dir={output_path}",
        f"--downsample_distance={downsample_distance}",
        f"--steep_turn_downsample_distance={steep_turn_downsample_distance}",
    ]

    # 执行命令
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)

        # 检查输出文件
        sim_map_file = output_path / "sim_map.bin"
        if sim_map_file.exists():
            size_mb = sim_map_file.stat().st_size / 1024 / 1024
            print(f"  ✅ sim_map.bin ({size_mb:.2f} MB)")
            return True
        else:
            print("  ⚠️  sim_map.bin 未生成")
            return False

    except subprocess.CalledProcessError as e:
        print(
            f"  ❌ sim_map 生成失败: {e.stderr[:200] if e.stderr else 'Unknown error'}"
        )
        return False
    except subprocess.TimeoutExpired:
        print("  ❌ sim_map 生成超时")
        return False


def generate_routing_map(
    map_dir: str, map_filename: str = "base_map.bin", routing_conf: Optional[str] = None
) -> bool:
    """
    生成 routing_map.bin

    Args:
        map_dir: 地图目录（包含 base_map.bin）
        map_filename: 地图文件名（默认 base_map.bin）
        routing_conf: routing 配置文件路径

    Returns:
        是否成功
    """
    # 检查topo_creator
    topo_creator = check_topo_creator()
    if not topo_creator:
        print("⚠️  topo_creator 未找到，跳过 routing_map 生成")
        print("   编译命令: bazel build //modules/routing/...")
        return False

    # 检查输入
    map_dir_path = Path(map_dir)
    if not map_dir_path.exists():
        print(f"❌ 地图目录不存在: {map_dir}")
        return False

    base_map_path = map_dir_path / map_filename
    if not base_map_path.exists():
        print(f"❌ 地图文件不存在: {base_map_path}")
        return False

    print("  📍 生成 routing_map.bin...")
    print(f"     输入: {base_map_path}")
    print(f"     topo_creator: {topo_creator}")

    # 构建命令
    cmd = [topo_creator]
    if routing_conf and Path(routing_conf).exists():
        cmd.extend(["--flagfile", routing_conf])

    try:
        # 运行 topo_creator (需要从 Apollo 根目录运行)
        result = subprocess.run(
            cmd + ["--map_dir", str(map_dir_path.absolute())],
            cwd="/apollo_workspace",
            capture_output=True,
            text=True,
            timeout=300,
        )

        # 检查输出文件
        routing_map_path = map_dir_path / "routing_map.bin"
        if routing_map_path.exists():
            size_mb = routing_map_path.stat().st_size / 1024 / 1024
            print(f"  ✅ routing_map.bin ({size_mb:.2f} MB)")
            return True
        else:
            print("  ⚠️  routing_map.bin 未生成")
            if result.stderr:
                print(f"     错误: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print("  ❌ routing_map 生成超时")
        return False
    except Exception as e:
        print(f"  ❌ routing_map 生成失败: {e}")
        return False


def generate_map_files(
    map_dir: str,
    map_filename: str = "base_map.bin",
    generate_sim: bool = True,
    generate_routing: bool = True,
    routing_conf: Optional[str] = None,
) -> dict:
    """
    批量生成地图辅助文件

    Args:
        map_dir: 地图目录
        map_filename: 地图文件名
        generate_sim: 是否生成 sim_map
        generate_routing: 是否生成 routing_map
        routing_conf: routing 配置文件路径

    Returns:
        生成结果字典 {'sim_map': bool, 'routing_map': bool}
    """
    print("\n" + "=" * 70)
    print("生成地图辅助文件")
    print("=" * 70)
    print(f"\n地图目录: {map_dir}")
    print(f"地图文件: {map_filename}\n")

    results = {}

    if generate_sim:
        results["sim_map"] = generate_sim_map(map_dir, map_filename)
    else:
        results["sim_map"] = None

    if generate_routing:
        results["routing_map"] = generate_routing_map(
            map_dir, map_filename, routing_conf
        )
    else:
        results["routing_map"] = None

    print("\n" + "=" * 70)
    print("生成完成")
    print("=" * 70)

    return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="生成地图辅助文件 (sim_map, routing_map)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成所有地图文件
  python3 map_generator.py --map_dir output/map/my_map

  # 只生成 sim_map
  python3 map_generator.py --map_dir output/map/my_map --no-routing

  # 只生成 routing_map
  python3 map_generator.py --map_dir output/map/my_map --no-sim
        """,
    )

    parser.add_argument("--map_dir", required=True, help="地图目录")
    parser.add_argument("--map_filename", default="base_map.bin", help="地图文件名")
    parser.add_argument("--no-sim", action="store_true", help="不生成 sim_map")
    parser.add_argument("--no-routing", action="store_true", help="不生成 routing_map")
    parser.add_argument(
        "--routing_conf",
        default="/apollo_workspace/modules/routing/conf/routing.conf",
        help="routing 配置文件",
    )

    args = parser.parse_args()

    results = generate_map_files(
        map_dir=args.map_dir,
        map_filename=args.map_filename,
        generate_sim=not args.no_sim,
        generate_routing=not args.no_routing,
        routing_conf=args.routing_conf,
    )

    # 返回码：至少一个成功则返回0
    success = any(v for v in results.values() if v is not None and v)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
