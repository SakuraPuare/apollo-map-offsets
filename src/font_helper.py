#!/usr/bin/env python3
"""
字体辅助模块
用于在 Docker 环境中加载中文字体
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path

# 全局字体属性对象
_font_props = None


def get_font_properties():
    """获取字体属性对象，用于显式设置文本字体"""
    global _font_props
    return _font_props


def setup_chinese_font():
    """
    设置中文字体
    优先使用本地 simhei.ttf，如果不存在则使用系统字体
    """
    global _font_props

    # 尝试加载本地 simhei.ttf
    local_font = Path(__file__).parent.parent / "simhei.ttf"

    if local_font.exists():
        # 注册本地字体
        fm.fontManager.addfont(str(local_font))

        # 创建字体属性对象
        _font_props = fm.FontProperties(fname=str(local_font))
        font_name = _font_props.get_name()

        # 强制设置所有字体相关参数
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = [font_name]
        plt.rcParams["axes.unicode_minus"] = False

        # 强制刷新字体缓存
        plt.rcParams["font.size"] = 10

        # 设置所有可能使用字体的组件
        plt.rcParams["xtick.labelsize"] = 10
        plt.rcParams["ytick.labelsize"] = 10
        plt.rcParams["legend.fontsize"] = 10
        plt.rcParams["axes.labelsize"] = 11
        plt.rcParams["axes.titlesize"] = 12
        plt.rcParams["figure.titlesize"] = 14

        print(f"✅ 使用本地字体: {font_name} ({local_font})")
        return font_name
    else:
        # 使用系统字体
        system_fonts = [
            "Noto Sans CJK SC",
            "WenQuanYi Zen Hei",
            "WenQuanYi Micro Hei",
            "SimHei",
            "Microsoft YaHei",
        ]

        # 尝试创建字体属性对象
        for font in system_fonts:
            try:
                _font_props = fm.FontProperties(family=font)
                break
            except Exception:
                continue

        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = system_fonts
        plt.rcParams["axes.unicode_minus"] = False

        print(f"⚠️  本地字体 {local_font} 不存在，使用系统字体")
        return system_fonts[0]
