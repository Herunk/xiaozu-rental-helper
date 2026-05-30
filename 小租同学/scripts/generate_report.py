#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小租同学 - 房源可租性评估报告 PDF 生成脚本

=== 参数说明 ===
  --json JSON_FILE     JSON 数据文件路径（支持 @filepath 格式避免中文乱码）
  --output OUTPUT_DIR  输出 PDF 文件路径（绝对路径或相对路径）

=== 调用示例 ===
  python generate_report.py --json "@report_data.json" --output "report.pdf"

=== JSON 数据格式 ===
  {
    "score": 85,                    // int, 0-100, 必填
    "level": "强烈推荐",             // string, 必填
    "advantages": ["朝南采光好"],    // string[], 可选
    "fatal": ["疑似串串房"],        // string[], 可选
    "serious": ["商水商电"],        // string[], 可选
    "minor": ["插座不足"],          // string[], 可选
    "suggestions": ["建议实地看房"], // string[], 可选
    "confirm": ["确认水电类型"]     // string[], 可选
  }

=== 错误码对照表 ===
  0   - 成功
  1   - JSON 文件读取失败（文件不存在/格式错误/编码问题）
  2   - reportlab 库安装失败（pip install 失败，需手动安装）
  3   - 中文字体未检测到（PDF 中文可能乱码，但仍会尝试生成）
  4   - PDF 生成失败（输出目录无写入权限/磁盘空间不足/文件名非法）
  5   - 未知错误（打印完整 traceback）

=== 特殊字符转义完整列表 ===
  以下字符在写入 PDF 前自动转义为 HTML 实体：
  <   →  &lt;
  >   →  &gt;
  &   →  &amp;
  "   →  &quot;
  '   →  &#39;
  全角符号（自动转义）：
  《》 → 对应 HTML 实体
  【】 → 对应 HTML 实体
  Emoji（自动过滤或替换为文本描述）：
  😊 → [微笑]
  ⚠️ → ⚠
  ✅ → [√]
  ❌ → [×]
  🔴 → [红]
  🟡 → [黄]
  🟢 → [绿]
"""

import sys
import os
import json
import argparse
import re
from datetime import datetime

# === 特殊字符转义 ===

def escape_special_chars(text):
    """转义特殊字符为 HTML 实体，确保 reportlab 安全渲染"""
    if not text:
        return text

    # HTML 实体基础转义
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#39;')

    # 全角符号转义（reportlab 可能无法正确渲染）
    fullwidth_map = {
        '\uff1c': '&lt;',     # ＜
        '\uff1e': '&gt;',     # ＞
        '\uff06': '&amp;',    # ＆
        '\uff02': '&quot;',   # ＂
        '\uff07': '&#39;',    # ＇
        '\u300a': '《',       # 《
        '\u300b': '》',       # 》
        '\u3010': '【',       # 【
        '\u3011': '】',       # 】
        '\uff08': '(',        # （
        '\uff09': ')',        # ）
        '\u3001': '、',       # 、
        '\uff1a': ':',        # ：
    }
    for full, half in fullwidth_map.items():
        text = text.replace(full, half)

    # Emoji 安全处理：替换为文本描述或保留简写
    emoji_map = {
        '\U0001f534': '[红]',     # 🔴
        '\U0001f7e1': '[黄]',     # 🟡
        '\U0001f7e2': '[绿]',     # 🟢
        '\u26a0\ufe0f': '⚠',      # ⚠️
        '\u2705': '[√]',          # ✅
        '\u274c': '[×]',          # ❌
        '\u2757': '!!',           # ❗
        '\u2753': '?',            # ❓
        '\U0001f4f8': '[相机]',    # 📸
        '\U0001f4b0': '[钱]',     # 💰
        '\U0001f4cb': '[清单]',   # 📋
        '\U0001f3e0': '[房]',     # 🏠
        '\U0001f4c4': '[文档]',   # 📄
        '\U0001f4f7': '[照片]',   # 📷
        '\u2764\ufe0f': '[心]',   # ❤️
        '\u2b50': '[星]',         # ⭐
    }
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)

    # 去除其他无法安全渲染的 emoji（U+1F000 以上范围）
    text = re.sub(r'[\U0001F000-\U0001FFFF]', '', text)

    return text


# === 中文字体检测 ===

def detect_chinese_font():
    """自动检测系统中文字体，返回 (路径, 名称) 或 (None, None)"""
    font_candidates = [
        # Windows
        (r"C:\Windows\Fonts\msyh.ttc", "msyh"),
        (r"C:\Windows\Fonts\msyhbd.ttc", "msyhbd"),
        (r"C:\Windows\Fonts\simhei.ttf", "simhei"),
        (r"C:\Windows\Fonts\simsun.ttc", "simsun"),
        (r"C:\Windows\Fonts\STSONG.TTF", "stsong"),
        # macOS
        ("/System/Library/Fonts/PingFang.ttc", "pingfang"),
        ("/System/Library/Fonts/STHeiti Medium.ttc", "stheit"),
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", "hiragino"),
        # Linux
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "notosans"),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "notosans"),
        ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", "wqy"),
        ("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", "droid"),
    ]

    for font_path, font_name in font_candidates:
        if os.path.exists(font_path):
            return font_path, font_name

    return None, None


# === 依赖安装 ===

def ensure_reportlab():
    """确保 reportlab 已安装，返回 (success: bool, error_msg: str)"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        return True, None
    except ImportError:
        print("[安装] 未检测到 reportlab，正在自动安装...")
        import subprocess
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "reportlab", "-q"],
                timeout=120
            )
            # 重试导入
            from reportlab.lib.pagesizes import A4
            return True, None
        except subprocess.CalledProcessError as e:
            return False, (
                f"reportlab 自动安装失败（pip install reportlab）。\n"
                f"请手动执行：{sys.executable} -m pip install reportlab\n"
                f"错误详情：{e}"
            )
        except subprocess.TimeoutExpired:
            return False, "reportlab 自动安装超时（>120秒），请手动执行：pip install reportlab"


# === PDF 生成 ===

def generate_pdf(json_data, output_path):
    """生成 PDF 报告，返回 (success: bool, exit_code: int, error_msg: str)"""

    # Step 1: 确保依赖
    ok, err = ensure_reportlab()
    if not ok:
        return False, 2, f"❌ 依赖检查失败：{err}"

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Step 2: 注册中文字体
    font_path, font_name = detect_chinese_font()
    font_registered = False
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
            font_registered = True
            print(f"[字体] 已注册中文字体：{font_name} ({font_path})")
        except Exception as e:
            print(f"⚠️  [字体] 注册失败：{font_path} → {e}")
            print(f"    [字体] 建议安装中文字体：Windows(微软雅黑) / macOS(苹方) / Linux(Noto Sans CJK)")
    else:
        print("⚠️  [字体] 未检测到任何中文字体！PDF 中的中文可能显示为方块/乱码。")
        print("    [字体] 请安装中文字体后重新生成。")
        print("    [字体] Windows: 确保 C:\\Windows\\Fonts\\ 下有 msyh.ttc 或 simhei.ttf")
        print("    [字体] macOS: 确保 /System/Library/Fonts/PingFang.ttc 存在")
        print("    [字体] Linux: sudo apt install fonts-noto-cjk")

    actual_font = 'ChineseFont' if font_registered else 'Helvetica'

    # Step 3: 预处理数据（转义特殊字符）
    def sanitize_list(lst):
        if not lst:
            return []
        result = []
        for item in lst:
            sanitized = escape_special_chars(str(item))
            # 截断超长文本
            if len(sanitized) > 500:
                sanitized = sanitized[:500] + "[已截断]"
            result.append(sanitized)
        return result

    score = max(0, min(100, json_data.get('score', 0)))
    level = escape_special_chars(str(json_data.get('level', '未评级')))
    advantages = sanitize_list(json_data.get('advantages', []))
    fatal = sanitize_list(json_data.get('fatal', []))
    serious = sanitize_list(json_data.get('serious', []))
    minor = sanitize_list(json_data.get('minor', []))
    suggestions = sanitize_list(json_data.get('suggestions', []))
    confirm = sanitize_list(json_data.get('confirm', []))

    # Step 4: 验证输出路径
    output_dir = os.path.dirname(os.path.abspath(output_path))
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"[目录] 已创建输出目录：{output_dir}")
        except PermissionError:
            return False, 4, (
                f"❌ 无权限创建输出目录：{output_dir}\n"
                f"请检查目录权限或更换输出路径。"
            )
        except OSError as e:
            return False, 4, f"❌ 创建输出目录失败：{e}"

    if not os.access(output_dir or '.', os.W_OK):
        return False, 4, (
            f"❌ 输出目录无写入权限：{output_dir or '当前目录'}\n"
            f"请更换到有写入权限的目录。"
        )

    # Step 5: 生成 PDF
    try:
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)

        # 定义样式
        title_style = ParagraphStyle('Title', fontName=actual_font, fontSize=18,
                                    textColor=colors.HexColor('#1a73e8'),
                                    alignment=TA_CENTER, spaceAfter=6)

        subtitle_style = ParagraphStyle('Subtitle', fontName=actual_font, fontSize=10,
                                       textColor=colors.grey,
                                       alignment=TA_CENTER, spaceAfter=20)

        heading_style = ParagraphStyle('Heading', fontName=actual_font, fontSize=14,
                                      textColor=colors.HexColor('#333333'),
                                      spaceBefore=15, spaceAfter=10)

        body_style = ParagraphStyle('Body', fontName=actual_font, fontSize=10,
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
        if score >= 80:
            score_color = colors.HexColor('#28a745')
        elif score >= 60:
            score_color = colors.HexColor('#ffc107')
        else:
            score_color = colors.HexColor('#dc3545')

        story.append(Paragraph(f"<b>综合评分：{score}/100 | 推荐等级：{level}</b>", body_style))
        story.append(Spacer(1, 0.3*cm))

        # 优势分析
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
        if fatal or serious or minor:
            story.append(Paragraph("二、问题分析", heading_style))

            if fatal:
                story.append(Paragraph("<b>致命问题（-20分/项）：</b>", body_style))
                for item in fatal:
                    story.append(Paragraph(f"• {item}", body_style))

            if serious:
                story.append(Paragraph("<b>严重问题（-10分/项）：</b>", body_style))
                for item in serious:
                    story.append(Paragraph(f"• {item}", body_style))

            if minor:
                story.append(Paragraph("<b>一般问题（-5分/项）：</b>", body_style))
                for item in minor:
                    story.append(Paragraph(f"• {item}", body_style))

            story.append(Spacer(1, 0.3*cm))

        # 建议措施
        if suggestions:
            story.append(Paragraph("三、建议措施", heading_style))
            for i, sug in enumerate(suggestions, 1):
                story.append(Paragraph(f"{i}. {sug}", body_style))
            story.append(Spacer(1, 0.3*cm))

        # 补充确认事项
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

        # 生成 PDF
        doc.build(story)
        file_size = os.path.getsize(output_path)
        print(f"✅ [成功] PDF 报告生成：{output_path} ({file_size / 1024:.1f} KB)")
        if not font_registered:
            print("⚠️  [提醒] 中文字体未注册，PDF 中中文可能显示异常，建议安装中文字体后重新生成。")
        return True, 0, None

    except PermissionError as e:
        return False, 4, (
            f"❌ 无权限写入文件：{output_path}\n"
            f"请检查：1) 目录是否有写入权限  2) 文件是否被其他程序占用\n"
            f"错误详情：{e}"
        )
    except OSError as e:
        return False, 4, (
            f"❌ 写入文件失败（磁盘空间不足或路径无效）：{e}\n"
            f"请检查磁盘空间并确认输出路径有效。"
        )
    except Exception as e:
        import traceback
        return False, 5, (
            f"❌ PDF 生成失败（未知错误）：{e}\n"
            f"{traceback.format_exc()}"
        )


# === 主函数 ===

def main():
    parser = argparse.ArgumentParser(
        description='小租同学 PDF 报告生成器 v5.0',
        epilog="""
调用示例：
  python generate_report.py --json "@report_data.json" --output "report.pdf"

错误码：
  0 - 成功
  1 - JSON 文件读取失败
  2 - reportlab 安装失败
  3 - 中文字体未检测到（仍尝试生成）
  4 - PDF 写入失败（权限不足/磁盘满）
  5 - 未知错误
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--json', required=True, help='JSON 数据文件路径（支持 @filepath 格式）')
    parser.add_argument('--output', required=True, help='输出 PDF 文件路径')

    args = parser.parse_args()

    # 处理 @filepath 格式
    json_path = args.json.lstrip('@')

    # Step 1: 读取 JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print(f"[读取] JSON 数据文件：{json_path}")
    except FileNotFoundError:
        print(f"❌ [错误] JSON 文件不存在：{json_path}")
        print(f"   请检查文件路径是否正确。")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ [错误] JSON 格式错误：{e}")
        print(f"   请检查 JSON 文件语法是否正确（注意引号、逗号、括号配对）。")
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"❌ [错误] JSON 文件编码错误：{e}")
        print(f"   请确认文件编码为 UTF-8。")
        sys.exit(1)
    except Exception as e:
        print(f"❌ [错误] 读取 JSON 文件失败：{e}")
        sys.exit(1)

    # Step 2: 数据校验
    if not isinstance(json_data, dict):
        print("❌ [错误] JSON 根元素必须是对象（dict），不能是数组。")
        sys.exit(1)

    if 'score' not in json_data:
        print("⚠️  [警告] JSON 缺少 'score' 字段，使用默认值 0。")
        json_data['score'] = 0
    if 'level' not in json_data:
        print("⚠️  [警告] JSON 缺少 'level' 字段，使用默认值 '未评级'。")
        json_data['level'] = '未评级'

    # score 范围校验
    score = json_data.get('score', 0)
    if not isinstance(score, (int, float)):
        print(f"⚠️  [警告] score 值类型无效（{type(score).__name__}），使用默认值 0。")
        json_data['score'] = 0
    elif score < 0 or score > 100:
        print(f"⚠️  [警告] score 值超出 0-100 范围（{score}），已裁剪。")
        json_data['score'] = max(0, min(100, int(score)))

    # Step 3: 生成 PDF
    ok, exit_code, error_msg = generate_pdf(json_data, args.output)

    if not ok:
        print(error_msg)
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
