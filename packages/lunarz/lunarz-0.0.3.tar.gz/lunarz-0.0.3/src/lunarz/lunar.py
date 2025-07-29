#!/usr/bin/env python3
import sys
import json
import datetime
import cnlunar

class LunarCalendar:
    """农历日历工具"""
    
    def __init__(self, date=None):
        """
        初始化农历日历
        
        :param date: 日期对象 (datetime.date/datetime.datetime)
                     默认为当前日期
        """
        if isinstance(date, datetime.date):
            date = datetime.datetime.combine(date, datetime.time(0, 0, 0))
        self.date = date or datetime.datetime.now()
        self.lunar = cnlunar.Lunar(self.date, godType='8char')
    
    def get_ganzhi(self):
        """获取年、月、日干支"""
        return {
            "year": self.lunar.year8Char,
            "month": self.lunar.month8Char,
            "day": self.lunar.day8Char
        }
    
    def get_lunar_day(self):
        """获取农历日期"""
        return self.lunar.lunarMonthCn + self.lunar.lunarDayCn
    
    def get_solar_term_info(self):
        """获取当前节气信息或距离下一个节气的天数"""
        try:
            today = self.lunar.date
            year = today.year
            
            # 检查今日是否是节气
            current_terms = self.lunar.get_todaySolarTerms()
            if current_terms != '无' and current_terms:
                return current_terms
            
            # 获取下一个节气
            next_term = self.lunar.nextSolarTerm
            if next_term:
                next_year = self.lunar.nextSolarTermYear
                next_month, next_day = self.lunar.nextSolarTermDate
                next_date = datetime.date(next_year, next_month, next_day)
                days_to_next = (next_date - today.date()).days
            
            # 获取上一个节气
            solar_terms = self.lunar.thisYearSolarTermsDic.copy()
            if today.month == 1 and today.day < 5:  # 年初处理
                prev_year_lunar = cnlunar.Lunar(datetime.datetime(year-1, 12, 31), godType='8char')
                solar_terms = prev_year_lunar.thisYearSolarTermsDic
            
            # 查找最近的上一个节气
            prev_term = None
            prev_month, prev_day = 0, 0
            for term, (m, d) in solar_terms.items():
                term_date = datetime.date(year, m, d)
                if m < today.month or (m == today.month and d < today.day):
                    if not prev_term or (term_date > datetime.date(year, prev_month, prev_day)):
                        prev_term = term
                        prev_month, prev_day = m, d
            
            # 处理年初情况（使用上年的冬至）
            if not prev_term:
                prev_term = "冬至"
                prev_month, prev_day = 12, 22
                prev_date = datetime.date(year-1, prev_month, prev_day)
                days_since_prev = (today.date() - prev_date).days
            else:
                prev_date = datetime.date(year, prev_month, prev_day)
                days_since_prev = (today.date() - prev_date).days
            
            # 格式化输出
            if prev_term and next_term and days_since_prev > 0 and days_to_next > 0:
                return f"{prev_term}第{days_since_prev}天，{days_to_next}天后{next_term}"
            elif prev_term and days_since_prev > 0:
                return f"{prev_term}第{days_since_prev}天"
            elif next_term and days_to_next > 0:
                return f"{days_to_next}天后{next_term}"
            
            return ""
        
        except Exception:
            return ""
    
    def get_fasting_info(self):
        """获取斋日信息（今日状态或下一斋日）"""
        try:
            ret = ""
            lunar_day = self.lunar.lunarDay
            # 直接调用 getMonthLeapMonthLeapDays
            month_day, leap_month, leap_day = self.lunar.getMonthLeapMonthLeapDays()
            
            fasting_days = [1, 8, 14, 15, 18, 23, 24, 28, 29, 30]
            lunar_day_cn = {
                1: "初一", 8: "初八", 14: "十四", 15: "十五", 18: "十八",
                23: "廿三", 24: "廿四", 28: "廿八", 29: "廿九", 30: "三十"
            }
            
            # 今日是斋日
            if lunar_day in fasting_days:
                ret += "十斋日"
            
            # 查找本月内下一个斋日
            next_fasting = None
            for day in fasting_days:
                if day > lunar_day:
                    next_fasting = day
                    break
            
            # 计算距离
            if next_fasting:
                days_until = next_fasting - lunar_day
                day_name = lunar_day_cn.get(next_fasting, f"{next_fasting}日")
                if ret:
                    return ret + f", 下次于{days_until}天后"
                return f"十斋日于{days_until}天后"
            else:
                # 跨月到下月初一
                days_until = (month_day - lunar_day) + 1
                if ret:
                    return ret + f", 下次于{days_until}天后"
                return f"十斋日于{days_until}天后"
                
        except Exception:
            return ""

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='农历日历工具')
    parser.add_argument('--date', type=str, help='日期 (YYYY-MM-DD)')
    parser.add_argument('--field', type=str, 
                        choices=['lunar', 'ganzhi', 'solar_term', 'fasting'], 
                        help='输出特定字段')
    
    args = parser.parse_args()
    
    # 解析日期
    date_obj = None
    if args.date:
        try:
            date_obj = datetime.datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"错误: 无效的日期格式 '{args.date}'")
            sys.exit(1)
    
    # 创建日历对象
    lunar_cal = LunarCalendar(date_obj)
    
    # 处理字段请求
    if args.field == 'lunar':
        print(lunar_cal.get_lunar_day())
    elif args.field == 'ganzhi':
        ganzhi = lunar_cal.get_ganzhi()
        print(f"{ganzhi['year']} {ganzhi['month']} {ganzhi['day']}")
    elif args.field == 'solar_term':
        print(lunar_cal.get_solar_term_info())
    elif args.field == 'fasting':
        print(lunar_cal.get_fasting_info())
    else:
        # 默认输出完整JSON
        result = {
            "lunar": lunar_cal.get_lunar_day(),
            "ganzhi": lunar_cal.get_ganzhi(),
            "solar_term": lunar_cal.get_solar_term_info(),
            "fasting": lunar_cal.get_fasting_info()
        }
        print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
