#!/usr/bin/env python3
"""
统一的可视化模块
整合了匹配可视化和障碍物可视化功能
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MPLPolygon
from pathlib import Path
from typing import List, Dict, Optional

# 设置中文字体
from font_helper import setup_chinese_font, get_font_properties
font_name = setup_chinese_font()
font_props = get_font_properties()


def set_chinese_labels(ax, xlabel=None, ylabel=None, title=None):
    """设置坐标轴标签和标题，确保使用中文字体"""
    if xlabel:
        ax.set_xlabel(xlabel, fontproperties=font_props, fontsize=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontproperties=font_props, fontsize=12)
    if title:
        ax.set_title(title, fontproperties=font_props, fontsize=14, fontweight='bold')


def load_results(filepath: str = 'results/offset_results.json') -> dict:
    """加载匹配结果"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_scenarios_data(filepath: str = 'input/scenarios.json') -> List[dict]:
    """加载scenarios.json数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    obstacles = []
    scenario_objects = data['scenario']['entities']['scenarioObjects']
    obj_dims = {}

    for obj in scenario_objects:
        obj_id = str(obj['id'])
        entity = obj['entityObject']
        if 'vehicle' in entity:
            dims = entity['vehicle']['boundingBox']['dimensions']
            obj_type = 'vehicle'
        elif 'unknownUnmovableObject' in entity:
            dims = entity['unknownUnmovableObject']['boundingBox']['dimensions']
            obj_type = 'object'
        else:
            continue
        obj_dims[obj_id] = (dims, obj_type)

    privates = data['scenario']['storyboard']['init']['actions']['privates']
    for private in privates:
        entity_ref = private['entityRef']['entityRef']
        for action in private['privateActions']:
            if 'teleportAction' in action:
                pos = action['teleportAction']['position']['worldPosition']
                if entity_ref in obj_dims:
                    dims, obj_type = obj_dims[entity_ref]
                    obstacles.append({
                        'id': entity_ref,
                        'x': pos['x'],
                        'y': pos['y'],
                        'heading': pos['h'],
                        'length': dims['length'],
                        'width': dims['width'],
                        'height': dims['height'],
                        'type': obj_type
                    })
                break

    return obstacles


def load_data_obstacles(filepath: str = 'input/data.json') -> List[dict]:
    """加载data.json数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    obstacles = []
    for obj in data.get('object', []):
        obstacles.append({
            'id': str(obj['id']),
            'x': obj['positionX'],
            'y': obj['positionY'],
            'heading': obj['heading'],
            'length': obj['length'],
            'width': obj['width'],
            'height': obj['height'],
            'type': obj['type']
        })

    return obstacles


def draw_obstacle_box(ax, x, y, length, width, heading, color, alpha=0.6, label=None):
    """绘制障碍物边界框"""
    # 计算矩形的四个角点（以中心点为原点）
    corners = np.array([
        [-length/2, -width/2],
        [length/2, -width/2],
        [length/2, width/2],
        [-length/2, width/2]
    ])

    # 旋转
    rot_matrix = np.array([
        [np.cos(heading), -np.sin(heading)],
        [np.sin(heading), np.cos(heading)]
    ])
    rotated_corners = corners @ rot_matrix.T

    # 平移到实际位置
    rotated_corners[:, 0] += x
    rotated_corners[:, 1] += y

    # 绘制多边形
    polygon = MPLPolygon(rotated_corners, closed=True,
                         edgecolor=color, facecolor=color,
                         alpha=alpha, linewidth=2, label=label)
    ax.add_patch(polygon)

    # 绘制朝向箭头
    arrow_length = max(length, width) * 0.5
    dx = arrow_length * np.cos(heading)
    dy = arrow_length * np.sin(heading)
    ax.arrow(x, y, dx, dy, head_width=0.3, head_length=0.5,
            fc=color, ec=color, alpha=alpha+0.2, linewidth=1.5)


def visualize_matching_overview(results: dict, output_file: str = 'visualizations/01_matching_overview.png'):
    """生成匹配总览图（6子图）"""
    fig = plt.figure(figsize=(20, 10))

    # 提取数据
    matched_pairs = results['matched_pairs']
    src_points = np.array([[p['src_pos']['x'], p['src_pos']['y']] for p in matched_pairs])
    dst_points = np.array([[p['dst_pos']['x'], p['dst_pos']['y']] for p in matched_pairs])
    errors = np.array([p['transform_error'] for p in matched_pairs])

    # 计算偏移
    dx = results['simple_offset_stats']['dx_mean']
    dy = results['simple_offset_stats']['dy_mean']

    # 子图1: 原始位置对比
    ax1 = plt.subplot(2, 3, 1)
    ax1.scatter(src_points[:, 0], src_points[:, 1],
               c='blue', s=100, alpha=0.6, label='Scenarios', marker='o')
    ax1.scatter(dst_points[:, 0], dst_points[:, 1],
               c='red', s=100, alpha=0.6, label='Data', marker='s')
    set_chinese_labels(ax1, xlabel='X (m)', ylabel='Y (m)', title='原始位置对比')
    ax1.legend(prop=font_props, fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')

    # 子图2: 应用偏移后的对比
    ax2 = plt.subplot(2, 3, 2)
    src_shifted = src_points + np.array([dx, dy])
    ax2.scatter(src_shifted[:, 0], src_shifted[:, 1],
               c='blue', s=100, alpha=0.6, label='Scenarios (shifted)', marker='o')
    ax2.scatter(dst_points[:, 0], dst_points[:, 1],
               c='red', s=100, alpha=0.6, label='Data', marker='s')

    # 画匹配线
    for i in range(len(src_shifted)):
        ax2.plot([src_shifted[i, 0], dst_points[i, 0]],
                [src_shifted[i, 1], dst_points[i, 1]],
                'g-', alpha=0.3, linewidth=0.5)

    set_chinese_labels(ax2, xlabel='X (m)', ylabel='Y (m)', title=f'应用偏移后 (Δx={dx:.2f}m, Δy={dy:.2f}m)')
    ax2.legend(prop=font_props, fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')

    # 子图3: 误差分布热图
    ax3 = plt.subplot(2, 3, 3)
    scatter = ax3.scatter(src_shifted[:, 0], src_shifted[:, 1],
                         c=errors, s=200, cmap='RdYlGn_r',
                         alpha=0.8, edgecolors='black', linewidths=1)
    cbar = plt.colorbar(scatter, ax=ax3)
    cbar.set_label('误差 (m)', fontproperties=font_props, fontsize=12)
    set_chinese_labels(ax3, xlabel='X (m)', ylabel='Y (m)', title='匹配误差分布')
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect('equal')

    # 子图4: 误差直方图
    ax4 = plt.subplot(2, 3, 4)
    ax4.hist(errors, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
    ax4.axvline(errors.mean(), color='red', linestyle='--', linewidth=2,
                label=f'平均值: {errors.mean():.2f}m')
    ax4.axvline(np.median(errors), color='green', linestyle='--', linewidth=2,
                label=f'中位数: {np.median(errors):.2f}m')
    set_chinese_labels(ax4, xlabel='误差 (m)', ylabel='频数', title='误差分布直方图')
    ax4.legend(prop=font_props, fontsize=10)
    ax4.grid(True, alpha=0.3, axis='y')

    # 子图5: 偏移向量分布
    ax5 = plt.subplot(2, 3, 5)
    offsets = dst_points - src_points
    ax5.scatter(offsets[:, 0], offsets[:, 1],
               c='purple', s=100, alpha=0.6, edgecolors='black')
    ax5.axvline(dx, color='red', linestyle='--', linewidth=2, label=f'Mean Δx={dx:.2f}m')
    ax5.axhline(dy, color='blue', linestyle='--', linewidth=2, label=f'Mean Δy={dy:.2f}m')
    set_chinese_labels(ax5, xlabel='Δx (m)', ylabel='Δy (m)', title='偏移向量分布')
    ax5.legend(prop=font_props, fontsize=10)
    ax5.grid(True, alpha=0.3)
    ax5.set_aspect('equal')

    # 子图6: 统计信息文本
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')

    stats_text = f"""
    匹配统计信息
    {'='*40}

    匹配点对数: {results['accuracy']['num_matches']}

    平移偏移:
      Δx = {dx:.4f} ± {results['simple_offset_stats']['dx_std']:.4f} m
      Δy = {dy:.4f} ± {results['simple_offset_stats']['dy_std']:.4f} m

    旋转角度:
      θ = {results['transformation']['rotation_degrees']:.6f}°

    匹配精度:
      平均误差:   {results['accuracy']['mean_error']:.4f} m
      中位数误差: {results['accuracy']['median_error']:.4f} m
      标准差:     {results['accuracy']['std_error']:.4f} m
      最大误差:   {results['accuracy']['max_error']:.4f} m
      最小误差:   {results['accuracy']['min_error']:.4f} m

    未匹配障碍物:
      Scenarios: {results['unmatched']['scenarios_count']}
      Data:      {results['unmatched']['data_count']}
    """

    ax6.text(0.1, 0.5, stats_text, fontproperties=font_props, fontsize=11,
            verticalalignment='center', bbox=dict(boxstyle='round',
            facecolor='wheat', alpha=0.5))

    plt.suptitle('障碍物匹配可视化分析', fontproperties=font_props, fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()

    # 保存图片
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ {output_file}")
    plt.close()


def visualize_vector_field(results: dict, output_file: str = 'visualizations/02_vector_field.png'):
    """可视化偏移向量场"""
    matched_pairs = results['matched_pairs']
    src_points = np.array([[p['src_pos']['x'], p['src_pos']['y']] for p in matched_pairs])
    dst_points = np.array([[p['dst_pos']['x'], p['dst_pos']['y']] for p in matched_pairs])

    fig, ax = plt.subplots(figsize=(12, 10))

    # 画源点
    ax.scatter(src_points[:, 0], src_points[:, 1],
              c='blue', s=150, alpha=0.6, label='Scenarios',
              marker='o', edgecolors='black', linewidths=1, zorder=3)

    # 画目标点
    ax.scatter(dst_points[:, 0], dst_points[:, 1],
              c='red', s=150, alpha=0.6, label='Data',
              marker='s', edgecolors='black', linewidths=1, zorder=3)

    # 画向量箭头
    for i in range(len(src_points)):
        dx_vec = dst_points[i, 0] - src_points[i, 0]
        dy_vec = dst_points[i, 1] - src_points[i, 1]

        ax.arrow(src_points[i, 0], src_points[i, 1],
                dx_vec, dy_vec,
                head_width=20, head_length=30,
                fc='green', ec='darkgreen',
                alpha=0.4, linewidth=1.5, zorder=2)

    ax.set_xlabel('X (m)', fontproperties=font_props, fontsize=14)
    ax.set_ylabel('Y (m)', fontproperties=font_props, fontsize=14)
    ax.set_title('障碍物变换向量场', fontproperties=font_props, fontsize=16, fontweight='bold')
    ax.legend(prop=font_props, fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ {output_file}")
    plt.close()


def visualize_obstacles_comparison(
    scenarios_obs: List[dict],
    data_obs: List[dict],
    results: dict,
    output_file: str = 'visualizations/03_obstacles_comparison.png'
):
    """详细的障碍物对比图（3子图布局）"""
    dx = results['simple_offset_stats']['dx_mean']
    dy = results['simple_offset_stats']['dy_mean']

    # 创建匹配字典
    matches = {}
    for pair in results['matched_pairs']:
        matches[pair['src_id']] = pair['dst_id']

    fig, axes = plt.subplots(1, 3, figsize=(24, 8))

    # 子图1: Scenarios 原始场景
    ax1 = axes[0]
    vehicle_count = 0
    object_count = 0
    for obs in scenarios_obs:
        if obs['type'] == 'vehicle':
            color = 'blue'
            vehicle_count += 1
        else:
            color = 'gray'
            object_count += 1

        draw_obstacle_box(ax1, obs['x'], obs['y'],
                         obs['length'], obs['width'], obs['heading'],
                         color, alpha=0.6)

    ax1.set_xlabel('X (m)', fontproperties=font_props, fontsize=12)
    ax1.set_ylabel('Y (m)', fontproperties=font_props, fontsize=12)
    ax1.set_title(f'Scenarios 场景\n车辆: {vehicle_count}, 障碍物: {object_count}',
                 fontproperties=font_props, fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')

    # 子图2: Data 场景
    ax2 = axes[1]
    type_colors = {
        'VEHICLE': 'red',
        'PEDESTRIAN': 'orange',
        'BICYCLE': 'purple',
        'UNKNOWN': 'gray',
        'UNKNOWN_MOVABLE': 'lightgray',
        'UNKNOWN_UNMOVABLE': 'darkgray'
    }

    type_counts = {}
    for obs in data_obs:
        type_counts[obs['type']] = type_counts.get(obs['type'], 0) + 1
        color = type_colors.get(obs['type'], 'gray')
        draw_obstacle_box(ax2, obs['x'], obs['y'],
                         obs['length'], obs['width'], obs['heading'],
                         color, alpha=0.5)

    ax2.set_xlabel('X (m)', fontproperties=font_props, fontsize=12)
    ax2.set_ylabel('Y (m)', fontproperties=font_props, fontsize=12)
    title_text = 'Data 场景\n' + ', '.join([f'{k}: {v}' for k, v in type_counts.items()])
    ax2.set_title(title_text, fontproperties=font_props, fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')

    # 子图3: 偏移后对比
    ax3 = axes[2]
    matched_data_ids = set(matches.values())

    # 绘制偏移后的scenarios障碍物（半透明）
    for obs in scenarios_obs:
        color = 'blue' if obs['type'] == 'vehicle' else 'gray'
        draw_obstacle_box(ax3, obs['x'] + dx, obs['y'] + dy,
                         obs['length'], obs['width'], obs['heading'],
                         color, alpha=0.3)

    # 绘制data中匹配的障碍物
    for obs in data_obs:
        if obs['id'] in matched_data_ids:
            color = type_colors.get(obs['type'], 'gray')
            draw_obstacle_box(ax3, obs['x'], obs['y'],
                             obs['length'], obs['width'], obs['heading'],
                             color, alpha=0.6)

    ax3.set_xlabel('X (m)', fontproperties=font_props, fontsize=12)
    ax3.set_ylabel('Y (m)', fontproperties=font_props, fontsize=12)
    ax3.set_title(f'偏移后叠加对比\nΔx={dx:.2f}m, Δy={dy:.2f}m, 匹配: {len(matched_data_ids)}',
                 fontproperties=font_props, fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect('equal')

    plt.suptitle('障碍物场景对比', fontproperties=font_props, fontsize=18, fontweight='bold')
    plt.tight_layout()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ {output_file}")
    plt.close()


def generate_all_visualizations(
    results_file: str = 'results/offset_results.json',
    scenarios_file: str = 'input/scenarios.json',
    data_file: str = 'input/data.json',
    output_dir: str = 'visualizations'
):
    """生成所有可视化图表"""
    print("\n" + "="*70)
    print("生成可视化图表")
    print("="*70)

    # 加载数据
    print("\n加载数据...")
    results = load_results(results_file)
    scenarios_obs = load_scenarios_data(scenarios_file)
    data_obs = load_data_obstacles(data_file)

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 生成图表
    print("\n生成图表:")
    visualize_matching_overview(results, f'{output_dir}/01_matching_overview.png')
    visualize_vector_field(results, f'{output_dir}/02_vector_field.png')
    visualize_obstacles_comparison(scenarios_obs, data_obs, results,
                                   f'{output_dir}/03_obstacles_comparison.png')

    print("\n" + "="*70)
    print("✅ 所有可视化完成!")
    print("="*70)
    print(f"\n生成的图表位于: {output_dir}/")
    print("  - 01_matching_overview.png   (匹配总览-6子图)")
    print("  - 02_vector_field.png        (向量场)")
    print("  - 03_obstacles_comparison.png (障碍物对比-3子图)")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='生成可视化图表')
    parser.add_argument('--results', default='results/offset_results.json',
                       help='匹配结果文件')
    parser.add_argument('--scenarios', default='input/scenarios.json',
                       help='Scenarios文件')
    parser.add_argument('--data', default='input/data.json',
                       help='Data文件')
    parser.add_argument('--output', default='visualizations',
                       help='输出目录')

    args = parser.parse_args()

    generate_all_visualizations(
        results_file=args.results,
        scenarios_file=args.scenarios,
        data_file=args.data,
        output_dir=args.output
    )


if __name__ == '__main__':
    main()
