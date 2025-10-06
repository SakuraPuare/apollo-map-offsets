#!/usr/bin/env python3
"""
使用匈牙利算法基于坐标匹配障碍物
ID不可信，只使用坐标和尺寸信息
"""

import json
import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Obstacle:
    """障碍物"""

    id: str
    x: float
    y: float
    heading: float
    length: float
    width: float
    height: float


def load_scenarios_obstacles(filepath: str) -> List[Obstacle]:
    """从scenarios.json提取障碍物"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    obstacles = []
    scenario_objects = data["scenario"]["entities"]["scenarioObjects"]
    obj_dims = {}

    for obj in scenario_objects:
        obj_id = str(obj["id"])
        entity = obj["entityObject"]
        if "vehicle" in entity:
            dims = entity["vehicle"]["boundingBox"]["dimensions"]
        elif "unknownUnmovableObject" in entity:
            dims = entity["unknownUnmovableObject"]["boundingBox"]["dimensions"]
        else:
            continue
        obj_dims[obj_id] = dims

    privates = data["scenario"]["storyboard"]["init"]["actions"]["privates"]
    for private in privates:
        entity_ref = private["entityRef"]["entityRef"]
        for action in private["privateActions"]:
            if "teleportAction" in action:
                pos = action["teleportAction"]["position"]["worldPosition"]
                if entity_ref in obj_dims:
                    dims = obj_dims[entity_ref]
                    obstacles.append(
                        Obstacle(
                            id=entity_ref,
                            x=pos["x"],
                            y=pos["y"],
                            heading=pos["h"],
                            length=dims["length"],
                            width=dims["width"],
                            height=dims["height"],
                        )
                    )
                break

    return obstacles


def load_data_obstacles(filepath: str) -> List[Obstacle]:
    """从data.json提取障碍物"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    obstacles = []
    for obj in data.get("object", []):
        obstacles.append(
            Obstacle(
                id=str(obj["id"]),
                x=obj["positionX"],
                y=obj["positionY"],
                heading=obj["heading"],
                length=obj["length"],
                width=obj["width"],
                height=obj["height"],
            )
        )

    return obstacles


def estimate_initial_transform(
    src_obs: List[Obstacle], dst_obs: List[Obstacle]
) -> Tuple[float, float]:
    """
    估计初始平移偏移（假设没有旋转或旋转很小）
    使用中心点的偏移作为初始估计
    """
    src_center = np.array([[obs.x, obs.y] for obs in src_obs]).mean(axis=0)
    dst_center = np.array([[obs.x, obs.y] for obs in dst_obs]).mean(axis=0)

    offset = dst_center - src_center
    return offset[0], offset[1]


def match_obstacles_hungarian(
    src_obs: List[Obstacle],
    dst_obs: List[Obstacle],
    initial_offset: Tuple[float, float] = None,
    max_distance: float = 50.0,
    dimension_weight: float = 100.0,
) -> List[Tuple[int, int, float]]:
    """
    使用匈牙利算法匹配障碍物

    参数:
        src_obs: 源障碍物列表
        dst_obs: 目标障碍物列表
        initial_offset: 初始偏移估计 (dx, dy)
        max_distance: 最大匹配距离阈值（米）
        dimension_weight: 尺寸差异的权重

    返回:
        匹配列表 [(src_idx, dst_idx, cost), ...]
    """
    n_src = len(src_obs)
    n_dst = len(dst_obs)

    # 如果没有提供初始偏移，估计一个
    if initial_offset is None:
        initial_offset = estimate_initial_transform(src_obs, dst_obs)

    dx_init, dy_init = initial_offset
    print(f"初始偏移估计: dx={dx_init:.2f}, dy={dy_init:.2f}")

    # 构建成本矩阵
    # 成本 = 坐标距离 + 尺寸差异
    cost_matrix = np.zeros((n_src, n_dst))

    for i, src in enumerate(src_obs):
        # 应用初始偏移
        src_x_adjusted = src.x + dx_init
        src_y_adjusted = src.y + dy_init

        for j, dst in enumerate(dst_obs):
            # 坐标距离
            pos_dist = np.sqrt(
                (src_x_adjusted - dst.x) ** 2 + (src_y_adjusted - dst.y) ** 2
            )

            # 尺寸差异（L1距离）
            dim_diff = (
                abs(src.length - dst.length)
                + abs(src.width - dst.width)
                + abs(src.height - dst.height)
            )

            # 总成本
            cost = pos_dist + dimension_weight * dim_diff

            # 如果距离太远，设为无穷大（不匹配）
            if pos_dist > max_distance:
                cost = 1e10

            cost_matrix[i, j] = cost

    # 使用匈牙利算法求解最优匹配
    print("运行匈牙利算法...")
    src_indices, dst_indices = linear_sum_assignment(cost_matrix)

    # 过滤掉成本过高的匹配
    matches = []
    for src_idx, dst_idx in zip(src_indices, dst_indices):
        cost = cost_matrix[src_idx, dst_idx]
        if cost < 1e9:  # 排除无穷大的匹配
            matches.append((src_idx, dst_idx, cost))

    print(f"找到 {len(matches)} 个有效匹配")
    return matches


def calculate_transform_from_matches(
    src_obs: List[Obstacle],
    dst_obs: List[Obstacle],
    matches: List[Tuple[int, int, float]],
) -> dict:
    """从匹配计算变换参数"""
    if not matches:
        return None

    # 提取匹配点对
    src_points = np.array([[src_obs[m[0]].x, src_obs[m[0]].y] for m in matches])
    dst_points = np.array([[dst_obs[m[1]].x, dst_obs[m[1]].y] for m in matches])

    # 计算中心点
    src_center = src_points.mean(axis=0)
    dst_center = dst_points.mean(axis=0)

    # 中心化
    src_centered = src_points - src_center
    dst_centered = dst_points - dst_center

    # SVD求解旋转
    H = src_centered.T @ dst_centered
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    # 确保是旋转矩阵
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    # 计算平移
    t = dst_center - R @ src_center

    # 提取旋转角度
    theta = np.arctan2(R[1, 0], R[0, 0])

    # 验证精度
    transformed = (R @ src_points.T).T + t
    errors = np.linalg.norm(transformed - dst_points, axis=1)

    # 计算每个点的偏移
    offsets = dst_points - src_points

    return {
        "rotation_matrix": R,
        "translation": t,
        "rotation_radians": theta,
        "rotation_degrees": np.degrees(theta),
        "errors": errors,
        "offsets": offsets,
        "src_points": src_points,
        "dst_points": dst_points,
    }


def main():
    """主函数"""
    scenarios_file = "input/scenarios.json"
    data_file = "input/data.json"

    print("=" * 70)
    print("使用匈牙利算法匹配障碍物（基于坐标，ID不可信）")
    print("=" * 70)

    # 加载数据
    print("\n1. 加载障碍物...")
    scenarios_obs = load_scenarios_obstacles(scenarios_file)
    data_obs = load_data_obstacles(data_file)

    print(f"   scenarios.json: {len(scenarios_obs)} 个障碍物")
    print(f"   data.json: {len(data_obs)} 个障碍物")

    # 估计初始偏移
    print("\n2. 估计初始偏移...")
    dx_init, dy_init = estimate_initial_transform(scenarios_obs, data_obs)

    # 匹配障碍物
    print("\n3. 匹配障碍物...")
    matches = match_obstacles_hungarian(
        scenarios_obs,
        data_obs,
        initial_offset=(dx_init, dy_init),
        max_distance=50.0,  # 允许50米的初始误差
        dimension_weight=100.0,  # 尺寸差异惩罚
    )

    if not matches:
        print("错误: 没有找到任何匹配！")
        return

    # 计算变换
    print("\n4. 计算精确变换...")
    result = calculate_transform_from_matches(scenarios_obs, data_obs, matches)

    # 输出结果
    print("\n" + "=" * 70)
    print("变换结果")
    print("=" * 70)
    print(f"匹配点对数: {len(matches)}")
    print("\n平移偏移:")
    print(f"  Δx = {result['translation'][0]:.6f} 米")
    print(f"  Δy = {result['translation'][1]:.6f} 米")
    print("\n旋转角度:")
    print(f"  θ = {result['rotation_degrees']:.6f} 度")
    print(f"  θ = {result['rotation_radians']:.6f} 弧度")

    print("\n旋转矩阵:")
    R = result["rotation_matrix"]
    print(f"  [{R[0, 0]:9.6f}  {R[0, 1]:9.6f}]")
    print(f"  [{R[1, 0]:9.6f}  {R[1, 1]:9.6f}]")

    print("\n匹配精度:")
    print(f"  平均误差: {result['errors'].mean():.4f} 米")
    print(f"  中位数误差: {np.median(result['errors']):.4f} 米")
    print(f"  最大误差: {result['errors'].max():.4f} 米")
    print(f"  最小误差: {result['errors'].min():.4f} 米")
    print(f"  标准差: {result['errors'].std():.4f} 米")

    print("\n简单平移统计（未考虑旋转）:")
    print(
        f"  dx: mean={result['offsets'][:, 0].mean():.2f}, std={result['offsets'][:, 0].std():.2f}"
    )
    print(
        f"  dy: mean={result['offsets'][:, 1].mean():.2f}, std={result['offsets'][:, 1].std():.2f}"
    )

    # 显示前20个匹配
    print("\n前20个匹配点对:")
    print(
        f"{'No.':<4} {'Src ID':<10} {'Dst ID':<10} {'Cost':<10} {'Error(m)':<10} {'Src Pos':<25} {'Dst Pos':<25}"
    )
    print("-" * 110)
    for i, (src_idx, dst_idx, cost) in enumerate(matches[:20]):
        src = scenarios_obs[src_idx]
        dst = data_obs[dst_idx]
        error = result["errors"][i]
        src_pos = f"({src.x:.2f}, {src.y:.2f})"
        dst_pos = f"({dst.x:.2f}, {dst.y:.2f})"
        print(
            f"{i + 1:<4} {src.id:<10} {dst.id:<10} {cost:<10.4f} {error:<10.4f} {src_pos:<25} {dst_pos:<25}"
        )

    # 保存结果
    output = {
        "transformation": {
            "translation": {
                "x": float(result["translation"][0]),
                "y": float(result["translation"][1]),
            },
            "rotation_radians": float(result["rotation_radians"]),
            "rotation_degrees": float(result["rotation_degrees"]),
            "rotation_matrix": result["rotation_matrix"].tolist(),
        },
        "accuracy": {
            "num_matches": len(matches),
            "mean_error": float(result["errors"].mean()),
            "median_error": float(np.median(result["errors"])),
            "max_error": float(result["errors"].max()),
            "min_error": float(result["errors"].min()),
            "std_error": float(result["errors"].std()),
        },
        "simple_offset_stats": {
            "dx_mean": float(result["offsets"][:, 0].mean()),
            "dx_std": float(result["offsets"][:, 0].std()),
            "dy_mean": float(result["offsets"][:, 1].mean()),
            "dy_std": float(result["offsets"][:, 1].std()),
        },
        "matched_pairs": [
            {
                "src_index": int(src_idx),
                "dst_index": int(dst_idx),
                "src_id": scenarios_obs[src_idx].id,
                "dst_id": data_obs[dst_idx].id,
                "src_pos": {
                    "x": float(scenarios_obs[src_idx].x),
                    "y": float(scenarios_obs[src_idx].y),
                },
                "dst_pos": {
                    "x": float(data_obs[dst_idx].x),
                    "y": float(data_obs[dst_idx].y),
                },
                "matching_cost": float(cost),
                "transform_error": float(result["errors"][i]),
                "dimensions": {
                    "src": {
                        "length": scenarios_obs[src_idx].length,
                        "width": scenarios_obs[src_idx].width,
                        "height": scenarios_obs[src_idx].height,
                    },
                    "dst": {
                        "length": data_obs[dst_idx].length,
                        "width": data_obs[dst_idx].width,
                        "height": data_obs[dst_idx].height,
                    },
                },
            }
            for i, (src_idx, dst_idx, cost) in enumerate(matches)
        ],
        "unmatched": {
            "scenarios_count": len(scenarios_obs) - len(matches),
            "data_count": len(data_obs) - len(matches),
        },
    }

    output_file = "results/offset_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n结果已保存到 {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
