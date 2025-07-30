import csv
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter

import chardet
import pandas as pd

from .pygrok import Grok


def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        raw_data = f.read(1024)  # 读取前 1024 字节
        result = chardet.detect(raw_data)
        return result["encoding"]


def is_jsonl(file_path):
    try:
        with open(file_path, "r", encoding=detect_encoding(file_path)) as f:
            for line in f:
                json.loads(line.strip())
        return True
    except Exception:
        return False


def is_xml(file_path):
    try:
        with open(file_path, "r", encoding=detect_encoding(file_path)) as f:
            ET.parse(f)
        return True
    except ET.ParseError:
        return False


def is_csv(file_path):
    try:
        with open(file_path, "r", encoding=detect_encoding(file_path)) as f:
            dialect = csv.Sniffer().sniff(f.read(1024))
            return dialect.delimiter == ","
    except Exception:
        return False


def is_tsv(file_path):
    try:
        with open(file_path, "r", encoding=detect_encoding(file_path)) as f:
            dialect = csv.Sniffer().sniff(f.read(1024))
            return dialect.delimiter == "\t"
    except Exception:
        return False


def is_delimited_by_semicolon_or_pipe(file_path):
    try:
        with open(file_path, "r", encoding=detect_encoding(file_path)) as f:
            sample = f.read(1024)
            return ";" in sample or "|" in sample
    except Exception:
        return False


def is_text(file_path):
    try:
        with open(file_path, "r", encoding=detect_encoding(file_path)) as f:
            f.read()
        return True
    except Exception:
        return False


def find_timestamps(file_path):
    timestamps = []
    timestamp_pattern = r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b"
    with open(file_path, "r", encoding=detect_encoding(file_path)) as f:
        for line in f:
            matches = re.findall(timestamp_pattern, line)
            timestamps.extend(matches)
    return timestamps


def flatten_dict(d, parent_key="", sep="."):
    """展平嵌套字典"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def preprocess_value(value):
    """预处理字段值，将不可哈希类型（如列表）转换为字符串"""
    if isinstance(value, list):
        return str(value)  # 将列表转换为字符串
    return value


def analyze_json_fields(file_path, max_rows=1000):
    # 读取 JSON 文件的前 max_rows 行
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_rows:
                break
            try:
                record = json.loads(line.strip())
                if isinstance(record, dict):
                    record = flatten_dict(record)  # 展平嵌套字典
                # 预处理字段值
                record = {k: preprocess_value(v) for k, v in record.items()}
                data.append(record)
            except json.JSONDecodeError:
                continue

    # 转换为 Pandas DataFrame
    df = pd.DataFrame(data)

    analysis_results = {}

    for column in df.columns:
        column_data = df[column].dropna()  # 去除空值
        total_count = len(column_data)

        if total_count == 0:
            continue

        # 字段类型
        field_type = column_data.map(type).mode()[0].__name__

        # 统计字段信息
        unique_values = column_data.nunique()
        min_value = (
            column_data.min() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        median_value = (
            column_data.median() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        max_value = (
            column_data.max() if pd.api.types.is_numeric_dtype(column_data) else None
        )

        # 计算 Top 10 及占比
        try:
            top_10 = Counter(column_data).most_common(10)
            top_10_percentages = [
                (value, count, count / total_count * 100) for value, count in top_10
            ]
        except TypeError:
            top_10_percentages = "无法统计（字段包含不可哈希类型）"

        # 保存结果
        analysis_results[column] = {
            "字段名称": column,
            "字段类型": field_type,
            "总数": total_count,
            "百分比": f"{(total_count / max_rows) * 100:.2f}%",
            "不同值数量": unique_values,
            "最小值": min_value,
            "中位数": median_value,
            "最大值": max_value,
            "Top 10 及占比": top_10_percentages,
        }

    return analysis_results


def analyze_csv_fields(file_path, delimiter=",", max_rows=1000):
    # 读取文件的前 max_rows 行
    data = pd.read_csv(file_path, delimiter=delimiter, nrows=max_rows)

    analysis_results = {}

    for column in data.columns:
        column_data = data[column].dropna()  # 去除空值
        total_count = len(column_data)

        if total_count == 0:
            continue

        # 字段类型
        field_type = column_data.map(type).mode()[0].__name__

        # 统计字段信息
        unique_values = column_data.nunique()
        min_value = (
            column_data.min() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        median_value = (
            column_data.median() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        max_value = (
            column_data.max() if pd.api.types.is_numeric_dtype(column_data) else None
        )

        # 计算 Top 10 及占比
        top_10 = Counter(column_data).most_common(10)
        top_10_percentages = [
            (value, count, count / total_count * 100) for value, count in top_10
        ]

        # 保存结果
        analysis_results[column] = {
            "字段名称": column,
            "字段类型": field_type,
            "总数": total_count,
            "百分比": f"{(total_count / max_rows) * 100:.2f}%",
            "不同值数量": unique_values,
            "最小值": min_value,
            "中位数": median_value,
            "最大值": max_value,
            "Top 10 及占比": top_10_percentages,
        }

    return analysis_results


def parse_xml_to_dataframe(file_path, max_rows=1000):
    """
    解析 XML 文件并将其转换为 Pandas DataFrame。
    仅解析前 max_rows 条记录。
    """
    rows = []
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ET.parse(f)
        root = tree.getroot()

        for i, element in enumerate(root):
            if i >= max_rows:
                break
            row = {}
            for child in element:
                row[child.tag] = child.text
            rows.append(row)

    return pd.DataFrame(rows)


def analyze_xml_fields(file_path, max_rows=1000):
    """
    分析 DataFrame 中的字段信息。
    """
    
    df = parse_xml_to_dataframe(file_path, max_rows=max_rows)
    analysis_results = {}

    for column in df.columns:
        column_data = df[column].dropna()  # 去除空值
        total_count = len(column_data)

        if total_count == 0:
            continue

        # 字段类型
        field_type = column_data.map(type).mode()[0].__name__

        # 统计字段信息
        unique_values = column_data.nunique()
        min_value = (
            column_data.min() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        median_value = (
            column_data.median() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        max_value = (
            column_data.max() if pd.api.types.is_numeric_dtype(column_data) else None
        )

        # 计算 Top 10 及占比
        top_10 = Counter(column_data).most_common(10)
        top_10_percentages = [
            (value, count, count / total_count * 100) for value, count in top_10
        ]

        # 保存结果
        analysis_results[column] = {
            "字段名称": column,
            "字段类型": field_type,
            "总数": total_count,
            "百分比": f"{(total_count / max_rows) * 100:.2f}%",
            "不同值数量": unique_values,
            "最小值": min_value,
            "中位数": median_value,
            "最大值": max_value,
            "Top 10 及占比": top_10_percentages,
        }

    return analysis_results


def analyze_delimited_file(file_path, delimiter=";", max_rows=1000):
    """
    读取以指定分隔符分割的文件，并统计字段信息。
    """
    # 读取文件的前 max_rows 行
    try:
        data = pd.read_csv(file_path, delimiter=delimiter, nrows=max_rows)
    except Exception as e:
        raise ValueError(f"无法读取文件，请检查分隔符是否正确。错误信息: {e}")

    analysis_results = {}

    for column in data.columns:
        column_data = data[column].dropna()  # 去除空值
        total_count = len(column_data)

        if total_count == 0:
            continue

        # 字段类型
        field_type = column_data.map(type).mode()[0].__name__

        # 统计字段信息
        unique_values = column_data.nunique()
        min_value = (
            column_data.min() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        median_value = (
            column_data.median() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        max_value = (
            column_data.max() if pd.api.types.is_numeric_dtype(column_data) else None
        )

        # 计算 Top 10 及占比
        top_10 = Counter(column_data).most_common(10)
        top_10_percentages = [
            (value, count, count / total_count * 100) for value, count in top_10
        ]

        # 保存结果
        analysis_results[column] = {
            "字段名称": column,
            "字段类型": field_type,
            "总数": total_count,
            "百分比": f"{(total_count / max_rows) * 100:.2f}%",
            "不同值数量": unique_values,
            "最小值": min_value,
            "中位数": median_value,
            "最大值": max_value,
            "Top 10 及占比": top_10_percentages,
        }

    return analysis_results


def analyze_grok_file(file_path):
    """
    使用 Grok 提取日志字段并统计字段信息。
    
    :param logs: 日志列表，每条日志为字符串
    :param pattern: Grok 模式
    :return: 提取字段的统计信息
    """
    with open(file_path, "r", encoding="utf-8") as f:
        logs = f.readlines()
    
        
    m_grok = Grok()
    _patter = m_grok.match_try(logs[0])[0]
    pattern_name = f"%{{{_patter[0]}}}"
    grok = Grok(pattern_name)
    extracted_data = []
    print(pattern_name)
    # 提取字段
    for log in logs:
        match = grok.match(log)
        if match:
            extracted_data.append(match)

    if not extracted_data:
        return "未提取到任何字段"

    # 转换为 Pandas DataFrame
    df = pd.DataFrame(extracted_data)

    # 字段统计
    analysis_results = {}
    for column in df.columns:
        column_data = df[column].dropna()  # 去除空值
        total_count = len(column_data)

        if total_count == 0:
            continue

        # 字段类型
        field_type = column_data.map(type).mode()[0].__name__

        # 统计字段信息
        unique_values = column_data.nunique()
        min_value = (
            column_data.min() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        median_value = (
            column_data.median() if pd.api.types.is_numeric_dtype(column_data) else None
        )
        max_value = (
            column_data.max() if pd.api.types.is_numeric_dtype(column_data) else None
        )

        # 计算 Top 10 及占比
        top_10 = Counter(column_data).most_common(10)
        top_10_percentages = [
            (value, count, count / total_count * 100) for value, count in top_10
        ]

        # 保存结果
        analysis_results[column] = {
            "字段名称": column,
            "字段类型": field_type,
            "总数": total_count,
            "百分比": f"{(total_count / len(df)) * 100:.2f}%",
            "不同值数量": unique_values,
            "最小值": min_value,
            "中位数": median_value,
            "最大值": max_value,
            "Top 10 及占比": top_10_percentages,
        }

    return analysis_results

if __name__ == "__main__":
    base_path = os.path.dirname(__file__)
    # 示例用法
    file_path = os.path.join(base_path, "eve.json")

    print("字符编码:", detect_encoding(file_path))
    print("是不是 JSONL:", is_jsonl(file_path))
    print("是不是 XML:", is_xml(file_path))
    print("是不是 CSV:", is_csv(file_path))
    print("是不是 TSV:", is_tsv(file_path))
    print("是不是以 ; 或 | 分割:", is_delimited_by_semicolon_or_pipe(file_path))
    print("样本是不是文本:", is_text(file_path))
    print("时间戳:", find_timestamps(file_path)[0])


    # file_path = os.path.join(base_path, "example1.txt")
    # delimiter = "|"  # 如果文件以 | 分割，替换为 '|'

    # results = analyze_delimited_file(file_path, delimiter=delimiter)
    # results = analyze_json_fields(file_path)
    logs = [
        '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326',
        '10.5.10.6 - - [21/May/2017:21:49:09 +0800] "GET /frame/login.jsp HTTP/1.1" 200 5369',
        '192.168.1.1 - - [22/May/2017:21:49:09 +0800] "POST /api/data HTTP/1.1" 404 1234',
    ]
    # Grok 模式
    pattern = '%{COMMONAPACHELOG}'
    file_path = os.path.join(base_path, "test-nginx-zm.log")
    # 提取并统计字段
    results = analyze_grok_file(file_path)

    # 打印结果
    for column, stats in results.items():
        print(f"字段: {column}")
        for key, value in stats.items():
            if key != "Top 10 及占比":
                print(f"  {key}: {value}")
            else:
                print("  Top 10 及占比:")
                for item in value:
                    print(f"    值: {item[0]}, 次数: {item[1]}, 占比: {item[2]:.2f}%")
        print()

