# -*- coding: utf-8 -*-
"""
报表图表生成模块
使用matplotlib生成饼图，支持中文显示（尽力而为）
"""

import io
import decimal
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免GUI依赖
import matplotlib.pyplot as plt


def _setup_chinese_font():
    """
    尝试设置中文字体支持
    如果找不到中文字体则使用默认字体，不会导致程序崩溃
    """
    # 尝试常见的中文字体
    chinese_fonts = [
        'SimHei',           # 黑体 (Windows)
        'Microsoft YaHei',  # 微软雅黑 (Windows)
        'WenQuanYi Micro Hei',  # 文泉驿微米黑 (Linux)
        'Noto Sans CJK SC',     # Noto思源黑体 (Linux)
        'PingFang SC',          # 苹方 (macOS)
        'Hiragino Sans GB',     # 冬青黑体 (macOS)
        'DejaVu Sans',          # 回退字体
    ]
    
    # 获取系统可用字体
    import matplotlib.font_manager as fm
    available_fonts = set([f.name for f in fm.fontManager.ttflist])
    
    # 查找可用的中文字体
    for font in chinese_fonts:
        if font in available_fonts:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            return font
    
    # 如果没找到中文字体，使用默认设置
    plt.rcParams['axes.unicode_minus'] = False
    return None


def generate_pie_chart(data_dict, title, total_label, total_value):
    """
    生成饼图PNG图像
    
    参数:
        data_dict: 数据字典 {标签: 数值}
        title: 图表标题
        total_label: 总计标签（如"总份数"或"总消费额"）
        total_value: 总计值
        
    返回:
        bytes: PNG图像的字节数据
    """
    # 尝试设置中文字体
    _setup_chinese_font()
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 如果没有数据，返回空图
    if not data_dict or all(v == 0 for v in data_dict.values()):
        ax.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=20)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        # 过滤掉值为0的项
        filtered_data = {k: float(v) for k, v in data_dict.items() if v > 0}
        
        if filtered_data:
            labels = list(filtered_data.keys())
            values = list(filtered_data.values())
            
            # 生成颜色
            colors = plt.cm.Set3(range(len(labels)))
            
            # 绘制饼图
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                pctdistance=0.75
            )
            
            # 设置字体大小
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_fontsize(9)
        else:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=20)
            ax.axis('off')
    
    # 设置标题
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # 添加总计信息
    total_text = f'{total_label}: {total_value}'
    fig.text(0.5, 0.02, total_text, ha='center', fontsize=12, fontweight='bold')
    
    # 调整布局
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
    # 保存到内存缓冲区
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    return buf.getvalue()
