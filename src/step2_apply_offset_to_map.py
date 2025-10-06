#!/usr/bin/env python3
"""
对 Apollo HD Map 应用偏移变换
根据之前计算的偏移量，平移地图中的所有坐标点
"""

import json
import argparse
from pathlib import Path
from google.protobuf import text_format

# Apollo 10.0 proto 导入
try:
    from modules.common_msgs.map_msgs.map_pb2 import Map

    map_pb2 = True  # 标记成功导入
except ImportError:
    print("警告: 未找到 Apollo proto 模块")
    print("请确保已编译 Apollo 10.0 proto 文件")
    Map = None
    map_pb2 = None


class MapOffsetTransformer:
    """地图偏移变换器"""

    def __init__(self, offset_x: float, offset_y: float, rotation: float = 0.0):
        """
        初始化变换器

        Args:
            offset_x: X方向偏移量（米）
            offset_y: Y方向偏移量（米）
            rotation: 旋转角度（弧度），默认为0
        """
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.rotation = rotation

        print("初始化地图变换器:")
        print(f"  偏移: Δx={offset_x:.4f}m, Δy={offset_y:.4f}m")
        print(f"  旋转: θ={rotation:.6f}rad ({rotation * 180 / 3.14159:.4f}°)")

    def transform_point(self, point):
        """
        对单个点应用变换

        Args:
            point: 包含 x, y 属性的点对象

        Returns:
            变换后的 (x, y)
        """
        # 简单平移（如果旋转角度很小可以忽略）
        if abs(self.rotation) < 0.01:  # 小于约0.57度
            new_x = point.x + self.offset_x
            new_y = point.y + self.offset_y
        else:
            # 带旋转的变换
            import math

            cos_theta = math.cos(self.rotation)
            sin_theta = math.sin(self.rotation)

            # 先旋转，再平移
            new_x = point.x * cos_theta - point.y * sin_theta + self.offset_x
            new_y = point.x * sin_theta + point.y * cos_theta + self.offset_y

        return new_x, new_y

    def transform_map(self, map_obj) -> int:
        """
        对整个地图应用变换

        Args:
            map_obj: map_pb2.Map 对象

        Returns:
            变换的点数量
        """
        point_count = 0

        # 1. 变换所有 lane 中的点
        print("\n处理 Lanes...")
        for lane in map_obj.lane:
            # Central curve
            for segment in lane.central_curve.segment:
                for point in segment.line_segment.point:
                    point.x, point.y = self.transform_point(point)
                    point_count += 1

            # Left boundary
            for segment in lane.left_boundary.curve.segment:
                for point in segment.line_segment.point:
                    point.x, point.y = self.transform_point(point)
                    point_count += 1

            # Right boundary
            for segment in lane.right_boundary.curve.segment:
                for point in segment.line_segment.point:
                    point.x, point.y = self.transform_point(point)
                    point_count += 1

        print(f"  处理了 {len(map_obj.lane)} 个 lanes")

        # 2. 变换所有 road 中的点
        print("\n处理 Roads...")
        for road in map_obj.road:
            for section in road.section:
                # Outer polygon edges
                for edge in section.boundary.outer_polygon.edge:
                    for segment in edge.curve.segment:
                        for point in segment.line_segment.point:
                            point.x, point.y = self.transform_point(point)
                            point_count += 1

        print(f"  处理了 {len(map_obj.road)} 个 roads")

        # 3. 变换所有 junction 中的点（如果有）
        if hasattr(map_obj, "junction"):
            print("\n处理 Junctions...")
            for junction in map_obj.junction:
                if hasattr(junction, "polygon"):
                    for point in junction.polygon.point:
                        point.x, point.y = self.transform_point(point)
                        point_count += 1
            print(f"  处理了 {len(map_obj.junction)} 个 junctions")

        # 4. 变换所有 crosswalk 中的点（如果有）
        if hasattr(map_obj, "crosswalk"):
            print("\n处理 Crosswalks...")
            for crosswalk in map_obj.crosswalk:
                if hasattr(crosswalk, "polygon"):
                    for point in crosswalk.polygon.point:
                        point.x, point.y = self.transform_point(point)
                        point_count += 1
            print(f"  处理了 {len(map_obj.crosswalk)} 个 crosswalks")

        # 5. 变换所有 stop_sign 中的点（如果有）
        if hasattr(map_obj, "stop_sign"):
            print("\n处理 Stop Signs...")
            for stop_sign in map_obj.stop_sign:
                for stop_line in stop_sign.stop_line:
                    for segment in stop_line.segment:
                        for point in segment.line_segment.point:
                            point.x, point.y = self.transform_point(point)
                            point_count += 1
            print(f"  处理了 {len(map_obj.stop_sign)} 个 stop signs")

        # 6. 变换所有 signal 中的点（如果有）
        if hasattr(map_obj, "signal"):
            print("\n处理 Traffic Signals...")
            for signal in map_obj.signal:
                for stop_line in signal.stop_line:
                    for segment in stop_line.segment:
                        for point in segment.line_segment.point:
                            point.x, point.y = self.transform_point(point)
                            point_count += 1
            print(f"  处理了 {len(map_obj.signal)} 个 signals")

        # 7. 变换所有 yield_sign 中的点（如果有）
        if hasattr(map_obj, "yield_sign"):
            print("\n处理 Yield Signs...")
            for yield_sign in map_obj.yield_sign:
                for stop_line in yield_sign.stop_line:
                    for segment in stop_line.segment:
                        for point in segment.line_segment.point:
                            point.x, point.y = self.transform_point(point)
                            point_count += 1
            print(f"  处理了 {len(map_obj.yield_sign)} 个 yield signs")

        # 8. 变换所有 overlap 中的点（如果有）
        if hasattr(map_obj, "overlap"):
            print("\n处理 Overlaps...")
            # Overlaps 通常不包含直接的点坐标，而是引用其他对象
            # 这里可能不需要处理
            pass

        # 9. 变换所有 clear_area 中的点（如果有）
        if hasattr(map_obj, "clear_area"):
            print("\n处理 Clear Areas...")
            for clear_area in map_obj.clear_area:
                if hasattr(clear_area, "polygon"):
                    for point in clear_area.polygon.point:
                        point.x, point.y = self.transform_point(point)
                        point_count += 1
            print(f"  处理了 {len(map_obj.clear_area)} 个 clear areas")

        # 10. 变换所有 speed_bump 中的点（如果有）
        if hasattr(map_obj, "speed_bump"):
            print("\n处理 Speed Bumps...")
            for speed_bump in map_obj.speed_bump:
                if hasattr(speed_bump, "position"):
                    for segment in speed_bump.position:
                        for point in segment.line_segment.point:
                            point.x, point.y = self.transform_point(point)
                            point_count += 1
            print(f"  处理了 {len(map_obj.speed_bump)} 个 speed bumps")

        # 11. 变换所有 parking_space 中的点（如果有）
        if hasattr(map_obj, "parking_space"):
            print("\n处理 Parking Spaces...")
            for parking_space in map_obj.parking_space:
                if hasattr(parking_space, "polygon"):
                    for point in parking_space.polygon.point:
                        point.x, point.y = self.transform_point(point)
                        point_count += 1
            print(f"  处理了 {len(map_obj.parking_space)} 个 parking spaces")

        return point_count


def load_offset_from_results(
    results_file: str = "results/offset_results.json",
) -> tuple:
    """
    从结果文件加载偏移量

    Args:
        results_file: 偏移结果文件路径

    Returns:
        (offset_x, offset_y, rotation) 元组
    """
    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    offset_x = results["simple_offset_stats"]["dx_mean"]
    offset_y = results["simple_offset_stats"]["dy_mean"]
    rotation = results["transformation"]["rotation_radians"]

    return offset_x, offset_y, rotation


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="对 Apollo HD Map 应用偏移变换")
    parser.add_argument(
        "input_map", type=str, help="输入地图文件路径 (text format .txt 或 binary .bin)"
    )
    parser.add_argument("output_map", type=str, help="输出地图文件路径")
    parser.add_argument(
        "--offset-file",
        type=str,
        default="results/offset_results.json",
        help="偏移结果文件路径（JSON格式）",
    )
    parser.add_argument(
        "--offset-x", type=float, help="手动指定X偏移量（米），会覆盖文件中的值"
    )
    parser.add_argument(
        "--offset-y", type=float, help="手动指定Y偏移量（米），会覆盖文件中的值"
    )
    parser.add_argument(
        "--rotation", type=float, help="手动指定旋转角度（弧度），会覆盖文件中的值"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "binary"],
        default="text",
        help="输出格式：text 或 binary（默认：text）",
    )
    parser.add_argument(
        "--new-map-id",
        type=str,
        default=None,
        help="新的地图ID（用于更新 metaInfo.json）",
    )

    args = parser.parse_args()

    if Map is None:
        print("错误: 未找到 Apollo proto 模块")
        print("请确保已编译 Apollo 10.0 proto 文件并正确安装")
        return 1

    # 加载偏移量
    if args.offset_x is not None and args.offset_y is not None:
        offset_x = args.offset_x
        offset_y = args.offset_y
        rotation = args.rotation if args.rotation is not None else 0.0
        print("使用手动指定的偏移量")
    else:
        print(f"从文件加载偏移量: {args.offset_file}")
        offset_x, offset_y, rotation = load_offset_from_results(args.offset_file)

    # 创建变换器
    transformer = MapOffsetTransformer(offset_x, offset_y, rotation)

    # 读取地图
    print(f"\n读取地图: {args.input_map}")
    map_obj = Map()

    try:
        with open(args.input_map, "r", encoding="utf-8") as f:
            text_format.Merge(f.read(), map_obj)
        print("  格式: Text")
    except Exception as e:
        print(f"  Text格式读取失败，尝试Binary格式: {e}")
        try:
            with open(args.input_map, "rb") as f:
                map_obj.ParseFromString(f.read())
            print("  格式: Binary")
        except Exception as e2:
            print(f"错误: 无法读取地图文件: {e2}")
            return 1

    # 应用变换
    print("\n" + "=" * 60)
    print("开始变换地图...")
    print("=" * 60)
    point_count = transformer.transform_map(map_obj)

    print("\n" + "=" * 60)
    print(f"变换完成！共处理 {point_count} 个点")
    print("=" * 60)

    # 更新地图 header 中的边界坐标和版本信息
    if args.new_map_id:
        output_map_name = Path(args.output_map).parent.name
        print("\n更新地图 header...")
        print(f"  原 version: {map_obj.header.version.decode('utf-8')}")
        print(f"  新 version: {output_map_name}")

        # 更新 version 字段（地图名称）
        map_obj.header.version = output_map_name.encode("utf-8")

        # 更新边界坐标（如果存在）
        if map_obj.header.HasField("left"):
            old_left = map_obj.header.left
            old_top = map_obj.header.top
            old_right = map_obj.header.right
            old_bottom = map_obj.header.bottom

            map_obj.header.left += offset_x
            map_obj.header.top += offset_y
            map_obj.header.right += offset_x
            map_obj.header.bottom += offset_y

            print("  边界坐标已更新:")
            print(f"    left:   {old_left:.4f} -> {map_obj.header.left:.4f}")
            print(f"    top:    {old_top:.4f} -> {map_obj.header.top:.4f}")
            print(f"    right:  {old_right:.4f} -> {map_obj.header.right:.4f}")
            print(f"    bottom: {old_bottom:.4f} -> {map_obj.header.bottom:.4f}")

    # 保存地图
    print(f"\n保存地图: {args.output_map}")
    try:
        if args.format == "text":
            with open(args.output_map, "w", encoding="utf-8") as f:
                f.write(text_format.MessageToString(map_obj))
            print("  格式: Text")
        else:
            with open(args.output_map, "wb") as f:
                f.write(map_obj.SerializeToString())
            print("  格式: Binary")
    except Exception as e:
        print(f"错误: 无法保存地图文件: {e}")
        return 1

    # 处理 metaInfo.json（如果提供了新的 map ID）
    if args.new_map_id:
        input_map_dir = Path(args.input_map).parent
        output_map_dir = Path(args.output_map).parent
        meta_info_file = input_map_dir / "metaInfo.json"

        if meta_info_file.exists():
            try:
                print("\n更新 metaInfo.json...")
                with open(meta_info_file, "r") as f:
                    meta_data = json.load(f)

                # 获取原始的 mapId (可能是字典的键)
                if meta_data:
                    old_map_id = list(meta_data.keys())[0]
                    old_meta = meta_data[old_map_id]

                    # 应用偏移到 left 和 top 坐标
                    # left 和 top 是地图左上角的坐标
                    old_left = old_meta.get("left", 0)
                    old_top = old_meta.get("top", 0)

                    # 应用偏移变换（注意：只应用平移，不需要旋转）
                    new_left = old_left + offset_x
                    new_top = old_top + offset_y

                    # 创建新的元数据，使用新的 map ID 和偏移后的坐标
                    new_meta_data = {
                        args.new_map_id: {
                            **old_meta,
                            "mapid": args.new_map_id,
                            "left": new_left,
                            "top": new_top,
                        }
                    }

                    # 保存新的 metaInfo.json
                    output_meta_file = output_map_dir / "metaInfo.json"
                    with open(output_meta_file, "w") as f:
                        json.dump(new_meta_data, f)

                    print("✅ 已更新 metaInfo.json")
                    print(f"   原地图 ID: {old_map_id}")
                    print(f"   新地图 ID: {args.new_map_id}")
                    print(f"   left: {old_left:.4f} -> {new_left:.4f}")
                    print(f"   top: {old_top:.4f} -> {new_top:.4f}")
            except Exception as e:
                print(f"⚠️  警告: 更新 metaInfo.json 失败: {e}")
        else:
            print("\n⚠️  未找到 metaInfo.json，跳过元信息更新")

    print("\n✅ 地图偏移完成！")
    print(f"输入: {args.input_map}")
    print(f"输出: {args.output_map}")
    print(f"偏移: Δx={offset_x:.4f}m, Δy={offset_y:.4f}m, θ={rotation:.6f}rad")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
