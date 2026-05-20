#!/usr/bin/env python3
"""
小租同学 - 房屋可租性 PDF 报告生成器
自动生成结构化验房评分报告，无需用户额外操作

用法：
  python generate_report.py --json '{"score":75,"level":"可以考虑","advantages":[...],"fatal":[...],"serious":[...],"minor":[...],"suggestions":[...],"confirm":[...]}'
  python generate_report.py --json @data.json          # 从文件读取
  echo '{...}' | python generate_report.py --stdin     # 从 stdin 读取
"""

import argparse
import json
import os
import platform
import sys
import tempfile
import warnings
from datetime import datetime
from pathlib import Path

# 抑制 fpdf2 废弃警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ── 自动安装 fpdf2 ──────────────────────────────────────────────
try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2", "-q"])
    from fpdf import FPDF


# ── 中文字体自动检测 ────────────────────────────────────────────
def _detect_chinese_fonts():
    """按优先级检测系统可用的中文字体，返回 (regular_path, bold_path, is_ttc)"""
    system = platform.system()

    if system == "Windows":
        candidates = [
            (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc"),   # 微软雅黑
            (r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simhei.ttf"),  # 黑体
            (r"C:\Windows\Fonts\simsun.ttc", r"C:\Windows\Fonts\simsun.ttc"),  # 宋体
        ]
    elif system == "Darwin":
        candidates = [
            ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/PingFang.ttc"),
            ("/System/Library/Fonts/STHeiti Light.ttc", "/System/Library/Fonts/STHeiti Medium.ttc"),
        ]
    else:  # Linux
        candidates = [
            ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
            ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        ]

    for regular, bold in candidates:
        if os.path.exists(regular):
            is_ttc = regular.lower().endswith(".ttc")
            return regular, bold if os.path.exists(bold) else regular, is_ttc

    return None, None, False


class RentalReportPDF(FPDF):
    """房屋可租性报告 PDF 生成器"""

    # 颜色定义
    C_PRIMARY = (41, 98, 255)
    C_FATAL = (220, 53, 69)
    C_SERIOUS = (255, 152, 0)
    C_MINOR = (160, 130, 0)
    C_GREEN = (40, 167, 69)
    C_GRAY = (108, 117, 125)
    C_DARK = (33, 37, 41)
    C_LIGHT = (248, 249, 250)
    C_WHITE = (255, 255, 255)

    def __init__(self):
        super().__init__()
        self._font_regular = "chinese"
        self._font_bold = "chinese_bold"
        self._chinese_ok = False
        self._setup_fonts()
        self.set_auto_page_break(auto=True, margin=20)

    def _setup_fonts(self):
        regular, bold, is_ttc = _detect_chinese_fonts()
        if regular:
            self._chinese_ok = True
            kw_reg = {"collection_font_number": 0} if is_ttc else {}
            kw_bold = {"collection_font_number": 0} if bold.lower().endswith(".ttc") else {}
            self.add_font(self._font_regular, "", regular, **kw_reg)
            self.add_font(self._font_bold, "B", bold, **kw_bold)
        else:
            self._chinese_ok = False
            self._font_regular = "Helvetica"
            self._font_bold = "Helvetica"

    @property
    def _avail_w(self):
        """当前页可用内容宽度"""
        return self.w - self.l_margin - self.r_margin

    def _sf(self, bold=False, size=10):
        """设置字体快捷方法"""
        name = self._font_bold if bold else self._font_regular
        style = "B" if bold else ""
        self.set_font(name, style, size)

    def _set_tc(self, color):
        """设置文字颜色"""
        self.set_text_color(*color)

    def _set_fc(self, color):
        """设置填充颜色"""
        self.set_fill_color(*color)

    # ── 原子绘制方法 ────────────────────────────────────────

    def _draw_section_title(self, title, color):
        """绘制章节标题（带左侧色条）"""
        self.ln(5)
        # 左侧色条
        self.set_draw_color(*color)
        self.set_line_width(1.2)
        x, y = self.l_margin, self.get_y()
        self.line(x, y, x, y + 7)
        # 标题文字
        self._sf(bold=True, size=12)
        self._set_tc(color)
        self.set_x(x + 4)
        self.cell(0, 8, title)
        self._set_tc(self.C_DARK)
        self.ln(10)
        # 底部细线
        self.set_draw_color(*self.C_LIGHT)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y() - 1, self.w - self.r_margin, self.get_y() - 1)

    def _draw_bullet(self, text, indent=10, bullet_char="-"):
        """绘制缩进条目"""
        self._sf(size=9)
        x_start = self.l_margin + indent
        self.set_x(x_start)
        cell_w = 6
        self.cell(cell_w, 6, bullet_char + " ")
        self.multi_cell(self._avail_w - indent - cell_w, 6, text)

    def _draw_tagged_item(self, text, tag_text, tag_color):
        """绘制带颜色标签的条目"""
        self._sf(size=9)
        indent = 8
        x_start = self.l_margin + indent
        self.set_x(x_start)
        # 标签
        tag_w = 24
        self._set_fc(tag_color)
        self._set_tc(self.C_WHITE)
        self.cell(tag_w, 6, tag_text, align="C", fill=True)
        self._set_tc(self.C_DARK)
        # 间隔
        self.cell(3, 6, "")
        # 文字
        self.multi_cell(self._avail_w - indent - tag_w - 3, 6, text)

    def _draw_label(self, text, x_start=None):
        """绘制小标签（如分类标题）"""
        self._sf(bold=True, size=9)
        self.set_x(x_start or (self.l_margin + 8))
        self.cell(0, 6, text)
        self.ln(7)

    # ── 报告各部分 ─────────────────────────────────────────

    def draw_header(self, data):
        """页眉区域"""
        self.add_page()
        # 品牌名
        self._sf(bold=True, size=20)
        self._set_tc(self.C_PRIMARY)
        self.cell(0, 14, "小租同学", align="C")
        self.ln(14)
        # 副标题
        self._sf(size=10)
        self._set_tc(self.C_GRAY)
        self.cell(0, 6, "房屋可租性评估报告", align="C")
        self.ln(8)
        self._set_tc(self.C_DARK)
        # 分隔线
        self.set_draw_color(*self.C_PRIMARY)
        self.set_line_width(0.6)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(5)
        # 日期
        self._sf(size=8)
        self._set_tc(self.C_GRAY)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 5, f"报告生成时间：{now}", align="R")
        self.ln(8)
        self._set_tc(self.C_DARK)

    def draw_score(self, data):
        """评分展示区"""
        score = data.get("score", 0)
        level = data.get("level", "")

        # 确定等级和颜色
        if score >= 80:
            color = self.C_GREEN
            level_text = level or "强烈推荐"
        elif score >= 60:
            color = self.C_SERIOUS
            level_text = level or "可以考虑"
        else:
            color = self.C_FATAL
            level_text = level or "不推荐"

        # 大分数
        self._sf(bold=True, size=42)
        self._set_tc(color)
        self.cell(55, 22, str(score), align="R")
        # /100
        self._sf(size=14)
        self._set_tc(self.C_GRAY)
        self.cell(20, 22, " /100")
        # 等级标签
        self.set_x(self.w - self.r_margin - 55)
        self._sf(bold=True, size=14)
        self._set_fc(color)
        self._set_tc(self.C_WHITE)
        self.cell(55, 14, level_text, align="C", fill=True)
        self.ln(20)
        self._set_tc(self.C_DARK)

    def draw_advantages(self, data):
        """优势分析"""
        items = data.get("advantages", [])
        if not items:
            return
        self._draw_section_title("优势分析", self.C_GREEN)
        for item in items:
            self._draw_bullet(item, indent=8, bullet_char="+")
        self.ln(2)

    def draw_problems(self, data):
        """问题分析"""
        fatal = data.get("fatal", [])
        serious = data.get("serious", [])
        minor = data.get("minor", [])
        if not (fatal or serious or minor):
            return

        self._draw_section_title("问题分析", self.C_FATAL)

        if fatal:
            self._set_tc(self.C_FATAL)
            self._draw_label("致命问题（-20分/项）", self.l_margin + 8)
            self._set_tc(self.C_DARK)
            for item in fatal:
                self._draw_tagged_item(item, "致命", self.C_FATAL)
            self.ln(2)

        if serious:
            self._set_tc(self.C_SERIOUS)
            self._draw_label("严重问题（-10分/项）", self.l_margin + 8)
            self._set_tc(self.C_DARK)
            for item in serious:
                self._draw_tagged_item(item, "严重", self.C_SERIOUS)
            self.ln(2)

        if minor:
            self._set_tc(self.C_MINOR)
            self._draw_label("一般问题（-5分/项）", self.l_margin + 8)
            self._set_tc(self.C_DARK)
            for item in minor:
                self._draw_tagged_item(item, "一般", self.C_MINOR)
            self.ln(2)

    def draw_suggestions(self, data):
        """建议措施"""
        items = data.get("suggestions", [])
        if not items:
            return
        self._draw_section_title("建议措施", self.C_PRIMARY)
        for item in items:
            self._draw_bullet(item, indent=8, bullet_char=">")
        self.ln(2)

    def draw_confirm(self, data):
        """补充确认事项"""
        items = data.get("confirm", [])
        if not items:
            return
        self._draw_section_title("补充确认事项", self.C_GRAY)
        for i, item in enumerate(items, 1):
            self._draw_bullet(item, indent=8, bullet_char=f"{i}.")
        self.ln(2)

    def draw_footer_note(self):
        """页脚免责声明"""
        self.ln(8)
        self.set_draw_color(*self.C_LIGHT)
        self.set_line_width(0.3)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)
        self._sf(size=7)
        self._set_tc(self.C_GRAY)
        self.multi_cell(0, 4,
            "\u672c\u62a5\u544a\u7531\u5c0f\u79df\u540c\u5b66 AI \u81ea\u52a8\u751f\u6210\uff0c\u4ec5\u4f9b\u53c2\u8003\uff0c\u4e0d\u6784\u6210\u6cd5\u5f8b\u5efa\u8bae\u3002"
            "\u623f\u5c4b\u5b9e\u9645\u60c5\u51b5\u8bf7\u4ee5\u73b0\u573a\u6838\u5b9e\u4e3a\u51c6\u3002"
            "\u8bc4\u5206\u57fa\u4e8e\u4e0a\u4f20\u6750\u6599\u7684\u53ef\u89c1\u4fe1\u606f\uff0c"
            "\u672a\u8986\u76d6\u90e8\u5206\u6807\u6ce8\u4e3a\u201c\u5efa\u8bae\u8865\u5145\u67e5\u770b\u201d\u3002")
        self._set_tc(self.C_DARK)

    def footer(self):
        """每页底部页码"""
        self.set_y(-15)
        self._sf(size=7)
        self._set_tc(self.C_GRAY)
        self.cell(0, 10,
            f"\u5c0f\u79df\u540c\u5b66 \u00b7 \u623f\u5c4b\u53ef\u79df\u6027\u8bc4\u4f30\u62a5\u544a  |  \u7b2c {self.page_no()} \u9875",
            align="C")
        self._set_tc(self.C_DARK)


def generate_report(data: dict, output_path: str = None) -> str:
    """
    生成 PDF 报告

    Args:
        data: 报告数据字典
            - score (int): 综合评分 0-100
            - level (str): 推荐等级文本
            - advantages (list[str]): 优势列表
            - fatal (list[str]): 致命问题列表
            - serious (list[str]): 严重问题列表
            - minor (list[str]): 一般问题列表
            - suggestions (list[str]): 建议措施列表
            - confirm (list[str]): 补充确认事项列表
        output_path: 输出路径，None 则自动生成临时文件

    Returns:
        生成的 PDF 文件绝对路径
    """
    pdf = RentalReportPDF()
    pdf.draw_header(data)
    pdf.draw_score(data)
    pdf.draw_advantages(data)
    pdf.draw_problems(data)
    pdf.draw_suggestions(data)
    pdf.draw_confirm(data)
    pdf.draw_footer_note()

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(tempfile.gettempdir(), "xiaozu_reports")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"rental_report_{timestamp}.pdf")

    pdf.output(output_path)
    return os.path.abspath(output_path)


# ── CLI 入口 ────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="小租同学 - 房屋可租性 PDF 报告生成器")
    parser.add_argument("--json", type=str, help="报告数据 JSON 字符串，或 @filepath 从文件读取")
    parser.add_argument("--stdin", action="store_true", help="从标准输入读取 JSON 数据")
    parser.add_argument("--output", "-o", type=str, help="输出 PDF 文件路径")
    args = parser.parse_args()

    if args.stdin:
        raw = sys.stdin.read()
    elif args.json:
        if args.json.startswith("@"):
            with open(args.json[1:], "r", encoding="utf-8") as f:
                raw = f.read()
        else:
            raw = args.json
    else:
        print("错误：请通过 --json 或 --stdin 提供报告数据", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误：{e}", file=sys.stderr)
        sys.exit(1)

    if "score" not in data:
        print("警告：缺少 score 字段，默认为 0", file=sys.stderr)
        data["score"] = 0

    output_path = generate_report(data, args.output)
    print(output_path)


if __name__ == "__main__":
    main()
