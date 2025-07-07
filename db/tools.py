import re


def sanitize_search_input(input_str):
    """清理和验证搜索输入"""
    # 移除SQL注入相关的特殊字符
    input_str = re.sub(r'[;\'"\\]', '', input_str)
    # 限制长度
    if len(input_str) > 50:
        input_str = input_str[:50]
    return input_str