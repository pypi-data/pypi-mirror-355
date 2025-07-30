import os
import json
import pandas as pd
from core.pygrok.field_detect import analyze_json_fields

def test_analyze_json_fields(tmp_path):
    # 创建临时 JSON 文件
    test_file = tmp_path / "test.json"
    data = [
        {"field1": 1, "field2": "value1"},
        {"field1": 2, "field2": "value2"},
        {"field1": 3, "field2": "value1"},
    ]
    with open(test_file, "w") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")

    # 调用函数
    results = analyze_json_fields(test_file)

    # 验证结果
    assert "field1" in results
    assert results["field1"]["总数"] == 3
    assert results["field1"]["字段类型"] == "int"
    assert results["field1"]["最小值"] == 1
    assert results["field1"]["最大值"] == 3
    assert results["field1"]["中位数"] == 2

    assert "field2" in results
    assert results["field2"]["总数"] == 3
    assert results["field2"]["字段类型"] == "str"
    assert results["field2"]["不同值数量"] == 2
    assert results["field2"]["Top 10 及占比"][0][0] == "value1"
    assert results["field2"]["Top 10 及占比"][0][1] == 2