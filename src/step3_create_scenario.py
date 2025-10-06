#!/usr/bin/env python3
"""
根据 data.json 创建新的场景文件
使用 scenarios.json 作为模板，替换为 data.json 中的障碍物数据
"""

import json
import copy
import argparse
import hashlib
import time
from typing import Dict, List


def load_json(filepath: str) -> dict:
    """加载 JSON 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict, filepath: str):
    """保存 JSON 文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def map_object_type(data_type: str) -> tuple:
    """
    将 data.json 中的类型映射到 scenarios.json 格式

    Args:
        data_type: data.json 中的类型（如 VEHICLE, UNKNOWN_UNMOVABLE 等）

    Returns:
        (entity_type, dimensions) 元组
        entity_type: 'vehicle' 或 'unknownUnmovableObject'
    """
    # 类型映射
    if data_type in ['VEHICLE']:
        return 'vehicle', 'vehicle'
    elif data_type in ['PEDESTRIAN']:
        return 'pedestrian', 'pedestrian'
    elif data_type in ['BICYCLE']:
        return 'bicycle', 'miscObject'
    else:
        # UNKNOWN, UNKNOWN_MOVABLE, UNKNOWN_UNMOVABLE 等
        return 'unknownUnmovableObject', 'miscObject'


def create_scenario_object(new_id: str, original_id: str, obj_data: dict) -> dict:
    """
    创建 scenarioObject

    Args:
        new_id: 新的障碍物 ID（连续递增）
        original_id: data.json 中的原始 ID
        obj_data: data.json 中的障碍物数据

    Returns:
        scenarioObject 字典
    """
    entity_type, catalog_type = map_object_type(obj_data['type'])

    # 根据类型生成名称
    type_prefix = {
        'vehicle': 'vehicle',
        'pedestrian': 'pedestrian',
        'unknownUnmovableObject': 'object'
    }.get(entity_type, 'object')

    scenario_obj = {
        "name": f"{type_prefix}_{new_id}",
        "id": new_id,
        "entityObject": {}
    }

    # 构建边界框
    bounding_box = {
        "center": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
        },
        "dimensions": {
            "length": obj_data['length'],
            "width": obj_data['width'],
            "height": obj_data['height']
        }
    }

    # 根据类型构建实体对象
    if entity_type == 'vehicle':
        scenario_obj["entityObject"]["vehicle"] = {
            "name": "",
            "vehicleCategory": "car",
            "boundingBox": bounding_box,
            "performance": {
                "maxSpeed": 69.444,
                "maxAcceleration": 200,
                "maxDeceleration": 10.0
            },
            "axles": {
                "frontAxle": {
                    "maxSteering": 0.5,
                    "wheelDiameter": 0.8,
                    "trackWidth": 1.68,
                    "positionX": 2.98,
                    "positionZ": 0.4
                },
                "rearAxle": {
                    "maxSteering": 0.0,
                    "wheelDiameter": 0.8,
                    "trackWidth": 1.68,
                    "positionX": 0.0,
                    "positionZ": 0.4
                }
            },
            "properties": {
                "property": [
                    {
                        "name": "original_id",
                        "value": str(original_id)
                    }
                ]
            }
        }
    elif entity_type == 'pedestrian':
        scenario_obj["entityObject"]["pedestrian"] = {
            "name": "",
            "mass": 80.0,
            "model": "walker.pedestrian.0001",
            "pedestrianCategory": "pedestrian",
            "boundingBox": bounding_box,
            "properties": {
                "property": [
                    {
                        "name": "original_id",
                        "value": str(original_id)
                    }
                ]
            }
        }
    else:
        scenario_obj["entityObject"]["unknownUnmovableObject"] = {
            "mass": 500.0,
            "boundingBox": bounding_box,
            "properties": {
                "property": [
                    {
                        "name": "original_id",
                        "value": str(original_id)
                    }
                ]
            }
        }

    return scenario_obj


def create_init_action(entity_ref: str, obj_data: dict) -> dict:
    """
    创建初始化动作（位置）

    Args:
        entity_ref: 实体引用 ID
        obj_data: data.json 中的障碍物数据

    Returns:
        private action 字典
    """
    return {
        "entityRef": {
            "entityRef": entity_ref
        },
        "privateActions": [
            {
                "teleportAction": {
                    "position": {
                        "worldPosition": {
                            "x": obj_data['positionX'],
                            "y": obj_data['positionY'],
                            "z": 0.0,
                            "h": obj_data['heading'],
                            "p": 0.0,
                            "r": 0.0
                        }
                    }
                }
            }
        ]
    }


def generate_scenario_id(original_id: str, suffix: str = "_offset") -> str:
    """
    生成新的场景 ID

    Args:
        original_id: 原始场景 ID
        suffix: 后缀标识

    Returns:
        新的场景 ID (24字符的十六进制字符串)
    """
    # 使用原始ID + 时间戳 + 后缀生成唯一ID
    content = f"{original_id}_{int(time.time())}_{suffix}"
    hash_obj = hashlib.md5(content.encode())
    return hash_obj.hexdigest()[:24]  # 取前24个字符


def update_map_filepath(filepath: str, map_name: str) -> str:
    """
    更新地图文件路径，指向偏移后的地图

    Args:
        filepath: 原始地图路径，如 "modules/map/data/xh_2025_gs_contest"
        map_name: 偏移后的地图名称，如 "xh_2025_gs_contest_offset"

    Returns:
        更新后的路径
    """
    from pathlib import Path
    path = Path(filepath)
    return str(path.parent / map_name)


def create_scenario_from_data(scenarios_template: dict, data_objects: List[dict],
                              match_results: dict = None, map_name: str = None) -> dict:
    """
    根据 data.json 创建新场景

    Args:
        scenarios_template: scenarios.json 模板
        data_objects: data.json 中的障碍物列表
        match_results: 匹配结果（可选），用于保留匹配的障碍物
        map_name: 偏移后的地图名称（可选），用于更新 filepath

    Returns:
        新的场景字典
    """
    # 深拷贝模板
    new_scenario = copy.deepcopy(scenarios_template)

    # 生成新的场景 ID
    original_id = new_scenario.get('id', 'unknown')
    new_id = generate_scenario_id(original_id, suffix="_offset")
    new_scenario['id'] = new_id
    print(f"生成新场景 ID: {new_id}")

    # 更新地图路径（如果提供了 map_name）
    if map_name:
        original_filepath = new_scenario.get('scenario', {}).get(
            'roadNetwork', {}
        ).get('logicFile', {}).get('filepath', '')

        if original_filepath:
            new_filepath = update_map_filepath(original_filepath, map_name)
            new_scenario['scenario']['roadNetwork']['logicFile']['filepath'] = new_filepath
            print(f"更新地图路径: {original_filepath} -> {new_filepath}")

    # 清空原有的障碍物
    new_scenario['scenario']['entities']['scenarioObjects'] = []
    new_scenario['scenario']['storyboard']['init']['actions']['privates'] = []

    # 如果提供了匹配结果，只处理匹配的障碍物
    if match_results:
        print(f"使用匹配结果，只保留 {len(match_results['matched_pairs'])} 个匹配的障碍物")
        # 按照匹配对的顺序处理障碍物
        id_to_obj = {str(obj['id']): obj for obj in data_objects}
        objects_to_process = []
        for pair in match_results['matched_pairs']:
            dst_id = pair['dst_id']
            if dst_id in id_to_obj:
                objects_to_process.append(id_to_obj[dst_id])
    else:
        print(f"处理所有 {len(data_objects)} 个障碍物")
        objects_to_process = data_objects

    # 创建新的障碍物（使用连续的新 ID）
    for idx, obj in enumerate(objects_to_process, start=1):
        original_id = str(obj['id'])
        new_id = str(idx)  # 从 1 开始的连续 ID

        # 创建 scenarioObject
        scenario_obj = create_scenario_object(new_id, original_id, obj)
        new_scenario['scenario']['entities']['scenarioObjects'].append(scenario_obj)

        # 创建初始化位置
        init_action = create_init_action(new_id, obj)
        new_scenario['scenario']['storyboard']['init']['actions']['privates'].append(init_action)

    print(f"创建了 {len(objects_to_process)} 个障碍物（ID: 1-{len(objects_to_process)}）")

    return new_scenario


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='根据 data.json 创建新的场景文件')
    parser.add_argument(
        '--template', '-t',
        type=str,
        default='input/scenarios.json',
        help='场景模板文件（默认: input/scenarios.json）')
    parser.add_argument(
        '--data', '-d',
        type=str,
        default='input/data.json',
        help='障碍物数据文件（默认: input/data.json）')
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='scenarios_new.json',
        help='输出场景文件（默认: scenarios_new.json）')
    parser.add_argument(
        '--match-results', '-m',
        type=str,
        default='results/offset_results.json',
        help='匹配结果文件（默认: results/offset_results.json）')
    parser.add_argument(
        '--all-objects',
        action='store_true',
        help='包含所有障碍物（默认只包含匹配的）')
    parser.add_argument(
        '--map-name',
        type=str,
        help='偏移后的地图名称（如 xh_2025_gs_contest_offset），用于更新场景中的地图路径')

    args = parser.parse_args()

    print("="*60)
    print("根据 data.json 创建新场景")
    print("="*60)

    # 加载模板
    print(f"\n加载场景模板: {args.template}")
    scenarios_template = load_json(args.template)

    # 加载障碍物数据
    print(f"加载障碍物数据: {args.data}")
    data = load_json(args.data)
    data_objects = data.get('object', [])
    print(f"  找到 {len(data_objects)} 个障碍物")

    # 加载匹配结果（如果提供）
    match_results = None
    if not args.all_objects:
        try:
            print(f"\n加载匹配结果: {args.match_results}")
            match_results = load_json(args.match_results)
            print(f"  匹配对数: {len(match_results['matched_pairs'])}")
        except FileNotFoundError:
            print(f"  未找到匹配结果文件: {args.match_results}")
            print("  将包含所有障碍物")

    # 创建新场景
    print("\n创建新场景...")
    new_scenario = create_scenario_from_data(
        scenarios_template,
        data_objects,
        match_results if not args.all_objects else None,
        map_name=args.map_name
    )

    # 保存 - 使用新的场景ID作为文件名
    new_scenario_id = new_scenario['id']
    output_path = args.output

    # 如果输出路径没有指定，使用新ID
    if args.output == 'scenarios_new.json':
        from pathlib import Path
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{new_scenario_id}.json")

    print(f"\n保存新场景: {output_path}")
    save_json(new_scenario, output_path)

    # 统计信息
    num_objects = len(new_scenario['scenario']['entities']['scenarioObjects'])
    num_vehicles = sum(1 for obj in new_scenario['scenario']['entities']['scenarioObjects']
                      if 'vehicle' in obj['entityObject'])
    num_static = sum(1 for obj in new_scenario['scenario']['entities']['scenarioObjects']
                    if 'unknownUnmovableObject' in obj['entityObject'])
    num_pedestrians = sum(1 for obj in new_scenario['scenario']['entities']['scenarioObjects']
                         if 'pedestrian' in obj['entityObject'])

    print("\n" + "="*60)
    print("场景创建完成！")
    print("="*60)
    print(f"场景 ID: {new_scenario_id}")
    print(f"总障碍物数: {num_objects}")
    print(f"  车辆: {num_vehicles}")
    print(f"  静态障碍物: {num_static}")
    print(f"  行人: {num_pedestrians}")
    if args.map_name:
        print(f"地图路径: modules/map/data/{args.map_name}")
    print(f"\n输出文件: {output_path}")


if __name__ == '__main__':
    main()
