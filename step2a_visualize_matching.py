#!/usr/bin/env python3
"""
可视化障碍物匹配结果
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib import patches

# 设置中文字体（Mac系统）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'STHeiti', 'Songti SC']  # Mac中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


def load_results(filepath: str = 'results/offset_results.json'):
    """加载匹配结果"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def visualize_matching(results: dict):
    """可视化匹配结果"""

    # 创建图形
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
    ax1.set_xlabel('X (m)', fontsize=12)
    ax1.set_ylabel('Y (m)', fontsize=12)
    ax1.set_title('原始位置对比', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
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

    ax2.set_xlabel('X (m)', fontsize=12)
    ax2.set_ylabel('Y (m)', fontsize=12)
    ax2.set_title(f'应用偏移后 (Δx={dx:.2f}m, Δy={dy:.2f}m)', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')

    # 子图3: 误差分布热图
    ax3 = plt.subplot(2, 3, 3)
    scatter = ax3.scatter(src_shifted[:, 0], src_shifted[:, 1],
                         c=errors, s=200, cmap='RdYlGn_r',
                         alpha=0.8, edgecolors='black', linewidths=1)
    cbar = plt.colorbar(scatter, ax=ax3)
    cbar.set_label('误差 (m)', fontsize=12)
    ax3.set_xlabel('X (m)', fontsize=12)
    ax3.set_ylabel('Y (m)', fontsize=12)
    ax3.set_title('匹配误差分布', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect('equal')

    # 子图4: 误差直方图
    ax4 = plt.subplot(2, 3, 4)
    ax4.hist(errors, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
    ax4.axvline(errors.mean(), color='red', linestyle='--', linewidth=2,
                label=f'平均值: {errors.mean():.2f}m')
    ax4.axvline(np.median(errors), color='green', linestyle='--', linewidth=2,
                label=f'中位数: {np.median(errors):.2f}m')
    ax4.set_xlabel('误差 (m)', fontsize=12)
    ax4.set_ylabel('频数', fontsize=12)
    ax4.set_title('误差分布直方图', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3, axis='y')

    # 子图5: 偏移向量分布
    ax5 = plt.subplot(2, 3, 5)
    offsets = dst_points - src_points
    ax5.scatter(offsets[:, 0], offsets[:, 1],
               c='purple', s=100, alpha=0.6, edgecolors='black')
    ax5.axvline(dx, color='red', linestyle='--', linewidth=2, label=f'Mean Δx={dx:.2f}m')
    ax5.axhline(dy, color='blue', linestyle='--', linewidth=2, label=f'Mean Δy={dy:.2f}m')
    ax5.set_xlabel('Δx (m)', fontsize=12)
    ax5.set_ylabel('Δy (m)', fontsize=12)
    ax5.set_title('偏移向量分布', fontsize=14, fontweight='bold')
    ax5.legend(fontsize=10)
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

    ax6.text(0.1, 0.5, stats_text, fontsize=11, family='Songti SC',
            verticalalignment='center', bbox=dict(boxstyle='round',
            facecolor='wheat', alpha=0.5))

    plt.suptitle('障碍物匹配可视化分析', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()

    # 保存图片
    output_file = 'visualizations/01_matching_overview.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"可视化结果已保存到: {output_file}")

    return fig


def visualize_detailed_matching(results: dict, num_show: int = 10):
    """详细可视化前N个匹配点对"""

    matched_pairs = results['matched_pairs'][:num_show]
    dx = results['simple_offset_stats']['dx_mean']
    dy = results['simple_offset_stats']['dy_mean']

    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    axes = axes.flatten()

    for i, pair in enumerate(matched_pairs):
        ax = axes[i]

        src_x, src_y = pair['src_pos']['x'], pair['src_pos']['y']
        dst_x, dst_y = pair['dst_pos']['x'], pair['dst_pos']['y']

        # 源点（蓝色）
        ax.scatter(src_x, src_y, c='blue', s=200, marker='o',
                  label='Scenarios', zorder=3, edgecolors='black', linewidths=2)

        # 偏移后的源点（绿色）
        src_shifted_x = src_x + dx
        src_shifted_y = src_y + dy
        ax.scatter(src_shifted_x, src_shifted_y, c='green', s=200, marker='^',
                  label='Shifted', zorder=3, edgecolors='black', linewidths=2)

        # 目标点（红色）
        ax.scatter(dst_x, dst_y, c='red', s=200, marker='s',
                  label='Data', zorder=3, edgecolors='black', linewidths=2)

        # 画箭头: 源点 -> 偏移后
        ax.annotate('', xy=(src_shifted_x, src_shifted_y), xytext=(src_x, src_y),
                   arrowprops=dict(arrowstyle='->', color='blue', lw=2, alpha=0.6))

        # 画箭头: 偏移后 -> 目标
        ax.annotate('', xy=(dst_x, dst_y), xytext=(src_shifted_x, src_shifted_y),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2, alpha=0.6))

        error = pair['transform_error']
        src_id = pair['src_id']
        dst_id = pair['dst_id']

        ax.set_title(f'#{i+1}: {src_id}→{dst_id}\n误差={error:.2f}m',
                    fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        if i == 0:
            ax.legend(fontsize=8, loc='upper left')

    plt.suptitle(f'前{num_show}个匹配点对详细视图', fontsize=16, fontweight='bold')
    plt.tight_layout()

    output_file = 'visualizations/02_detailed_matching.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"详细匹配可视化已保存到: {output_file}")

    return fig


def visualize_vector_field(results: dict):
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

    # 添加ID标签
    for i, pair in enumerate(matched_pairs):
        ax.text(src_points[i, 0], src_points[i, 1],
               pair['src_id'], fontsize=6, ha='right', va='bottom')

    ax.set_xlabel('X (m)', fontsize=14)
    ax.set_ylabel('Y (m)', fontsize=14)
    ax.set_title('障碍物变换向量场', fontsize=16, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()
    output_file = 'visualizations/03_vector_field.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"向量场可视化已保存到: {output_file}")

    return fig


def main():
    """主函数"""
    print("加载匹配结果...")
    results = load_results('offset_results_hungarian.json')

    print("\n生成可视化...")
    print("1. 总体匹配分析...")
    visualize_matching(results)

    print("2. 详细匹配视图...")
    visualize_detailed_matching(results, num_show=10)

    print("3. 向量场可视化...")
    visualize_vector_field(results)

    print("\n✅ 所有可视化完成!")
    print("生成的图片:")
    print("  - visualizations/01_matching_overview.png  (总体分析)")
    print("  - visualizations/02_detailed_matching.png  (详细匹配)")
    print("  - visualizations/03_vector_field.png       (向量场)")


if __name__ == '__main__':
    main()
