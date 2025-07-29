from lunarz import LunarCalendar
import datetime

def test_2025_december_fasting(lc_2025_12):
    """测试2025年12月1日的斋日信息"""
    # 2025年12月1日 农历十月十二
    fasting = lc_2025_12.get_fasting_info()
    assert fasting == "十斋日于2天后"  # 10月14日

def test_2026_january_fasting(lc_2026_01):
    """测试2026年1月1日的斋日信息"""
    # 2026年1月1日 农历冬月(十一月)十三
    fasting = lc_2026_01.get_fasting_info()
    assert fasting == "十斋日于1天后"  # 十一月十四

def test_2025_june_fasting(lc_2025_06):
    """测试2025年6月1日的斋日信息"""
    # 2025年6月1日 农历五月初六
    fasting = lc_2025_06.get_fasting_info()
    assert fasting == "十斋日于2天后"  # 五月初八

def test_2024_february_fasting(lc_2024_02):
    """测试2024年2月1日的斋日信息(闰年)"""
    # 2024年2月1日 农历腊月廿二
    fasting = lc_2024_02.get_fasting_info()
    assert fasting == "十斋日于1天后"  # 腊月廿三

def test_tenzhai_transition(lc_2024_02):
    """测试月底到下月的斋日转换"""
    # 2024年2月9日 农历腊月三十
    lc = LunarCalendar(datetime.date(2024, 2, 9))
    fasting = lc.get_fasting_info()
    assert fasting == "十斋日, 下次于1天后"  # 正月初一

def test_ganzhi_system(lc_2025_12):
    """测试干支系统"""
    ganzhi = lc_2025_12.get_ganzhi()
    # 2025年12月1日 乙巳年十月十二
    # 年干支: 乙巳, 月干支: 丁亥, 日干支: 乙巳
    assert ganzhi['year'] == "乙巳"
    assert ganzhi['month'] == "丁亥"
    assert ganzhi['day'] == "甲辰"

def test_solar_terms():
    """测试节气系统"""
    # 2025年12月2日 十月十二
    lc = LunarCalendar(datetime.date(2025, 12, 2))
    # 小雪后, 大雪前
    term = lc.get_solar_term_info()
    assert "小雪第10天" in term and "大雪" in term

def test_today_fasting():
    """测试今日斋日状态"""
    # 在初一运行
    lc = LunarCalendar(datetime.date(2025, 6, 5))
    fasting = lc.get_fasting_info()
    if lc.lunar.lunarDay == 1:
        assert fasting == "今日斋日"
    else:
        assert fasting != "今日斋日"

def test_output_format(lc_2025_06):
    """测试全套输出格式"""
    result = {
        "lunar": lc_2025_06.get_lunar_day(),
        "ganzhi": lc_2025_06.get_ganzhi(),
        "solar_term": lc_2025_06.get_solar_term_info(),
        "fasting": lc_2025_06.get_fasting_info()
    }
    
    # 2025年6月1日 五月初六
    assert isinstance(result, dict)
    assert result["lunar"] == "五月小初六"
    assert len(result["ganzhi"]["year"]) == 2
    assert len(result["ganzhi"]["month"]) == 2
    assert len(result["ganzhi"]["day"]) == 2
    assert isinstance(result["solar_term"], str)
    assert isinstance(result["fasting"], str)
