#!/usr/bin/env python3
"""
障碍物详细可视化
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import patches

# 设置中文字体（Mac系统）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'STHeiti', 'Songti SC']
plt.rcParams['axes.unicode_minus'] = False


def load_scenarios_data():
    """加载scenarios.json数据"""
    with open('input/scenarios.json', 'r', encoding='utf-8') as f:
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


def load_data_obstacles():
    """加载data.json数据"""
    with open('input/data.json', 'r', encoding='utf-8') as f:
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


def load_matching_results():
    """加载匹配结果"""
    with open('results/offset_results.json', 'r', encoding='utf-8') as f:
        return json.load(f)


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
    polygon = patches.Polygon(rotated_corners, closed=True,
                             edgecolor=color, facecolor=color,
                             alpha=alpha, linewidth=2, label=label)
    ax.add_patch(polygon)

    # 绘制朝向箭头
    arrow_length = max(length, width) * 0.5
    dx = arrow_length * np.cos(heading)
    dy = arrow_length * np.sin(heading)
    ax.arrow(x, y, dx, dy, head_width=0.3, head_length=0.5,
            fc=color, ec=color, alpha=alpha+0.2, linewidth=1.5)


def visualize_obstacles_detailed():
    """详细可视化障碍物"""

    scenarios_obs = load_scenarios_data()
    data_obs = load_data_obstacles()
    results = load_matching_results()

    dx = results['simple_offset_stats']['dx_mean']
    dy = results['simple_offset_stats']['dy_mean']

    # 创建匹配字典
    matches = {}
    for pair in results['matched_pairs']:
        matches[pair['src_id']] = pair['dst_id']

    # 创建大图
    fig = plt.figure(figsize=(24, 12))

    # ==================== 子图1: Scenarios 原始场景 ====================
    ax1 = plt.subplot(2, 3, 1)

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

        # 添加ID标签
        ax1.text(obs['x'], obs['y'], obs['id'],
                fontsize=6, ha='center', va='center',
                color='white', fontweight='bold')

    ax1.set_xlabel('X (m)', fontsize=12)
    ax1.set_ylabel('Y (m)', fontsize=12)
    ax1.set_title(f'Scenarios 原始场景\n车辆: {vehicle_count}, 障碍物: {object_count}',
                 fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')

    # ==================== 子图2: Data 场景 ====================
    ax2 = plt.subplot(2, 3, 2)

    # 统计类型
    type_counts = {}
    for obs in data_obs:
        type_counts[obs['type']] = type_counts.get(obs['type'], 0) + 1

    # 颜色映射
    type_colors = {
        'VEHICLE': 'red',
        'PEDESTRIAN': 'orange',
        'BICYCLE': 'purple',
        'UNKNOWN': 'gray',
        'UNKNOWN_MOVABLE': 'lightgray',
        'UNKNOWN_UNMOVABLE': 'darkgray'
    }

    for obs in data_obs:
        color = type_colors.get(obs['type'], 'gray')
        draw_obstacle_box(ax2, obs['x'], obs['y'],
                         obs['length'], obs['width'], obs['heading'],
                         color, alpha=0.5)

    ax2.set_xlabel('X (m)', fontsize=12)
    ax2.set_ylabel('Y (m)', fontsize=12)
    title_text = 'Data 场景\n' + ', '.join([f'{k}: {v}' for k, v in type_counts.items()])
    ax2.set_title(title_text, fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')

    # ==================== 子图3: 偏移后对比 ====================
    ax3 = plt.subplot(2, 3, 3)

    # 绘制偏移后的scenarios障碍物
    for obs in scenarios_obs:
        color = 'blue' if obs['type'] == 'vehicle' else 'gray'
        draw_obstacle_box(ax3, obs['x'] + dx, obs['y'] + dy,
                         obs['length'], obs['width'], obs['heading'],
                         color, alpha=0.4)

    # 绘制data障碍物（只显示匹配的）
    matched_data_ids = set(matches.values())
    for obs in data_obs:
        if obs['id'] in matched_data_ids:
            color = type_colors.get(obs['type'], 'gray')
            draw_obstacle_box(ax3, obs['x'], obs['y'],
                             obs['length'], obs['width'], obs['heading'],
                             color, alpha=0.6)

    ax3.set_xlabel('X (m)', fontsize=12)
    ax3.set_ylabel('Y (m)', fontsize=12)
    ax3.set_title(f'偏移后叠加对比\nΔx={dx:.2f}m, Δy={dy:.2f}m',
                 fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect('equal')

    # ==================== 子图4: 障碍物尺寸分布 ====================
    ax4 = plt.subplot(2, 3, 4)

    # Scenarios
    s_lengths = [obs['length'] for obs in scenarios_obs]
    s_widths = [obs['width'] for obs in scenarios_obs]
    ax4.scatter(s_lengths, s_widths, c='blue', s=100, alpha=0.6,
               label='Scenarios', edgecolors='black', linewidths=1)

    # Data (只显示匹配的)
    d_lengths = [obs['length'] for obs in data_obs if obs['id'] in matched_data_ids]
    d_widths = [obs['width'] for obs in data_obs if obs['id'] in matched_data_ids]
    ax4.scatter(d_lengths, d_widths, c='red', s=100, alpha=0.6,
               label='Data (matched)', marker='s', edgecolors='black', linewidths=1)

    ax4.set_xlabel('长度 (m)', fontsize=12)
    ax4.set_ylabel('宽度 (m)', fontsize=12)
    ax4.set_title('障碍物尺寸分布', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    ax4.set_aspect('equal')

    # ==================== 子图5: 障碍物类型统计 ====================
    ax5 = plt.subplot(2, 3, 5)

    # Scenarios类型
    scenarios_types = {'vehicle': 0, 'object': 0}
    for obs in scenarios_obs:
        scenarios_types[obs['type']] += 1

    # Data类型
    data_types_matched = {}
    for obs in data_obs:
        if obs['id'] in matched_data_ids:
            data_types_matched[obs['type']] = data_types_matched.get(obs['type'], 0) + 1

    # 绘制柱状图
    width = 0.35
    labels = ['Scenarios\nVehicle', 'Scenarios\nObject', 'Data\nMatched']
    values = [scenarios_types['vehicle'], scenarios_types['object'], len(matched_data_ids)]
    colors = ['blue', 'gray', 'red']

    bars = ax5.bar(range(len(values)), values, color=colors, alpha=0.7,
                  edgecolor='black', linewidth=2)

    # 添加数值标签
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(val), ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax5.set_ylabel('数量', fontsize=12)
    ax5.set_title('障碍物类型统计', fontsize=14, fontweight='bold')
    ax5.set_xticks(range(len(labels)))
    ax5.set_xticklabels(labels, fontsize=10)
    ax5.grid(True, alpha=0.3, axis='y')

    # ==================== 子图6: 详细信息表格 ====================
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')

    info_text = f"""
    障碍物详细信息
    {'='*50}

    Scenarios 场景:
      总数: {len(scenarios_obs)}
      车辆: {scenarios_types['vehicle']}
      静态障碍物: {scenarios_types['object']}

      坐标范围:
        X: [{min(o['x'] for o in scenarios_obs):.2f}, {max(o['x'] for o in scenarios_obs):.2f}]
        Y: [{min(o['y'] for o in scenarios_obs):.2f}, {max(o['y'] for o in scenarios_obs):.2f}]

      尺寸范围:
        长度: [{min(o['length'] for o in scenarios_obs):.2f}, {max(o['length'] for o in scenarios_obs):.2f}] m
        宽度: [{min(o['width'] for o in scenarios_obs):.2f}, {max(o['width'] for o in scenarios_obs):.2f}] m

    Data 场景:
      总数: {len(data_obs)}
      匹配数: {len(matched_data_ids)}
      未匹配: {len(data_obs) - len(matched_data_ids)}

      类型分布:
    """

    for obj_type, count in sorted(type_counts.items()):
        info_text += f"        {obj_type}: {count}\n"

    info_text += f"""
      坐标范围:
        X: [{min(o['x'] for o in data_obs):.2f}, {max(o['x'] for o in data_obs):.2f}]
        Y: [{min(o['y'] for o in data_obs):.2f}, {max(o['y'] for o in data_obs):.2f}]

    匹配质量:
      匹配成功率: {len(matched_data_ids)/len(scenarios_obs)*100:.1f}%
      平均误差: {results['accuracy']['mean_error']:.2f} m
    """

    ax6.text(0.1, 0.5, info_text, fontsize=10,
            verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    plt.suptitle('障碍物详细分析', fontsize=18, fontweight='bold', y=0.98)
    plt.tight_layout()

    output_file = 'visualizations/04_obstacles_detailed.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"障碍物详细可视化已保存到: {output_file}")

    return fig


def visualize_obstacles_with_boxes():
    """绘制带边界框的障碍物细节图"""

    scenarios_obs = load_scenarios_data()
    data_obs = load_data_obstacles()
    results = load_matching_results()

    dx = results['simple_offset_stats']['dx_mean']
    dy = results['simple_offset_stats']['dy_mean']

    # 创建匹配字典
    matches = {}
    for pair in results['matched_pairs']:
        matches[pair['src_id']] = pair['dst_id']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 10))

    # 左图: Scenarios 所有障碍物带边界框
    for obs in scenarios_obs:
        color = 'blue' if obs['type'] == 'vehicle' else 'gray'
        draw_obstacle_box(ax1, obs['x'], obs['y'],
                         obs['length'], obs['width'], obs['heading'],
                         color, alpha=0.6)

        # 添加ID标签
        ax1.text(obs['x'], obs['y'], obs['id'],
                fontsize=8, ha='center', va='center',
                color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.5))

    ax1.set_xlabel('X (m)', fontsize=14)
    ax1.set_ylabel('Y (m)', fontsize=14)
    ax1.set_title('Scenarios 场景 - 所有障碍物（带朝向）', fontsize=16, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')

    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='blue', alpha=0.6, label='车辆'),
        Patch(facecolor='gray', alpha=0.6, label='静态障碍物')
    ]
    ax1.legend(handles=legend_elements, fontsize=12, loc='upper right')

    # 右图: 匹配对比（偏移后）
    matched_data_ids = set(matches.values())

    # 绘制偏移后的scenarios（半透明）
    for obs in scenarios_obs:
        color = 'blue' if obs['type'] == 'vehicle' else 'gray'
        draw_obstacle_box(ax2, obs['x'] + dx, obs['y'] + dy,
                         obs['length'], obs['width'], obs['heading'],
                         color, alpha=0.3)

    # 绘制data中匹配的障碍物
    for obs in data_obs:
        if obs['id'] in matched_data_ids:
            draw_obstacle_box(ax2, obs['x'], obs['y'],
                             obs['length'], obs['width'], obs['heading'],
                             'red', alpha=0.6)

            # 找到对应的scenarios ID
            src_id = [k for k, v in matches.items() if v == obs['id']][0]
            ax2.text(obs['x'], obs['y'], f"{src_id}→{obs['id']}",
                    fontsize=6, ha='center', va='center',
                    color='white', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.5))

    ax2.set_xlabel('X (m)', fontsize=14)
    ax2.set_ylabel('Y (m)', fontsize=14)
    ax2.set_title(f'匹配对比（偏移后）\nΔx={dx:.2f}m, Δy={dy:.2f}m',
                 fontsize=16, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')

    # 添加图例
    legend_elements2 = [
        Patch(facecolor='blue', alpha=0.3, label='Scenarios (偏移后)'),
        Patch(facecolor='red', alpha=0.6, label='Data (匹配)')
    ]
    ax2.legend(handles=legend_elements2, fontsize=12, loc='upper right')

    plt.suptitle('障碍物边界框可视化', fontsize=18, fontweight='bold')
    plt.tight_layout()

    output_file = 'visualizations/05_obstacles_boxes.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"障碍物边界框可视化已保存到: {output_file}")

    return fig


def main():
    """主函数"""
    print("生成障碍物可视化...")
    print("\n1. 障碍物详细分析图...")
    visualize_obstacles_detailed()

    print("2. 障碍物边界框图...")
    visualize_obstacles_with_boxes()

    print("\n✅ 障碍物可视化完成!")
    print("生成的图片:")
    print("  - visualizations/04_obstacles_detailed.png  (6子图详细分析)")
    print("  - visualizations/05_obstacles_boxes.png     (边界框可视化)")


if __name__ == '__main__':
    main()
