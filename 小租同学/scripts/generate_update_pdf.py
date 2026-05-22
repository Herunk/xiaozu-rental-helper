#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小租同学 - 更新说明 PDF 生成脚本
根据 TRACE 评测结果，生成一份说明更新内容的 PDF 文档
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


def generate_update_pdf(output_path):
    """生成更新说明 PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm, mm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        print("正在安装 reportlab...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "-q"])
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm, mm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

    # 注册中文字体
    font_path, font_name = detect_chinese_font()
    font_registered = False
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
            font_registered = True
        except Exception as e:
            print(f"中文字体注册失败：{e}，将使用 Helvetica 作为回退字体")

    if not font_registered:
        print("警告：未检测到中文字体，PDF 中的中文内容可能显示为方块/乱码！")

    actual_font = 'ChineseFont' if font_registered else 'Helvetica'

    # 创建 PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)

    # 定义样式
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                fontName=actual_font, fontSize=20,
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
                                leading=16, spaceAfter=6)

    bold_style = ParagraphStyle('Bold', parent=styles['Normal'],
                                fontName=actual_font, fontSize=10,
                                leading=16, spaceAfter=4)

    small_style = ParagraphStyle('Small', parent=styles['Normal'],
                                fontName=actual_font, fontSize=9,
                                leading=14, spaceAfter=4,
                                textColor=colors.HexColor('#555555'))

    # 辅助函数：安全包裹 Paragraph 文本（将中文引号转为 HTML 实体）
    def q(text):
        """将中文引号转为安全字符"""
        return text.replace('\u201c', '&ldquo;').replace('\u201d', '&rdquo;')

    # 构建内容
    story = []

    # 标题
    story.append(Paragraph("小租同学 - TRACE 评测修复更新说明", title_style))
    story.append(Paragraph("基于 SkillHub TRACE 五维评测体系", subtitle_style))
    story.append(Paragraph(f"更新日期：{datetime.now().strftime('%Y年%m月%d日')}", subtitle_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#eee')))
    story.append(Spacer(1, 0.5*cm))

    # 总览
    story.append(Paragraph("一、更新总览", heading_style))
    story.append(Paragraph(q(
        '根据 SkillHub TRACE 五维评测体系（Trust 信任 / Reliability 可靠性 / Adaptability 适用性 / '
        'Convention 规范性 / Effectiveness 有效性）的检查结果，本次共修复 <b>6 项问题</b>，'
        '涉及 <b>SKILL.md</b> 和 <b>generate_report.py</b> 两个文件。'
    ), body_style))
    story.append(Spacer(1, 0.3*cm))

    # 更新汇总表
    summary_data = [
        ['#', 'TRACE 维度', '严重程度', '修复状态', '涉及文件'],
        ['1', 'T + C', '高', '已修复', 'SKILL.md'],
        ['2', 'R', '高', '已修复', 'generate_report.py'],
        ['3', 'C', '高', '已修复', 'SKILL.md'],
        ['4', 'R', '中', '已修复', 'SKILL.md'],
        ['5', 'A', '中', '已修复', 'SKILL.md'],
        ['6', 'C', '低', '已修复', 'generate_report.py'],
    ]

    summary_table = Table(summary_data, colWidths=[1.2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), actual_font),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*cm))

    # 逐项详细说明
    story.append(Paragraph("二、逐项修复详情", heading_style))
    story.append(Spacer(1, 0.2*cm))

    # --- 修复项 1 ---
    story.append(Paragraph("<b>修复 #1：SKILL.md 中 fpdf2 与 reportlab 文档不一致</b>", bold_style))
    story.append(Paragraph("TRACE 维度：T（Trust 信任）+ C（Convention 规范性） | 严重程度：高", small_style))
    story.append(Paragraph(q(
        '问题：SKILL.md 第 190 行写\u201c如 fpdf2 未安装\u201d，但实际脚本 generate_report.py 使用的是 '
        'reportlab 库，文档与实现各说各话，用户按文档操作会产生困惑。'
    ), body_style))
    story.append(Paragraph(q(
        '修复：将 SKILL.md 中的\u201cfpdf2\u201d替换为\u201creportlab\u201d，命令从 '
        '<b>pip install fpdf2 -q</b> 改为 <b>pip install reportlab -q</b>。'
        '同时统一脚本注释中的报告名称为\u201c房源可租性评估报告\u201d。'
    ), body_style))
    story.append(Spacer(1, 0.3*cm))

    # --- 修复项 2 ---
    story.append(Paragraph("<b>修复 #2：中文字体失败时静默降级为 Helvetica</b>", bold_style))
    story.append(Paragraph("TRACE 维度：R（Reliability 可靠性） | 严重程度：高", small_style))
    story.append(Paragraph(q(
        '问题：generate_report.py 中字体注册失败时静默降级为 Helvetica（英文字体），'
        '导致中文内容在 PDF 中显示为方块/乱码，用户完全无感知。'
    ), body_style))
    story.append(Paragraph(q(
        '修复：(1) 字体注册 except 块中增加详细错误日志，打印具体失败原因和字体路径；'
        '(2) 降级后打印醒目警告\u201c未检测到中文字体，PDF 中的中文内容可能显示为方块/乱码\u201d；'
        '(3) SKILL.md 核心规则表中新增第 12 条，明确要求字体失败时打印警告而非静默降级。'
    ), body_style))
    story.append(Spacer(1, 0.3*cm))

    # --- 修复项 3 ---
    story.append(Paragraph("<b>修复 #3：缺少反模式与 FAQ 章节</b>", bold_style))
    story.append(Paragraph("TRACE 维度：C（Convention 规范性） | 严重程度：高", small_style))
    story.append(Paragraph(q(
        '问题：TRACE Convention 维度硬性要求包含反模式和 FAQ，当前 SKILL.md 完全没有。'
    ), body_style))
    story.append(Paragraph(q(
        '修复：在\u201c核心规则\u201d与\u201c对话引导\u201d之间新增\u201c反模式与 FAQ\u201d章节，包含：'
        '(1) 6 条常见误用场景及正确做法（如：把小租同学当法律顾问、只靠价格决定租不租等）；'
        '(2) 7 条 FAQ（照片模糊评分准吗、中文方块怎么办、支持视频吗等高频问题）。'
    ), body_style))
    story.append(Spacer(1, 0.3*cm))

    # --- 修复项 4 ---
    story.append(Paragraph("<b>修复 #4：缺少异常输入处理规范</b>", bold_style))
    story.append(Paragraph("TRACE 维度：R（Reliability 可靠性） | 严重程度：中", small_style))
    story.append(Paragraph(q(
        '问题：SKILL.md 完全没有定义空值、超长文本、特殊字符等异常输入的处理策略。'
    ), body_style))
    story.append(Paragraph(q(
        '修复：在核心规则表中新增第 8-12 条，明确定义：'
        '(1) 空值/缺失字段使用默认值，不中断流程；'
        '(2) 超长文本截断至 500 字并标注\u201c[已截断]\u201d；'
        '(3) 特殊字符须转义为 HTML 实体；'
        '(4) 非法文件格式明确提示不支持；'
        '(5) 字体失败时打印警告。'
    ), body_style))
    story.append(Spacer(1, 0.3*cm))

    # --- 修复项 5 ---
    story.append(Paragraph(q('<b>修复 #5：缺少触发条件示例和\u201c不做之事\u201d清单</b>'), bold_style))
    story.append(Paragraph("TRACE 维度：A（Adaptability 适用性） | 严重程度：中", small_style))
    story.append(Paragraph(q(
        '问题：用户不知道说什么话会触发这个 Skill，也不清楚哪些事做不了。'
    ), body_style))
    story.append(Paragraph(q(
        '修复：在\u201c三大核心功能\u201d之后新增\u201c触发条件\u201d章节，包含：'
        '(1) 4 类触发类型及对应的用户话术示例（验房/价格/问答/综合）；'
        '(2) 6 条\u201c不做之事\u201d清单及建议替代方案（如：不提供法律意见、不代签合同、不支持视频等）。'
    ), body_style))
    story.append(Spacer(1, 0.3*cm))

    # --- 修复项 6 ---
    story.append(Paragraph("<b>修复 #6：报告命名漂移</b>", bold_style))
    story.append(Paragraph("TRACE 维度：C（Convention 规范性） | 严重程度：低", small_style))
    story.append(Paragraph(q(
        '问题：脚本注释写\u201cPDF可租性报告\u201d，SKILL.md 写\u201cPDF可租性报告\u201d/\u201c房源可租性评估报告\u201d，'
        '命名不统一。'
    ), body_style))
    story.append(Paragraph(q(
        '修复：将 generate_report.py 脚本注释从\u201cPDF可租性报告生成脚本\u201d统一为'
        '\u201c房源可租性评估报告生成脚本\u201d。SKILL.md 参考资源描述同步更新。'
    ), body_style))
    story.append(Spacer(1, 0.5*cm))

    # 修改文件清单
    story.append(Paragraph("三、修改文件清单", heading_style))

    file_data = [
        ['文件路径', '修改类型', '修改内容摘要'],
        ['SKILL.md', '内容更新', 'fpdf2 \u2192 reportlab；新增触发条件章节；新增反模式与 FAQ 章节；新增异常输入处理规则（第8-12条）'],
        ['scripts/generate_report.py', '内容更新', '字体注册失败时打印详细错误日志；降级时打印警告信息；脚本注释标题统一'],
    ]

    file_table = Table(file_data, colWidths=[4*cm, 2.5*cm, 8*cm])
    file_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), actual_font),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    story.append(file_table)
    story.append(Spacer(1, 0.5*cm))

    # TRACE 评分变化
    story.append(Paragraph("四、TRACE 评分预估变化", heading_style))

    trace_data = [
        ['TRACE 维度', '修复前', '修复后（预估）', '提升原因'],
        ['T - Trust', '中', '高', '文档与实现已一致，不再误导用户'],
        ['R - Reliability', '中', '高', '字体失败有明确警告，异常输入有规范'],
        ['A - Adaptability', '良', '优', '新增触发示例和不做之事清单'],
        ['C - Convention', '中', '优', '新增反模式/FAQ，命名已统一'],
        ['E - Effectiveness', '良', '良', '无变化（原本已合格）'],
    ]

    trace_table = Table(trace_data, colWidths=[3*cm, 2*cm, 3*cm, 6.5*cm])
    trace_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), actual_font),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    story.append(trace_table)
    story.append(Spacer(1, 0.5*cm))

    # 页脚
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#eee')))
    story.append(Paragraph(q(
        f'<i>更新说明由 小租同学 自动生成 | {datetime.now().strftime("%Y-%m-%d %H:%M")}</i>'
    ), subtitle_style))

    # 生成 PDF
    doc.build(story)
    print(f"PDF 更新说明生成成功：{output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description='小租同学更新说明PDF生成器')
    parser.add_argument('--output', required=True, help='输出PDF文件路径')
    args = parser.parse_args()

    try:
        generate_update_pdf(args.output)
    except Exception as e:
        print(f"生成PDF失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
