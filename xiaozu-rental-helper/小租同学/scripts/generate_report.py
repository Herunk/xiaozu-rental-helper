#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小租同学 - 房源可租性评估报告生成脚本
使用方法: python generate_report.py --json "@data.json" --output "report.pdf"
"""

import sys
import os
import json
import argparse
from datetime import datetime

def detect_chinese_font():
    """自动检测系统中文字体"""
    font_candidates = [
        # Windows
        (r"C:\Windows\Fonts\msyh.ttc", "msyh"),
        (r"C:\Windows\Fonts\simhei.ttf", "simhei"),
        (r"C:\Windows\Fonts\simsun.ttc", "simsun"),
        # macOS
        ("/System/Library/Fonts/PingFang.ttc", "pingfang"),
        ("/System/Library/Fonts/STHeiti Medium.ttc", "stheit"),
        # Linux
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "notosans"),
    ]
    
    for font_path, font_name in font_candidates:
        if os.path.exists(font_path):
            return font_path, font_name
    
    return None, None

def generate_pdf(json_data, output_path):
    """生成PDF报告"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        print("错误：未安装reportlab库，正在自动安装...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "-q"])
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    
    # 注册中文字体
    font_path, font_name = detect_chinese_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
            font_registered = True
        except Exception as e:
            print(f"⚠️ 中文字体注册失败（{font_path}）：{e}，将使用 Helvetica 作为回退字体（中文可能乱码）")
            font_registered = False
    else:
        font_registered = False
    
    actual_font = 'ChineseFont' if font_registered else 'Helvetica'
    if not font_registered:
        print("⚠️ 警告：未检测到中文字体，PDF 中的中文内容可能显示为方块/乱码！")
        print("   建议安装中文字体：Windows(微软雅黑) / macOS(苹方) / Linux(Noto Sans CJK)")

    # 创建PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4, 
                           leftMargin=2*cm, rightMargin=2*cm, 
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # 定义样式
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], 
                                fontName=actual_font, fontSize=18,
                                textColor=colors.HexColor('#1a73e8'),
                                alignment=TA_CENTER, spaceAfter=6)
    
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                   fontName=actual_font, fontSize=10,
                                   textColor=colors.grey,
                                   alignment=TA_CENTER, spaceAfter=20)
    
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                  fontName=actual_font, fontSize=14,
                                  textColor=colors.HexColor('#333333'),
                                  spaceBefore=15, spaceAfter=10)
    
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                fontName=actual_font, fontSize=10,
                                leading=16, spaceAfter=8)
    
    # 构建内容
    story = []
    
    # 标题
    story.append(Paragraph("房源可租性评估报告", title_style))
    story.append(Paragraph("小租同学 · 租房避坑助手", subtitle_style))
    story.append(Paragraph(f"报告生成时间：{datetime.now().strftime('%Y年%m月%d日')}", subtitle_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#eee')))
    story.append(Spacer(1, 0.3*cm))
    
    # 综合评分
    score = json_data.get('score', 0)
    level = json_data.get('level', '未评级')
    
    # 根据评分设置颜色
    if score >= 80:
        score_color = colors.HexColor('#28a745')
    elif score >= 60:
        score_color = colors.HexColor('#ffc107')
    else:
        score_color = colors.HexColor('#dc3545')
    
    story.append(Paragraph(f"<b>综合评分：{score}/100 | 推荐等级：{level}</b>", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    # 优势分析
    advantages = json_data.get('advantages', [])
    if advantages:
        story.append(Paragraph("一、优势分析", heading_style))
        adv_data = [['序号', '优势项目']]
        for i, adv in enumerate(advantages, 1):
            adv_data.append([str(i), adv])
        
        adv_table = Table(adv_data, colWidths=[2*cm, 12*cm])
        adv_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), actual_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(adv_table)
        story.append(Spacer(1, 0.3*cm))
    
    # 问题分析
    fatal = json_data.get('fatal', [])
    serious = json_data.get('serious', [])
    minor = json_data.get('minor', [])
    
    if fatal or serious or minor:
        story.append(Paragraph("二、问题分析", heading_style))
        
        if fatal:
            story.append(Paragraph("<b>🔴 致命问题（-20分/项）：</b>", body_style))
            for item in fatal:
                story.append(Paragraph(f"• {item}", body_style))
        
        if serious:
            story.append(Paragraph("<b>🟡 严重问题（-10分/项）：</b>", body_style))
            for item in serious:
                story.append(Paragraph(f"• {item}", body_style))
        
        if minor:
            story.append(Paragraph("<b>🟢 一般问题（-5分/项）：</b>", body_style))
            for item in minor:
                story.append(Paragraph(f"• {item}", body_style))
        
        story.append(Spacer(1, 0.3*cm))
    
    # 建议措施
    suggestions = json_data.get('suggestions', [])
    if suggestions:
        story.append(Paragraph("三、建议措施", heading_style))
        for i, sug in enumerate(suggestions, 1):
            story.append(Paragraph(f"{i}. {sug}", body_style))
        story.append(Spacer(1, 0.3*cm))
    
    # 补充确认事项
    confirm = json_data.get('confirm', [])
    if confirm:
        story.append(Paragraph("四、补充确认事项", heading_style))
        for item in confirm:
            story.append(Paragraph(f"□ {item}", body_style))
        story.append(Spacer(1, 0.3*cm))
    
    # 页脚
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#eee')))
    story.append(Paragraph("<i>报告由 小租同学 · 租房避坑助手 自动生成</i>", subtitle_style))
    story.append(Paragraph("<i>本报告仅供参考，具体房源情况请以实地看房为准</i>", subtitle_style))
    
    # 生成PDF
    doc.build(story)
    print(f"✅ PDF报告生成成功：{output_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description='小租同学PDF报告生成器')
    parser.add_argument('--json', required=True, help='JSON数据文件路径（使用@filename格式）')
    parser.add_argument('--output', required=True, help='输出PDF文件路径')
    
    args = parser.parse_args()
    
    # 处理@filepath格式
    json_path = args.json.lstrip('@')
    
    # 读取JSON数据
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败：{e}")
        sys.exit(1)
    
    # 生成PDF
    try:
        generate_pdf(json_data, args.output)
    except Exception as e:
        print(f"❌ 生成PDF失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
