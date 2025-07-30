from datetime import datetime
import re
import warnings
from .pygrok.pygrok import Grok

def find_time(line):
    """
    使用pygrok库来匹配时间戳
    :param line: 待匹配的字符串
    :return: 匹配到的时间戳字符串，如果没有匹配到则返回空字符串
    """
    try:
        
        grok = Grok()
        data = grok.match_time_try(line)
        if len(data) < 1:
            return ""
        re_k = None
        for k in data.keys():
            re_k = k
            break
        re_str = grok.predefined_patterns[re_k].regex_str
        t_grok = Grok(f"""({re_str})""")
        matches = t_grok.regex_obj.findall(line)

        if matches:
            return "".join(matches[0][0])
        else:
            return ""
    except Exception as e:
        print(f"find_time error {line}")
        return ""


def try_time(text):
    formats = [
        "%a %b %d %H:%M:%S GMT %Y",
        "%Y-%m-%d %H:%M:%S",  # 2025-05-06 14:30:00
        "%d/%b/%Y:%H:%M:%S %z",  # 06/May/2025:14:30:00 +0000
        "%Y-%m-%d %H:%M:%S.%f",  # 2025-05-06 14:30:00.123456
        "%Y-%m-%d %H:%M:%S,%f",  # 2025-05-06 14:30:00,123456
        "%Y-%m-%dT%H:%M:%S",  # 2025-05-06T14:30:00
        "%Y-%m-%dT%H:%M:%S.%f",  # 2025-05-06T14:30:00.123456
        "%Y-%m-%dT%H:%M:%S,%f",  # 2025-05-06T14:30:00,123456
        "%Y-%m-%dT%H:%M:%S%z",  # 2025-05-06T14:30:00+0000
        "%Y-%m-%dT%H:%M:%S.%f%z",  # 2025-05-06T14:30:00.123456+0000
        "%Y-%m-%dT%H:%M:%S,%f%z",  # 2025-05-06T14:30:00,123456+0000
        "%Y/%m/%d %H:%M:%S",  # 2025/05/06 14:30:00
        "%d-%b-%Y %H:%M:%S",  # 06-May-2025 14:30:00
        "%d-%m-%Y %H:%M:%S",  # 06-05-2025 14:30:00
        "%m/%d/%Y %H:%M:%S",  # 05/06/2025 14:30:00
        "%d %b %Y %H:%M:%S",  # 06 May 2025 14:30:00
        "%d %B %Y %H:%M:%S",  # 06 May 2025 14:30:00
        "%b %d %H:%M:%S",  # 06 May 14:30:00
        "%B %d %H:%M:%S",  # 06 May 14:30:00
        "%Y%m%d%H%M%S",  # 20250506143000
        "%y-%m-%d %H:%M:%S",  # 2025-05-06 14:30:00
        "%A, %d %B %Y %H:%M:%S",  # Tuesday, 06 May 2025 14:30:00
        "%a, %d-%b-%Y %H:%M:%S %z",  # Tue, 06-May-2025 14:30:00 +0800
        "%Y年%m月%d日 %H时%M分%S秒",  # 2025年05月06日 14时30分00秒
        "%m月%d日 %H时%M分%S秒",  # 05月06日 14时30分00秒
        "%Y-%m-%d",  # 2025-05-06
        "%y-%m-%d",  # 2025-05-06
        "%d-%m-%Y",  # 06-05-2025
        "%m/%d/%Y",  # 05/06/2025
        "%Y/%m/%d",  # 2025/05/06
        "%Y%m%d",  # 20250506
        "%Y年%m月%d日",  # 2025年05月06日
        "%m月%d日",  # 05月06日
    ]
    for f in formats:
        # 只对纯数字格式做长度校验
        if f in ("%Y%m%d%H%M%S", "%Y%m%d") and len(text) != len(
            f.replace("%Y", "0000")
            .replace("%m", "00")
            .replace("%d", "00")
            .replace("%H", "00")
            .replace("%M", "00")
            .replace("%S", "00")
        ):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                _t = datetime.strptime(text, f)
            if _t.year == 1900:
                new_year = 2025
                _t = _t.replace(year=new_year)
            ret = _t.strftime("%Y-%m-%d %H:%M:%S")
            return ret
        except ValueError:
            pass
    # 尝试解析时间戳格式
    try:
        # 秒级时间戳
        if len(text) == 10 and text.isdigit():
            return datetime.fromtimestamp(int(text)).strftime("%Y-%m-%d %H:%M:%S")
        # 毫秒级时间戳
        if len(text) == 13 and text.isdigit():
            return datetime.fromtimestamp(int(text) / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    except ValueError:
        pass
    return ""
