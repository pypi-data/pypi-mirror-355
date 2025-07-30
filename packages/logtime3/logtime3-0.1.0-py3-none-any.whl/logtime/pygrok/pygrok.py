try:
    import regex as re
except ImportError as e:
    # If you import re, grok_match can't handle regular expression containing atomic group(?>)
    import re

import os

from .config import LOG_SET, TIME_SET
from loguru import logger

DEFAULT_PATTERNS_DIRS = [os.path.dirname(os.path.abspath(__file__)) + "/patterns"]


class Grok(object):
    def __init__(self, pattern=None, custom_patterns_dir=None, custom_patterns={}):
        self.pattern = pattern
        self.custom_patterns_dir = custom_patterns_dir
        self.predefined_patterns = _reload_patterns(DEFAULT_PATTERNS_DIRS)

        custom_pats = {}
        if custom_patterns_dir is not None:
            custom_pats = _reload_patterns([custom_patterns_dir])

        for pat_name, regex_str in custom_patterns.items():
            custom_pats[pat_name] = Pattern(pat_name, regex_str)

        if len(custom_pats) > 0:
            self.predefined_patterns.update(custom_pats)

        self.type_mapper = {}
        py_regex_pattern = pattern
        
        if pattern is None:
            return
        while True:
            # Finding all types specified in the groks
            m = re.findall(r"%{(\w+):(\w+):(\w+)}", py_regex_pattern)
            for n in m:
                self.type_mapper[n[1]] = n[2]
            # replace %{pattern_name:custom_name} (or %{pattern_name:custom_name:type}
            # with regex and regex group name

            py_regex_pattern = re.sub(
                r"%{(\w+):(\w+)(?::\w+)?}",
                lambda m: "(?P<"
                + m.group(2)
                + ">"
                + self.predefined_patterns[m.group(1)].regex_str
                + ")",
                py_regex_pattern,
            )

            # replace %{pattern_name} with regex
            py_regex_pattern = re.sub(
                r"%{(\w+)}",
                lambda m: "(" + self.predefined_patterns[m.group(1)].regex_str + ")",
                py_regex_pattern,
            )

            if re.search(r"%{\w+(:\w+)?}", py_regex_pattern) is None:
                break

        self.regex_obj = re.compile(py_regex_pattern)
        self.py_regex_pattern = py_regex_pattern
        
    def match(self, text):
        """If text is matched with pattern, return variable names specified(%{pattern:variable name})
        in pattern and their corresponding values.If not matched, return None.
        custom patterns can be passed in by custom_patterns(pattern name, pattern regular expression pair)
        or custom_patterns_dir.
        """

        match_obj = self.regex_obj.search(text)

        if match_obj == None:
            return None
        matches = match_obj.groupdict()
        for key, match in matches.items():
            try:
                if self.type_mapper[key] == "int":
                    matches[key] = int(match)
                if self.type_mapper[key] == "float":
                    matches[key] = float(match)
            except (TypeError, KeyError) as e:
                pass
        return matches

    def match_try(self, text):
        # 初始化结果字典
        result = {}
        # 遍历LOG_SET中的每个项
        for item in LOG_SET:
            try:
                # 获取预定义模式的正则表达式字符串
                py_regex_pattern = self.predefined_patterns[item].regex_str
                while True:
                    # Finding all types specified in the groks
                    m = re.findall(r"%{(\w+):(\w+):(\w+)}", py_regex_pattern)
                    for n in m:
                        self.type_mapper[n[1]] = n[2]
                    # replace %{pattern_name:custom_name} (or %{pattern_name:custom_name:type}
                    # with regex and regex group name

                    py_regex_pattern = re.sub(
                        r"%{(\w+):(\w+)(?::\w+)?}",
                        lambda m: "(?P<"
                        + m.group(2)
                        + ">"
                        + self.predefined_patterns[m.group(1)].regex_str
                        + ")",
                        py_regex_pattern,
                    )

                    py_regex_pattern = re.sub(
                        r"%{(\w+):([\[\]\w]+)(?::[\[\]\w]+)?}",
                        lambda m: "(?P<"
                        + m.group(2).strip("[").strip("]").replace("][", "_")
                        + ">"
                        + self.predefined_patterns[m.group(1)].regex_str
                        + ")",
                        py_regex_pattern,
                    )

                    # replace %{pattern_name} with regex
                    py_regex_pattern = re.sub(
                        r"%{(\w+)}",
                        lambda m: "("
                        + self.predefined_patterns[m.group(1)].regex_str
                        + ")",
                        py_regex_pattern,
                    )

                    # replace %{pattern_name:[zeek][files][fuid]} with regex and regex group name
                    py_regex_pattern = re.sub(
                        r"%{(\w+)}",
                        lambda m: "("
                        + self.predefined_patterns[m.group(1)].regex_str
                        + ")",
                        py_regex_pattern,
                    )

                    if re.search(r"%{\w+(:\w+)?}", py_regex_pattern) is None:
                        break

                self.regex_obj = re.compile(py_regex_pattern)

                ret = self.match(text)
                if ret:
                    if len(ret.keys()) > 2:
                        result[item] = ret
            except Exception as e:
                logger.warning(f"name: {item}  error: {e}  re_str: {py_regex_pattern}")
                logger.exception(e)
                pass

        def count_empty_values(d):
            print(d)
            count = 0
            for v in d.values():
                if v not in [None, ""]:
                    count += 1
            return count

        sorted_result = sorted(
            result.items(), key=lambda x: count_empty_values(x[1]), reverse=True
        )
        return sorted_result

    def match_time_try(self, text):
        result = {}
        for item in TIME_SET.keys():
            try:
                py_regex_pattern = self.predefined_patterns[item].regex_str
                while True:
                    # Finding all types specified in the groks
                    m = re.findall(r"%{(\w+):(\w+):(\w+)}", py_regex_pattern)
                    for n in m:
                        self.type_mapper[n[1]] = n[2]
                    # replace %{pattern_name:custom_name} (or %{pattern_name:custom_name:type}
                    # with regex and regex group name

                    py_regex_pattern = re.sub(
                        r"%{(\w+):(\w+)(?::\w+)?}",
                        lambda m: "(?P<"
                        + m.group(2)
                        + ">"
                        + self.predefined_patterns[m.group(1)].regex_str
                        + ")",
                        py_regex_pattern,
                    )

                    py_regex_pattern = re.sub(
                        r"%{(\w+):([\[\]\w]+)(?::[\[\]\w]+)?}",
                        lambda m: "(?P<"
                        + m.group(2).strip("[").strip("]").replace("][", "_")
                        + ">"
                        + self.predefined_patterns[m.group(1)].regex_str
                        + ")",
                        py_regex_pattern,
                    )

                    # replace %{pattern_name} with regex
                    py_regex_pattern = re.sub(
                        r"%{(\w+)}",
                        lambda m: "("
                        + self.predefined_patterns[m.group(1)].regex_str
                        + ")",
                        py_regex_pattern,
                    )

                    # replace %{pattern_name:[zeek][files][fuid]} with regex and regex group name
                    py_regex_pattern = re.sub(
                        r"%{(\w+)}",
                        lambda m: "("
                        + self.predefined_patterns[m.group(1)].regex_str
                        + ")",
                        py_regex_pattern,
                    )

                    if re.search(r"%{\w+(:\w+)?}", py_regex_pattern) is None:
                        break

                self.regex_obj = re.compile(py_regex_pattern)

                ret = self.match(text)
                if ret is not None:
                    result[item] = ret
            except Exception as e:
                logger.warning(f"name: {item}  error: {e}  re_str: {py_regex_pattern}")
                logger.exception(e)
                pass

        return result
    
def _wrap_pattern_name(pat_name):
    return "%{" + pat_name + "}"


def _reload_patterns(patterns_dirs):
    """ """
    all_patterns = {}
    for dir in patterns_dirs:
        for f in os.listdir(dir):
            patterns = _load_patterns_from_file(os.path.join(dir, f))
            all_patterns.update(patterns)

    return all_patterns


def _load_patterns_from_file(file):
    """ """
    patterns = {}
    with open(file, "r") as f:
        for l in f:
            l = l.strip()
            if l == "" or l.startswith("#"):
                continue

            sep = l.find(" ")
            pat_name = l[:sep]
            regex_str = l[sep:].strip()
            field_dict = {}
            _field_data = re.findall(r"%{(\w+):(\w+)?}", regex_str)
            if _field_data:
                for _field in _field_data:
                    field_dict[_field[1]] = _field[0]
            pat = Pattern(pat_name, regex_str, field_dict)
            patterns[pat.pattern_name] = pat
    return patterns


class Pattern(object):
    """ """

    def __init__(self, pattern_name, regex_str, field_dict, sub_patterns={}):
        self.pattern_name = pattern_name
        self.regex_str = regex_str
        self.sub_patterns = sub_patterns  # sub_pattern name list
        self.field_dict = field_dict

    def __str__(self):
        return "<Pattern:%s,  %s,  %s>" % (
            self.pattern_name,
            self.regex_str,
            self.sub_patterns,
        )


if __name__ == "__main__":
    text = "Apr 20 01:45:01 aiserver CRON[862908]: pam_unix(cron:session): session closed for user root"
    # pattern = '%{SYSLOGTIMESTAMP:timestamp} .*? .*?%{INT:field}.*'
    # pattern = '%{SYSLOGTIMESTAMP:timestamp} %{SYSLOGHOST:host} %{GREEDYDATA:message}'
    text = '10.5.10.6 - - [21/May/2017:21:49:09 +0800] "GET /frame/login.jsp HTTP/1.1" 200 5369'
    # pattern = '%{COMMONAPACHELOG}'
    # text = '2014-11-03T18:28:32.450-0500 I NETWORK [initandlisten] waiting for connections on port 27017'
    # text = '2014-02-15T23:39:43.945958Z my-test-loadbalancer 192.168.131.39:2817 10.0.0.1:80 0.000073 0.001048 0.000057 200 200 0 29 "GET http://www.example.com:80/ HTTP/1.1"'
    text = '2015-04-10T08:11:09.865823Z us-west-1-production-media 49.150.87.133:55128 - -1 -1 -1 408 - 1294336 0 "PUT https://media.xxxyyyzzz.com:443/videos/F4_M-T4X0MM6Hvy1PFHesw HTTP/1.1"'
    # text = '1258867934.558264	F2xow8TIkvHG4Zz41	198.189.255.75	192.168.1.105	CHhAvVGS1DHFjwGM9	HTTP	0	EXTRACT	-	-	0.046240	-	F	54229	605292323	4244449	0	T	-	-	-	-	extract-1258867934.558264-HTTP-F2xow8TIkvHG4Zz41	T	4000'
    # text = "May 28 17:23:25 myHost kernel: [3124658.791874] Shorewall:FORWARD:REJECT:IN=eth2 OUT=eth2 SRC=1.2.3.4 DST=192.168.0.10 LEN=141 TOS=0x00 PREC=0x00 TTL=63 ID=55251 PROTO=UDP SPT=5353 DPT=5335 LEN=121"
    text = 'May 28 17:31:07 server Shorewall:net2fw:DROP:IN=eth1 OUT= MAC=00:02:b3:c7:2f:77:38:72:c0:6e:92:9c:08:00 SRC=127.0.0.1 DST=1.2.3.4 LEN=60 TOS=0x00 PREC=0x00 TTL=49 ID=6480 DF PROTO=TCP SPT=59088 DPT=8080 WINDOW=2920 RES=0x00 SYN URGP=0'
    text = 'May 28 17:31:07'
    text = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'
    grok = Grok()
    # logger.debug(grok.match(text))
    # logger.debug(grok.match_try(text))
    from pprint import pprint

    data = grok.match_try(text)
    for item in data:
        k = item[0]
        v = item[1]
        r = grok.predefined_patterns[k].regex_str
        logger.debug(f"name: {k}  re_str: {r}")
        logger.debug(grok.predefined_patterns[k].field_dict)
        pprint(v)

    data = grok.match_time_try(text)
    for item in data.keys():
        r = grok.predefined_patterns[item].regex_str
        logger.debug(f"name: {k}  re_str: {r}")