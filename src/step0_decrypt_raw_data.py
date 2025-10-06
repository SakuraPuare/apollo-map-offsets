#!/usr/bin/env python3
"""
Step 0: 解密原始数据
从 input/raw.json 解密数据到 input/data.json
"""

import json
import base64
import hashlib
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def decrypt_sim_world(encrypted_data: str) -> dict:
    """
    解密 SimWorldUpdate 数据

    加密算法:
    1. Base64 编码
    2. 前 16 字节为 IV
    3. 密钥: SHA256("明月几时有")
    4. AES-CBC + Pkcs7 padding

    Args:
        encrypted_data: Base64 编码的加密数据

    Returns:
        解密后的 JSON 对象
    """
    if not encrypted_data:
        return {}

    # Step 1: Base64 解码
    encrypted_bytes = base64.b64decode(encrypted_data)

    # Step 2: 提取 IV (前 16 字节)
    iv = encrypted_bytes[:16]

    # Step 3: 提取密文 (16 字节之后)
    ciphertext = encrypted_bytes[16:]

    # Step 4: 生成密钥 (SHA256("明月几时有"))
    passphrase = "明月几时有"
    key = hashlib.sha256(passphrase.encode('utf-8')).digest()

    # Step 5: AES-CBC 解密
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_bytes = cipher.decrypt(ciphertext)

    # Step 6: 去除 PKCS7 填充
    unpadded_bytes = unpad(decrypted_bytes, AES.block_size)

    # Step 7: 解析 JSON
    decrypted_str = unpadded_bytes.decode('utf-8')
    return json.loads(decrypted_str)


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║              Step 0: 解密原始数据 (Decrypt Raw Data)              ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    # 输入输出文件路径
    input_file = Path('input/raw.json')
    output_file = Path('input/data.json')

    # 检查输入文件是否存在
    if not input_file.exists():
        print(f"❌ 错误: 输入文件不存在: {input_file}")
        print("\n请确保 input/raw.json 文件存在")
        return 1

    print(f"📖 读取加密数据: {input_file}")

    # 读取原始数据
    with open(input_file, 'r') as f:
        content = f.read().strip()

    # 尝试解析为 JSON
    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError:
        # 如果解析失败，尝试逐行解析（JSONL 格式）
        raw_data = [json.loads(line) for line in content.split('\n') if line.strip()]

    # 确保是列表格式
    if isinstance(raw_data, dict):
        raw_data = [raw_data]

    print(f"✅ 已读取 {len(raw_data)} 条记录")

    # 解密数据
    print("\n🔓 开始解密...")
    decrypted_data = []

    for i, record in enumerate(raw_data, 1):
        if isinstance(record, dict) and record.get('type') == 'SimWorldUpdate':
            try:
                # 解密 world 字段
                encrypted_world = record.get('world', '')
                decrypted_world = decrypt_sim_world(encrypted_world)

                # 更新记录
                record['world'] = decrypted_world

                if i % 10 == 0 or i == len(raw_data):
                    print(f"  进度: {i}/{len(raw_data)}")

            except Exception as e:
                print(f"⚠️  警告: 第 {i} 条记录解密失败: {e}")
                import traceback
                traceback.print_exc()
                continue

        decrypted_data.append(record)

    print(f"\n✅ 解密完成: {len(decrypted_data)} 条记录")

    # 提取 world 字段作为最终数据
    # data.json 应该是 world 的内容，而不是完整的 raw 数据
    final_data = None
    for record in decrypted_data:
        if isinstance(record, dict) and record.get('type') == 'SimWorldUpdate':
            final_data = record.get('world')
            break

    if not final_data:
        print("❌ 错误: 未找到有效的 SimWorldUpdate 数据")
        return 1

    # 保存解密后的数据
    print(f"\n💾 保存到: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 解密完成！数据已保存到 {output_file}")

    # 显示统计信息
    print("\n📊 统计信息:")
    print(f"  - 输入记录: {len(raw_data)}")
    print(f"  - SimWorldUpdate 记录: {sum(1 for r in decrypted_data if isinstance(r, dict) and r.get('type') == 'SimWorldUpdate')}")
    if isinstance(final_data, dict):
        print(f"  - 提取的障碍物数量: {len(final_data.get('object', []))}")

    return 0


if __name__ == '__main__':
    import sys
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
