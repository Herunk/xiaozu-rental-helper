#!/usr/bin/env python3
"""
租房价格对比计算脚本

本脚本为纯计算工具，不包含任何内置租房价格数据。
实际使用时，必须通过 WebSearch/WebFetch 实时获取用户询问城市的租房价格数据，
再将数据作为参数传入本脚本进行对比计算。

用法：
    python price_comparison.py --city 深圳 --district 南山区 --house-type 一室一厅 --rent 3500 --avg-price 3800 --min-price 3200 --max-price 4500
"""

import json
import argparse
import sys


# 户型名称标准化映射（保留此工具函数，无内置数据依赖）
HOUSE_TYPE_MAP = {
    "1": "一居室", "一室": "一居室", "一室一厅": "一居室", "1室": "一居室",
    "1室1厅": "一居室", "单间": "一居室", "开间": "一居室",
    "2": "两居室", "二室": "两居室", "两室": "两居室",
    "二室一厅": "两居室", "两室一厅": "两居室", "2室": "两居室",
    "2室1厅": "两居室", "2室2厅": "两居室",
    "3": "三居室", "三室": "三居室", "三室一厅": "三居室",
    "3室": "三居室", "3室1厅": "三居室", "3室2厅": "三居室",
}


def normalize_house_type(house_type_str):
    """将各种户型表述标准化为一居室/两居室/三居室"""
    if not house_type_str:
        return None
    house_type_str = house_type_str.strip().replace(" ", "")
    for key, value in HOUSE_TYPE_MAP.items():
        if key in house_type_str:
            return value
    # 默认：包含"室"字的取第一个数字
    if "室" in house_type_str:
        for char in house_type_str:
            if char.isdigit():
                num = int(char)
                if num == 1:
                    return "一居室"
                elif num == 2:
                    return "两居室"
                elif num >= 3:
                    return "三居室"
    return None


def compare_price(city, district, house_type_str, user_rent, avg_price, min_price=None, max_price=None):
    """
    对比用户租金与实时获取的同区域同类型房源参考均价。

    Args:
        city:          城市（实时获取，不限城市）
        district:       区域
        house_type_str: 户型描述
        user_rent:      用户租金（元/月）
        avg_price:      实时获取的参考均价（元/月，必填）
        min_price:      实时获取的价格下限（元/月，可选）
        max_price:      实时获取的价格上限（元/月，可选）

    Returns:
        dict: 包含对比结果的字典
    """
    # 参数校验
    if not avg_price or avg_price <= 0:
        return {
            "status": "missing_data",
            "avg_price": 0,
            "price_range": "",
            "diff_percent": 0,
            "conclusion": "缺少有效的参考均价数据，请先通过 WebSearch 实时查询该城市该区域的最新租房均价。",
            "recommendation": "搜索关键词示例：<城市> <区域> 租房均价 2026"
        }

    if not user_rent or user_rent <= 0:
        return {
            "status": "invalid_rent",
            "avg_price": avg_price,
            "price_range": f"{min_price or '?'}-{max_price or '?'}元/月",
            "diff_percent": 0,
            "conclusion": "请提供有效的租金数值。",
            "recommendation": ""
        }

    house_type = normalize_house_type(house_type_str) or house_type_str or "未知户型"
    diff_percent = round((user_rent - avg_price) / avg_price * 100, 1)
    price_range = f"{min_price or avg_price}-{max_price or avg_price}元/月" if (min_price or max_price) else f"约{avg_price}元/月"

    # 生成结论
    if user_rent < avg_price * 0.9:
        level = "偏低"
        conclusion = (f"该房源价格偏低，比 {city}{district} {house_type} 均价（{avg_price}元/月）低 {abs(diff_percent)}%。"
                      f"请务必核实房源真实性，警惕价格远低于市场的不正常房源。")
        recommendation = ("核实要点：\n1. 要求查看房产证或租房合同确认房东身份\n"
                          "2. 实地看房确认房源真实存在\n"
                          "3. 警惕要求提前转账或个人账户收款的房东")
    elif user_rent > avg_price * 1.1:
        level = "偏高"
        conclusion = (f"该房源价格偏高，比 {city}{district} {house_type} 均价（{avg_price}元/月）高 {diff_percent}%。"
                      f"建议尝试与房东协商，或考虑其他候选房源。")
        recommendation = ("砍价建议：\n1. 以周边同户型均价为谈判依据\n"
                          "2. 表明长租意愿，争取月付或季付优惠\n"
                          "3. 对比同区域其他房源，综合评估性价比")
    else:
        level = "合理"
        conclusion = (f"该房源价格合理，与 {city}{district} {house_type} 均价（{avg_price}元/月）基本一致。"
                      f"该区域参考租金范围：{price_range}。")
        recommendation = "价格合理，建议结合房源综合条件（装修、家电配套、周边配套等）做最终决定。"

    return {
        "status": "success",
        "city": city,
        "district": district,
        "house_type": house_type,
        "avg_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "price_range": price_range,
        "user_rent": user_rent,
        "diff_percent": diff_percent,
        "price_level": level,
        "conclusion": conclusion,
        "recommendation": recommendation,
    }


def main():
    parser = argparse.ArgumentParser(
        description="租房价格对比工具（全国通用，需配合实时数据使用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python price_comparison.py --city 深圳 --district 南山区 --house-type 一室一厅 \\
      --rent 3500 --avg-price 3800 --min-price 3200 --max-price 4500
        """
    )
    parser.add_argument("--city", required=True, help="城市（如：深圳、成都、武汉）")
    parser.add_argument("--district", required=True, help="区域（如：南山区、高新区）")
    parser.add_argument("--house-type", dest="house_type", required=True,
                        help="户型（如：一室一厅、两居室、三室两厅）")
    parser.add_argument("--rent", type=int, required=True, help="用户租金（元/月）")
    parser.add_argument("--avg-price", type=int, required=True,
                        help="实时获取的参考均价（元/月，必填）")
    parser.add_argument("--min-price", type=int, default=None,
                        help="实时获取的价格下限（元/月，可选）")
    parser.add_argument("--max-price", type=int, default=None,
                        help="实时获取的价格上限（元/月，可选）")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()

    result = compare_price(
        city=args.city,
        district=args.district,
        house_type_str=args.house_type,
        user_rent=args.rent,
        avg_price=args.avg_price,
        min_price=args.min_price,
        max_price=args.max_price
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("租房价格对比结果")
        print("=" * 40)
        print(f"  城市：{result.get('city', '')}")
        print(f"  区域：{result.get('district', '')}")
        print(f"  户型：{result.get('house_type', '')}")
        print(f"  参考均价：{result.get('avg_price', 0)} 元/月")
        if result.get('min_price') or result.get('max_price'):
            print(f"  参考范围：{result.get('price_range', '')}")
        print(f"  你的租金：{result.get('user_rent', 0)} 元/月")
        if result.get('diff_percent'):
            print(f"  与均价偏差：{result.get('diff_percent', 0):+.1f}%")
        print("=" * 40)
        print()
        print(result.get('conclusion', ''))
        if result.get('recommendation'):
            print()
            print(result['recommendation'])


if __name__ == "__main__":
    main()
