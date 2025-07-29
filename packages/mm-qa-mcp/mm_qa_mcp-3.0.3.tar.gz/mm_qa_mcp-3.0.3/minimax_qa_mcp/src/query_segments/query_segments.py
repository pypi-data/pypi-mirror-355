#!/usr/bin/env python3
"""
代码搜索与分析工具

该工具可以根据不同类型的输入提供相应的代码分析功能：
1. --type API：API路径：获取API的入参、出参和接口逻辑
2. --type FUNC 函数名：获取函数的调用链关系图谱
3. --type CODE 代码片段：分析代码影响的函数
4. --type ANY --limit 10 随意输入：模糊搜索相似代码
5. --type FUNC_DETAIL 函数名：查询函数的详细代码实现

使用方法:
$ python query_segments.py <输入内容> [--type API|FUNC|CODE|ANY|FUNC_DETAIL] [--limit 10] [--exact]

参数说明:
--type    : 指定输入类型，可选值：API, FUNC, CODE, ANY, FUNC_DETAIL（默认自动识别）
--limit   : 结果数量限制，默认为10
--exact   : 精确匹配模式
--output  : 输出文件路径，用于保存函数调用图谱
"""

import requests
import json
import sys
import re
import time
from functools import wraps
from tabulate import tabulate
import os
from prettytable import PrettyTable

from minimax_qa_mcp.utils.utils import Utils

# 配置常量
WEAVIATE_URL = Utils.get_conf('weaviate_url', 'url_port') + "/v1"
DEFAULT_LIMIT = 10
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试间隔(秒)
BATCH_SIZE = 50  # 批处理大小
MAX_CONTENT_LENGTH = 250  # 显示的最大内容长度
CLASS_NAME = "GoCodeSegment"  # 数据库中的实际类名

# 调试模式
DEBUG = True

# 输入类型常量
TYPE_API = "API"
TYPE_FUNC = "FUNC"
TYPE_CODE = "CODE"
TYPE_ANY = "ANY"
TYPE_FUNC_DETAIL = "FUNC_DETAIL"


def with_retry(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """
    装饰器: 为函数添加重试逻辑
    
    参数:
        max_retries (int): 最大重试次数
        delay (int): 重试间隔(秒)
        
    返回:
        function: 被装饰的函数
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        print(f"达到最大重试次数({max_retries}), 放弃操作")
                        raise e
                    print(f"操作失败: {str(e)}, 将在 {delay} 秒后重试 ({retries}/{max_retries})")
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


def validate_limit(limit):
    """
    验证并规范化limit参数
    
    参数:
        limit (int): 输入的limit值
        
    返回:
        int: 规范化后的limit值
    """
    try:
        limit = int(limit)
        return max(1, min(limit, 100))  # 确保limit在1-100之间
    except (ValueError, TypeError):
        print(f"警告: 无效的limit值 '{limit}', 使用默认值 {DEFAULT_LIMIT}")
        return DEFAULT_LIMIT


def detect_input_type(input_text):
    """
    自动检测输入的类型
    
    参数:
        input_text (str): 用户输入的文本
        
    返回:
        str: 输入类型 (API, FUNC, CODE, FUNC_DETAIL, ANY)
    """
    if not input_text:
        return TYPE_ANY

    # 如果以斜杠开头，可能是API路径
    if input_text.startswith('/') and '/' in input_text[1:]:
        return TYPE_API

    # 函数命名模式 + "实现" 或 "详情" 或 "代码"，可能需要查询函数详情
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s+(实现|详情|代码|细节|function detail)$', input_text, re.IGNORECASE):
        return TYPE_FUNC_DETAIL

    # 如果是单个词，可能是函数名
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', input_text) and not '\n' in input_text:
        return TYPE_FUNC

    # 如果包含多行或特殊语法，可能是代码片段
    if '\n' in input_text or '{' in input_text or ';' in input_text:
        return TYPE_CODE

    # 包含编程语言的常见关键字，可能是代码
    code_keywords = ['func', 'return', 'if', 'else', 'for', 'while', 'class', 'struct', 'import', 'package']
    for keyword in code_keywords:
        if re.search(r'\b' + keyword + r'\b', input_text):
            return TYPE_CODE

    # 默认为模糊查询
    return TYPE_ANY


def search_api_info(api_path, limit=10, exact=False):
    """
    搜索API信息，包括出入参数和接口逻辑

    参数:
        api_path (str): API路径
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配

    返回:
        dict: API信息，包括路径、入参、出参和实现逻辑
    """
    if not api_path:
        return {"error": "API路径不能为空"}

    limit = validate_limit(limit)

    # 首先从IdlApiMapping中查找API定义
    api_mapping = query_idl_api_mapping(api_path, limit, exact)

    if api_mapping:
        # 找到了API映射，构建结果
        result = {
            "api_path": api_path,
            "definitions": []
        }

        # 如果exact为True且找到了多个结果，再次过滤确保路径完全匹配
        if exact and len(api_mapping) > 1:
            filtered_mapping = []
            for mapping in api_mapping:
                # 规范化路径（去掉开头的斜杠进行比较）
                norm_api_path = api_path.lstrip('/')
                norm_mapping_path = mapping.get("http_path", "").lstrip('/')

                if norm_mapping_path == norm_api_path:
                    filtered_mapping.append(mapping)

            # 如果找到了精确匹配的结果，使用这些结果
            if filtered_mapping:
                api_mapping = filtered_mapping

        for mapping in api_mapping:
            # 查找对应的请求和响应结构体
            req_struct = None
            resp_struct = None

            # 查询请求结构体
            if mapping.get("request_type"):
                req_structs = query_idl_struct(mapping.get("request_type"), 1, True)
                if req_structs:
                    req_struct = req_structs[0]

            # 尝试查询响应结构体，有多种可能的名称格式

            # 1. 从response_type字段获取
            if mapping.get("response_type") and mapping.get("response_type") != mapping.get("request_type"):
                resp_structs = query_idl_struct(mapping.get("response_type"), 1, True)
                if resp_structs:
                    resp_struct = resp_structs[0]

            # 2. 尝试根据方法名推断响应结构体名称
            if not resp_struct and mapping.get("method_name"):
                # 尝试查找"方法名+Resp"或"方法名+Response"格式的结构体
                possible_resp_names = [
                    f"{mapping.get('method_name')}Resp",
                    f"{mapping.get('method_name')}Response",
                    # 将首字母大写
                    f"{mapping.get('method_name')[0].upper()}{mapping.get('method_name')[1:]}Resp",
                    f"{mapping.get('method_name')[0].upper()}{mapping.get('method_name')[1:]}Response"
                ]

                for resp_name in possible_resp_names:
                    resp_structs = query_idl_struct(resp_name, 1, True)
                    if resp_structs:
                        resp_struct = resp_structs[0]
                        break

            # 3. 尝试将请求结构体的"Req"替换为"Resp"
            if not resp_struct and mapping.get("request_type") and "Req" in mapping.get("request_type"):
                resp_name = mapping.get("request_type").replace("Req", "Resp")
                resp_structs = query_idl_struct(resp_name, 1, True)
                if resp_structs:
                    resp_struct = resp_structs[0]

            # 构建API信息
            api_info = {
                "function": mapping.get("method_name", ""),
                "package": mapping.get("service_name", ""),
                "file_path": mapping.get("idl_file", ""),
                "http_method": mapping.get("http_method", ""),
                "request_type": mapping.get("request_type", ""),
                "response_type": resp_struct.get("struct_name") if resp_struct else mapping.get("response_type", ""),
                "input_params": extract_struct_fields(req_struct.get("content", "")) if req_struct else [],
                "output_params": extract_struct_fields(resp_struct.get("content", "")) if resp_struct else [],
                "logic": mapping.get("idl_content", ""),
                "comments": mapping.get("comments", "")
            }

            result["definitions"].append(api_info)

        return result

    # 如果IdlApiMapping中没有找到，尝试在CodeSegment中查找

    # 首先查找API定义（路由定义）
    api_def = query_by_content(f"API route {api_path}", limit)

    # 如果找不到，尝试直接搜索路径
    if not api_def:
        api_def = query_by_field("file_path", api_path, limit, exact)

    # 如果仍找不到，尝试搜索内容
    if not api_def:
        api_def = query_by_content(api_path, limit)

    if not api_def:
        return {"error": f"未找到API: {api_path}"}

    # 提取API相关信息
    result = {
        "api_path": api_path,
        "definitions": [],
    }

    # 遍历找到的定义
    for segment in api_def:
        # 提取代码中的参数信息
        params = extract_api_params(segment.get("code", ""))

        # 构建API信息
        api_info = {
            "function": segment.get("function", ""),
            "package": segment.get("package", ""),
            "file_path": segment.get("file_path", ""),
            "input_params": params.get("input", []),
            "output_params": params.get("output", []),
            "logic": segment.get("code", ""),
            "comments": segment.get("comments", "")
        }
        result["definitions"].append(api_info)

    return result


def query_idl_api_mapping(api_path, limit=10, exact=False):
    """
    查询IdlApiMapping类中的API定义
    
    参数:
        api_path (str): API路径
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配
        
    返回:
        list: API映射列表
    """
    if not api_path:
        return []

    limit = validate_limit(limit)

    operator = "Equal" if exact else "Like"

    # 如果是模糊查询，但API路径是完整的，例如"/v1/music_upload"
    # 尝试直接用Equal查询，因为API路径通常是完整的
    if not exact and api_path.startswith("/") and "/" in api_path[1:]:
        # 先尝试精确匹配
        result = query_idl_api_mapping_with_operator(api_path, limit, "Equal")
        if result:
            return result

    # 按指定的匹配模式查询
    return query_idl_api_mapping_with_operator(api_path, limit, operator)


def query_idl_api_mapping_with_operator(api_path, limit, operator):
    """
    使用特定操作符查询IdlApiMapping

    参数:
        api_path (str): API路径
        limit (int): 结果数量限制
        operator (str): 查询操作符 (Equal, Like)

    返回:
        list: API映射列表
    """
    value_str = api_path

    # 对于Like操作符，如果api_path不包含通配符，添加通配符
    if operator == "Like" and "*" not in api_path:
        value_str = f"*{api_path}*"

    graphql_query = f"""
    {{
      Get {{
        IdlApiMapping(
          where: {{
            path: ["http_path"],
            operator: {operator},
            valueString: "{value_str}"
          }}
          limit: {limit}
        ) {{
          method_name
          http_path
          http_method
          idl_file
          service_name
          idl_content
          request_type
          response_type
          comments
        }}
      }}
    }}
    """

    response = execute_graphql_query(graphql_query)
    if not response or "error" in response:
        error_msg = response.get("error") if response else "未知错误"
        print(f"查询IdlApiMapping失败: {error_msg}")
        return []

    results = response.get("data", {}).get("Get", {}).get("IdlApiMapping", [])

    # 增强精确匹配处理
    if operator == "Equal" and results:
        # 对结果进行后处理，确保http_path完全匹配
        exact_results = []
        for item in results:
            if item.get("http_path") == api_path or item.get("http_path") == value_str:
                exact_results.append(item)
        return exact_results

    return results


def query_idl_struct(struct_name, limit=1, exact=True):
    """
    查询IdlStructDefinition类中的结构体定义
    
    参数:
        struct_name (str): 结构体名称
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配
        
    返回:
        list: 结构体定义列表
    """
    if not struct_name:
        return []

    limit = validate_limit(limit)

    operator = "Equal" if exact else "Like"

    graphql_query = f"""
    {{
      Get {{
        IdlStructDefinition(
          where: {{
            path: ["struct_name"],
            operator: {operator},
            valueString: "{struct_name}"
          }}
          limit: {limit}
        ) {{
          struct_name
          idl_file
          content
        }}
      }}
    }}
    """

    response = execute_graphql_query(graphql_query)
    if not response or "error" in response:
        error_msg = response.get("error") if response else "未知错误"
        print(f"查询IdlStructDefinition失败: {error_msg}")
        return []

    return response.get("data", {}).get("Get", {}).get("IdlStructDefinition", [])


def extract_struct_fields(struct_content):
    """
    从结构体内容中提取字段信息
    
    参数:
        struct_content (str): 结构体内容
        
    返回:
        list: 字段列表
    """
    if not struct_content:
        return []

    # 解析结构体定义中的字段
    fields = []

    # 首先移除struct行和大括号行
    lines = struct_content.split('\n')
    content_lines = []
    for line in lines:
        if not line.strip().startswith('struct') and not line.strip() in ['{', '}']:
            content_lines.append(line)

    # 使用正则表达式匹配每个字段定义行
    # 例如 "1: required string purpose // 用途"
    for line in content_lines:
        line = line.strip()
        if not line or line.startswith('//'):
            continue

        # 尝试匹配字段定义
        field_pattern = r'(\d+):\s*(required|optional)?\s*(\w+)\s+(\w+)(?:\s*//\s*(.*))?'
        match = re.search(field_pattern, line)

        if match:
            field_id, required, field_type, field_name, comment = match.groups()

            fields.append({
                "name": field_name,
                "type": field_type,
                "required": required == "required",
                "comment": comment.strip() if comment else ""
            })

    return fields


def extract_api_params(code):
    """
    从API代码中提取入参和出参
    
    参数:
        code (str): API实现代码
        
    返回:
        dict: 包含input和output的字典
    """
    if not code:
        return {"input": [], "output": []}

    params = {
        "input": [],
        "output": []
    }

    # 查找函数定义行
    func_def_match = re.search(r'func\s+\w+\s*\((.*?)\)(.*?){', code, re.DOTALL)

    if func_def_match:
        # 提取入参
        input_params_str = func_def_match.group(1).strip()
        if input_params_str:
            for param in input_params_str.split(','):
                param = param.strip()
                if param:
                    name_type = param.split()
                    if len(name_type) >= 2:
                        params["input"].append({
                            "name": name_type[0],
                            "type": " ".join(name_type[1:])
                        })

        # 提取出参
        output_params_str = func_def_match.group(2).strip()
        if output_params_str:
            # 去掉前导的返回值括号
            output_params_str = output_params_str.lstrip('(').rstrip(')')

            # 分割多个返回值
            for param in output_params_str.split(','):
                param = param.strip()
                if param:
                    params["output"].append({"type": param})

    return params


def get_function_call_chain(function_name, limit=10, direction="both"):
    """
    获取函数调用链
    
    参数:
        function_name (str): 函数名
        limit (int): 结果数量限制
        direction (str): 调用方向，可选值：caller（调用者）, callee（被调用者）, both（双向）
        
    返回:
        dict: 函数调用链信息
    """
    if not function_name:
        return {"error": "函数名不能为空"}

    limit = validate_limit(limit)

    result = {
        "function": function_name,
        "callers": [],  # 调用此函数的函数
        "callees": [],  # 此函数调用的函数
    }

    # 查找函数定义
    func_defs = query_by_field("function", function_name, limit, True)

    if not func_defs:
        # 如果在CodeSegment中找不到函数定义，检查是否是接口定义的方法
        # 尝试在FunctionCallRelation中查找
        if direction in ["callee", "both"]:
            result["callees"] = query_function_callees(function_name, limit)

        if direction in ["caller", "both"]:
            result["callers"] = query_function_callers(function_name, limit)

        # 如果找到了调用关系但没有函数定义，这可能是一个接口方法
        if result["callers"] or result["callees"]:
            return result
        else:
            return {"error": f"未找到函数: {function_name}"}

    # 获取调用关系
    if direction in ["caller", "both"]:
        # 使用FunctionCallRelation查找调用此函数的代码（谁调用了这个函数）
        result["callers"] = query_function_callers(function_name, limit)

        # 如果没有找到，尝试使用旧方法
        if not result["callers"]:
            # 查找调用此函数的代码（谁调用了这个函数）
            caller_query = f"call {function_name}"
            callers = query_by_content(caller_query, limit)

            for caller in callers:
                if caller.get("function") != function_name:  # 排除自己调用自己
                    result["callers"].append({
                        "function": caller.get("function", ""),
                        "package": caller.get("package", ""),
                        "file_path": caller.get("file_path", ""),
                        "line": f"{caller.get('start_line', 0)}-{caller.get('end_line', 0)}"
                    })

    if direction in ["callee", "both"]:
        # 使用FunctionCallRelation查找此函数调用的代码（这个函数调用了谁）
        result["callees"] = query_function_callees(function_name, limit)

        # 如果没有找到，尝试使用旧方法
        if not result["callees"]:
            # 查找此函数调用的代码（这个函数调用了谁）
            for func_def in func_defs:
                code = func_def.get("code", "")
                # 使用正则表达式查找函数调用
                calls = re.findall(r'(\w+)\s*\(', code)

                # 去重，筛选出真正的函数
                unique_calls = set(calls)
                for call in unique_calls:
                    if call != function_name and not call in ["if", "for", "switch", "select", "defer"]:
                        # 查找被调用函数的定义
                        callee_defs = query_by_field("function", call, 1, True)
                        if callee_defs:
                            callee = callee_defs[0]
                            result["callees"].append({
                                "function": call,
                                "package": callee.get("package", ""),
                                "file_path": callee.get("file_path", ""),
                                "line": f"{callee.get('start_line', 0)}-{callee.get('end_line', 0)}"
                            })

    return result


def query_function_callers(function_name, limit=10):
    """
    查询调用指定函数的函数列表（谁调用了这个函数）
    
    参数:
        function_name (str): 被调用的函数名
        limit (int): 结果数量限制
        
    返回:
        list: 调用者列表
    """
    if not function_name:
        return []

    limit = validate_limit(limit)

    # 使用精确匹配，避免匹配到其他包含该函数名的函数
    graphql_query = f"""
    {{
      Get {{
        FunctionCallRelation(
          where: {{
            operator: Equal,
            path: ["callee_function"],
            valueString: "{function_name}"
          }}
          limit: {limit}
        ) {{
          callee_function
          caller_function
          caller_file
          call_line
        }}
      }}
    }}
    """

    response = execute_graphql_query(graphql_query)
    if not response or "errors" in response:
        error_msg = response.get("errors")[0]["message"] if "errors" in response else "未知错误"
        print(f"查询FunctionCallRelation失败: {error_msg}")
        return []

    calls = response.get("data", {}).get("Get", {}).get("FunctionCallRelation", [])

    # 格式化结果
    callers = []
    for call in calls:
        # 确认callee_function等于查询的函数名
        if call.get("callee_function") != function_name:
            continue

        caller_func = call.get("caller_function", "")
        if not caller_func:
            continue

        # 尝试获取包名
        package_name = ""
        caller_file = call.get("caller_file", "")
        if caller_file:
            # 从文件路径提取包名
            parts = caller_file.split("/")
            if len(parts) >= 2:
                package_name = parts[-2]

        callers.append({
            "function": caller_func,
            "package": package_name,
            "file_path": caller_file,
            "line": str(call.get("call_line", 0))
        })

    # 如果精确匹配没有结果，尝试模糊匹配
    if not callers:
        # 使用模糊匹配
        fuzzy_query = f"""
        {{
          Get {{
            FunctionCallRelation(
              where: {{
                operator: Like,
                path: ["callee_function"],
                valueString: "*{function_name}*"
              }}
              limit: {limit}
            ) {{
              callee_function
              caller_function
              caller_file
              call_line
            }}
          }}
        }}
        """

        fuzzy_response = execute_graphql_query(fuzzy_query)
        if not fuzzy_response or "errors" in fuzzy_response:
            return []

        fuzzy_calls = fuzzy_response.get("data", {}).get("Get", {}).get("FunctionCallRelation", [])

        for call in fuzzy_calls:
            # 检查callee_function是否包含查询的函数名（不区分大小写）
            if function_name.lower() not in call.get("callee_function", "").lower():
                continue

            caller_func = call.get("caller_function", "")
            if not caller_func:
                continue

            # 尝试获取包名
            package_name = ""
            caller_file = call.get("caller_file", "")
            if caller_file:
                # 从文件路径提取包名
                parts = caller_file.split("/")
                if len(parts) >= 2:
                    package_name = parts[-2]

            callers.append({
                "function": caller_func,
                "package": package_name,
                "file_path": caller_file,
                "line": str(call.get("call_line", 0))
            })

    return callers


def query_function_callees(function_name, limit=10):
    """
    查询指定函数调用的函数列表（这个函数调用了谁）
    
    参数:
        function_name (str): 调用者函数名
        limit (int): 结果数量限制
        
    返回:
        list: 被调用者列表
    """
    if not function_name:
        return []

    limit = validate_limit(limit)

    # 使用精确匹配，避免匹配到其他包含该函数名的函数
    graphql_query = f"""
    {{
      Get {{
        FunctionCallRelation(
          where: {{
            operator: Equal,
            path: ["caller_function"],
            valueString: "{function_name}"
          }}
          limit: {limit}
        ) {{
          callee_function
          caller_function
          callee_file
          call_line
        }}
      }}
    }}
    """

    response = execute_graphql_query(graphql_query)
    if not response or "errors" in response:
        error_msg = response.get("errors")[0]["message"] if "errors" in response else "未知错误"
        print(f"查询FunctionCallRelation失败: {error_msg}")
        return []

    calls = response.get("data", {}).get("Get", {}).get("FunctionCallRelation", [])

    # 格式化结果
    callees = []
    for call in calls:
        # 确认caller_function等于查询的函数名
        if call.get("caller_function") != function_name:
            continue

        callee_func = call.get("callee_function", "")
        if not callee_func:
            continue

        # 尝试获取包名
        package_name = ""
        callee_file = call.get("callee_file", "")
        if callee_file:
            # 从文件路径提取包名
            parts = callee_file.split("/")
            if len(parts) >= 2:
                package_name = parts[-2]

        callees.append({
            "function": callee_func,
            "package": package_name,
            "file_path": callee_file,
            "line": str(call.get("call_line", 0))
        })

    # 如果精确匹配没有结果，尝试模糊匹配
    if not callees:
        # 使用模糊匹配
        fuzzy_query = f"""
        {{
          Get {{
            FunctionCallRelation(
              where: {{
                operator: Like,
                path: ["caller_function"],
                valueString: "*{function_name}*"
              }}
              limit: {limit}
            ) {{
              callee_function
              caller_function
              callee_file
              call_line
            }}
          }}
        }}
        """

        fuzzy_response = execute_graphql_query(fuzzy_query)
        if not fuzzy_response or "errors" in fuzzy_response:
            return []

        fuzzy_calls = fuzzy_response.get("data", {}).get("Get", {}).get("FunctionCallRelation", [])

        for call in fuzzy_calls:
            # 检查caller_function是否包含查询的函数名（不区分大小写）
            if function_name.lower() not in call.get("caller_function", "").lower():
                continue

            callee_func = call.get("callee_function", "")
            if not callee_func:
                continue

            # 尝试获取包名
            package_name = ""
            callee_file = call.get("callee_file", "")
            if callee_file:
                # 从文件路径提取包名
                parts = callee_file.split("/")
                if len(parts) >= 2:
                    package_name = parts[-2]

            callees.append({
                "function": callee_func,
                "package": package_name,
                "file_path": callee_file,
                "line": str(call.get("call_line", 0))
            })

    return callees


def analyze_code_impact(code_snippet, limit=10):
    """
    分析代码片段影响的函数
    
    参数:
        code_snippet (str): 代码片段
        limit (int): 结果数量限制
        
    返回:
        dict: 受影响的函数列表
    """
    if not code_snippet:
        return {"error": "代码片段不能为空"}

    limit = validate_limit(limit)

    result = {
        "code_snippet": code_snippet[:MAX_CONTENT_LENGTH] + "..." if len(
            code_snippet) > MAX_CONTENT_LENGTH else code_snippet,
        "affected_functions": []
    }

    # 提取代码中的关键部分
    # 提取代码中可能的函数调用
    calls = re.findall(r'(\w+)\s*\(', code_snippet)

    # 提取代码中可能的变量访问
    vars = re.findall(r'(\w+)\s*=', code_snippet)

    # 提取结构体和接口名称
    structs = re.findall(r'type\s+(\w+)\s+(struct|interface)', code_snippet)
    struct_names = [s[0] for s in structs]

    # 合并关键词
    keywords = set(calls + vars + struct_names)

    # 查找包含这些关键词的函数
    for keyword in keywords:
        if len(keyword) > 3:  # 忽略太短的词
            funcs = query_by_content(keyword, limit // len(keywords) + 1)

            for func in funcs:
                # 检查是否是真正的函数
                if func.get("type") == "function":
                    result["affected_functions"].append({
                        "function": func.get("function", ""),
                        "package": func.get("package", ""),
                        "file_path": func.get("file_path", ""),
                        "line": f"{func.get('start_line', 0)}-{func.get('end_line', 0)}",
                        "relevance": "直接调用" if keyword in calls else "使用变量"
                    })

    # 去重
    unique_functions = []
    seen = set()

    for func in result["affected_functions"]:
        key = f"{func['function']}:{func['package']}"
        if key not in seen:
            seen.add(key)
            unique_functions.append(func)

    result["affected_functions"] = unique_functions[:limit]

    return result


def generate_function_call_graph(call_chain, output_file=None):
    """
    生成函数调用关系图
    
    参数:
        call_chain (dict): 函数调用链信息
        output_file (str): 输出文件路径
        
    返回:
        bool: 是否成功
    """
    if not call_chain:
        print("错误: 函数调用链信息为空")
        return False

    try:
        # 构建简单的文本图
        graph_text = [f"函数 '{call_chain['function']}' 的调用关系图:\n"]

        # 添加调用者
        if call_chain.get("callers"):
            graph_text.append("\n调用此函数的函数:")
            for i, caller in enumerate(call_chain["callers"]):
                graph_text.append(f"{i + 1}. {caller['function']} (包: {caller['package']})")
        else:
            graph_text.append("\n没有找到调用此函数的函数")

        # 添加被调用者
        if call_chain.get("callees"):
            graph_text.append("\n此函数调用的函数:")
            for i, callee in enumerate(call_chain["callees"]):
                graph_text.append(f"{i + 1}. {callee['function']} (包: {callee['package']})")
        else:
            graph_text.append("\n此函数没有调用其他函数")

        # 拼接文本
        graph_text = "\n".join(graph_text)

        # 打印到控制台
        print(graph_text)

        # 如果指定了输出文件，写入文件
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(graph_text)
                print(f"\n调用关系图已保存到: {output_file}")
            except IOError as e:
                print(f"写入文件失败: {e}")
                return False

        return True
    except Exception as e:
        print(f"生成调用关系图时出错: {e}")
        return False


def query_segments(query_value, limit=10, exact=False, query_type=None):
    """
    查询代码片段
    
    参数:
        query_value (str): 查询值
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配
        query_type (str): 查询类型，可选值：function, package, file_path, all
        
    返回:
        list: 查询结果列表
    """
    if not query_value:
        print("错误: 查询内容不能为空")
        return []

    limit = validate_limit(limit)

    # 自动检测查询类型
    if not query_type:
        query_type = detect_query_type(query_value)

    if query_type == "function":
        return query_by_field("function", query_value, limit, exact)
    elif query_type == "function_detail":
        # 提取函数名（去掉后面的"详情"、"实现"等词）
        function_name = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)', query_value).group(1)
        return get_function_detail(function_name, exact)
    elif query_type == "package":
        return query_by_field("package", query_value, limit, exact)
    elif query_type == "file_path":
        return query_by_field("file_path", query_value, limit, exact)
    else:
        return query_all_types(query_value, limit, exact)


def query_all_types(query_value, limit=10, exact=False):
    """
    查询所有类型的代码片段，并按类型分组返回结果
    同时查询四个主要类：GoCodeSegment、IdlApiMapping、IdlStructDefinition、FunctionCallRelation
    
    参数:
        query_value (str): 查询值
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配
        
    返回:
        dict: 按类型分组的查询结果
    """
    if not query_value:
        return {}

    limit = validate_limit(limit)
    all_results = []

    # 调试信息 - 注释掉，实际使用时可以去掉
    # print(f"\n开始搜索 '{query_value}' (精确匹配: {exact})...")

    # 1. 查询 GoCodeSegment 类
    go_code_results = query_code_segments(query_value, limit, exact)
    # print(f"GoCodeSegment 类搜索结果: {len(go_code_results)} 条")
    if go_code_results:
        all_results.extend(go_code_results)

    # 2. 查询 IdlApiMapping 类
    api_results = query_api_mappings(query_value, limit, exact)
    # print(f"IdlApiMapping 类搜索结果: {len(api_results)} 条")
    if api_results:
        all_results.extend(api_results)

    # 3. 查询 IdlStructDefinition 类
    struct_results = query_struct_definitions(query_value, limit, exact)
    # print(f"IdlStructDefinition 类搜索结果: {len(struct_results)} 条")
    if struct_results:
        all_results.extend(struct_results)

    # 4. 查询 FunctionCallRelation 类
    relation_results = query_function_relations(query_value, limit, exact)
    # print(f"FunctionCallRelation 类搜索结果: {len(relation_results)} 条")
    if relation_results:
        all_results.extend(relation_results)

    # print(f"总共找到 {len(all_results)} 条结果")

    # 按类型分组结果
    grouped_results = {}
    for result in all_results[:limit]:
        result_type = result.get("type", "unknown")
        if result_type not in grouped_results:
            grouped_results[result_type] = []
        grouped_results[result_type].append(result)

    return grouped_results


def query_code_segments(query_value, limit=10, exact=False):
    """
    查询 GoCodeSegment 类
    
    参数:
        query_value (str): 查询值
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配
        
    返回:
        list: 查询结果列表
    """
    # 先尝试按字段查询
    fields = ["name", "package", "file_path"]
    results = []

    for field in fields:
        field_results = query_by_field(field, query_value, limit // 3, exact)
        if field_results:
            results.extend(field_results)

    # 再尝试按内容查询
    if len(results) < limit:
        content_results = query_by_content(query_value, limit - len(results))
        if content_results:
            results.extend(content_results)

    return results


def query_api_mappings(query_value, limit=10, exact=False):
    """
    查询 IdlApiMapping 类中的API定义
    
    参数:
        query_value (str): 查询值
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配
        
    返回:
        list: 格式化的API映射结果列表
    """
    limit = validate_limit(limit)
    operator = "Equal" if exact else "Like"
    value_str = query_value

    # 对于Like操作符，添加通配符
    if operator == "Like" and "*" not in query_value:
        value_str = f"*{query_value}*"

    # 尝试多个字段查询
    fields = ["method_name", "http_path", "request_type", "response_type", "idl_content"]
    api_results = []

    for field in fields:
        graphql_query = f"""
        {{
          Get {{
            IdlApiMapping(
              where: {{
                path: ["{field}"],
                operator: {operator},
                valueString: "{value_str}"
              }}
              limit: {limit // len(fields)}
            ) {{
              method_name
              http_path
              http_method
              idl_file
              service_name
              idl_content
              request_type
              response_type
              comments
              _additional {{
                id
              }}
            }}
          }}
        }}
        """

        response = execute_graphql_query(graphql_query)
        if response and "error" not in response:
            results = response.get("data", {}).get("Get", {}).get("IdlApiMapping", [])

            for result in results:
                api_result = {
                    "id": result.get("_additional", {}).get("id", ""),
                    "function": result.get("method_name", ""),
                    "package": result.get("service_name", ""),
                    "file_path": result.get("idl_file", ""),
                    "type": "api",
                    "code": result.get("idl_content", ""),
                    "http_path": result.get("http_path", ""),
                    "http_method": result.get("http_method", ""),
                    "request_type": result.get("request_type", ""),
                    "response_type": result.get("response_type", ""),
                    "comments": result.get("comments", "")
                }
                api_results.append(api_result)

    return api_results


def query_struct_definitions(query_value, limit=10, exact=False):
    """
    查询 IdlStructDefinition 类中的结构体定义
    
    参数:
        query_value (str): 查询值
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配
        
    返回:
        list: 格式化的结构体定义结果列表
    """
    limit = validate_limit(limit)
    operator = "Equal" if exact else "Like"
    value_str = query_value

    # 对于Like操作符，添加通配符
    if operator == "Like" and "*" not in query_value:
        value_str = f"*{query_value}*"

    # 尝试多个字段查询
    fields = ["struct_name", "content", "fields"]
    struct_results = []

    for field in fields:
        graphql_query = f"""
        {{
          Get {{
            IdlStructDefinition(
              where: {{
                path: ["{field}"],
                operator: {operator},
                valueString: "{value_str}"
              }}
              limit: {limit // len(fields)}
            ) {{
              struct_name
              idl_file
              content
              fields
              line_start
              line_end
              comments
              _additional {{
                id
              }}
            }}
          }}
        }}
        """

        response = execute_graphql_query(graphql_query)
        if response and "error" not in response:
            results = response.get("data", {}).get("Get", {}).get("IdlStructDefinition", [])

            for result in results:
                struct_result = {
                    "id": result.get("_additional", {}).get("id", ""),
                    "function": result.get("struct_name", ""),
                    "package": os.path.dirname(result.get("idl_file", "")),
                    "file_path": result.get("idl_file", ""),
                    "type": "struct",
                    "code": result.get("content", ""),
                    "fields": result.get("fields", ""),
                    "comments": result.get("comments", ""),
                    "start_line": result.get("line_start", 0),
                    "end_line": result.get("line_end", 0)
                }
                struct_results.append(struct_result)

    return struct_results


def query_function_relations(query_value, limit=10, exact=False):
    """
    查询 FunctionCallRelation 类中的函数调用关系
    
    参数:
        query_value (str): 查询值
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配
        
    返回:
        list: 格式化的函数调用关系结果列表
    """
    limit = validate_limit(limit)
    operator = "Equal" if exact else "Like"
    value_str = query_value

    # 对于Like操作符，添加通配符
    if operator == "Like" and "*" not in query_value:
        value_str = f"*{query_value}*"

    # 尝试多个字段查询
    fields = ["caller_function", "callee_function", "caller_package", "callee_package", "call_context"]
    relation_results = []

    for field in fields:
        graphql_query = f"""
        {{
          Get {{
            FunctionCallRelation(
              where: {{
                path: ["{field}"],
                operator: {operator},
                valueString: "{value_str}"
              }}
              limit: {limit // len(fields)}
            ) {{
              caller_function
              caller_file
              caller_package
              callee_function
              callee_file
              callee_package
              call_line
              call_context
              call_type
              _additional {{
                id
              }}
            }}
          }}
        }}
        """

        response = execute_graphql_query(graphql_query)
        if response and "error" not in response:
            results = response.get("data", {}).get("Get", {}).get("FunctionCallRelation", [])

            for result in results:
                relation_result = {
                    "id": result.get("_additional", {}).get("id", ""),
                    "function": result.get("caller_function", ""),
                    "package": result.get("caller_package", ""),
                    "file_path": result.get("caller_file", ""),
                    "type": "function_call",
                    "code": result.get("call_context", ""),
                    "called_function": result.get("callee_function", ""),
                    "called_package": result.get("callee_package", ""),
                    "called_file": result.get("callee_file", ""),
                    "line": result.get("call_line", 0),
                    "call_type": result.get("call_type", "")
                }
                relation_results.append(relation_result)

    return relation_results


def detect_query_type(query_value):
    """
    自动检测查询类型
    
    参数:
        query_value (str): 查询值
        
    返回:
        str: 查询类型 (function, function_detail, package, file_path, all)
    """
    if not query_value:
        return "all"

    # 查询值为路径格式，例如 "path/to/file.go"
    if "/" in query_value and not query_value.startswith("/"):
        return "file_path"

    # 查询值为完整路径格式，例如 "/abs/path/to/file.go"
    if query_value.startswith("/"):
        return "file_path"

    # 函数详情查询模式：函数名+特定关键词
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s+(实现|详情|代码|细节|function detail)$', query_value, re.IGNORECASE):
        return "function_detail"

    # 查询值包含点号，可能是包名，例如 "github.com/user/repo"
    if "." in query_value and "/" in query_value:
        return "package"

    # 查询值是有效的标识符，可能是函数名
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', query_value):
        return "function"

    # 默认为全部类型查询
    return "all"


def query_by_field(field_name, field_value, limit=10, exact=False):
    """
    按字段查询代码片段
    
    参数:
        field_name (str): 字段名称 (name, package, file_path)
        field_value (str): 字段值
        limit (int): 结果数量限制
        exact (bool): 是否精确匹配
        
    返回:
        list: 查询结果列表
    """
    if not field_name or not field_value:
        return []

    # 字段名映射，兼容旧代码
    field_mapping = {
        "function": "name",
        "type": "segment_type"
    }

    # 如果使用了旧字段名，转换为新字段名
    if field_name in field_mapping:
        field_name = field_mapping[field_name]

    limit = validate_limit(limit)

    operator = "" if exact else "Like"

    graphql_query = f"""
    {{
      Get {{
        {CLASS_NAME}(
          where: {{
            path: ["{field_name}"],
            operator: {operator},
            valueString: "{field_value}"
          }}
          limit: {limit}
        ) {{
          _additional {{
            id
          }}
          name
          package
          file_path
          segment_type
          content
          imports
          line_start
          line_end
        }}
      }}
    }}
    """

    response = execute_graphql_query(graphql_query)
    if not response or "error" in response:
        error_msg = response.get("error") if response else "未知错误"
        print(f"查询失败: {error_msg}")
        return []

    segments = response.get("data", {}).get("Get", {}).get(CLASS_NAME, [])
    return [format_graphql_result(segment) for segment in segments]


def query_by_content(query_text, limit=10):
    """
    按内容查询代码片段
    
    参数:
        query_text (str): 查询文本
        limit (int): 结果数量限制
        
    返回:
        list: 查询结果列表
    """
    if not query_text:
        return []

    limit = validate_limit(limit)

    # 清理查询文本，避免特殊字符导致查询失败
    cleaned_query = query_text.replace('"', '\\"').replace('\n', ' ')

    graphql_query = f"""
    {{
      Get {{
        {CLASS_NAME}(
          nearText: {{
            concepts: ["{cleaned_query}"]
          }}
          limit: {limit}
        ) {{
          _additional {{
            id
            certainty
          }}
          name
          package
          file_path
          segment_type
          content
          imports
          line_start
          line_end
        }}
      }}
    }}
    """

    response = execute_graphql_query(graphql_query)
    if not response or "error" in response:
        error_msg = response.get("error") if response else "未知错误"
        print(f"查询失败: {error_msg}")
        return []

    segments = response.get("data", {}).get("Get", {}).get(CLASS_NAME, [])

    # 处理结果并按相关性（certainty）排序
    results = []
    for segment in segments:
        result = format_graphql_result(segment)
        certainty = segment.get("_additional", {}).get("certainty", 0)
        result["relevance"] = certainty
        results.append(result)

    # 按相关性排序
    results.sort(key=lambda x: x.get("relevance", 0), reverse=True)

    return results


def format_graphql_result(graphql_segment):
    """
    格式化GraphQL查询结果
    
    参数:
        graphql_segment (dict): GraphQL查询结果
        
    返回:
        dict: 格式化后的结果
    """
    if not graphql_segment:
        return {}

    segment = {
        "id": graphql_segment.get("_additional", {}).get("id", ""),
        "function": graphql_segment.get("name", ""),  # 映射name到function
        "package": graphql_segment.get("package", ""),
        "file_path": graphql_segment.get("file_path", ""),
        "type": graphql_segment.get("segment_type", ""),  # 映射segment_type到type
        "code": graphql_segment.get("content", ""),
        "imports": graphql_segment.get("imports", []),
        "comments": graphql_segment.get("comments", ""),
        "start_line": graphql_segment.get("line_start", 0),
        "end_line": graphql_segment.get("line_end", 0)
    }
    return segment


@with_retry()
def execute_graphql_query(query):
    """
    执行GraphQL查询
    
    参数:
        query (str): GraphQL查询语句
        
    返回:
        dict: 查询结果
    """
    if not query:
        return {"error": "查询语句不能为空"}

    url = f"{WEAVIATE_URL}/graphql"
    headers = {
        "Content-Type": "application/json"
    }

    payload = {"query": query}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"GraphQL查询错误: {response.status_code} - {response.text}"
            if DEBUG:
                print(error_msg)
            return {"error": error_msg}
    except requests.RequestException as e:
        error_msg = f"请求异常: {e}"
        if DEBUG:
            print(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"未知异常: {e}"
        if DEBUG:
            print(error_msg)
        return {"error": error_msg}


def print_summary_table(segments):
    """
    将查询结果格式化输出为表格
    
    参数:
        segments (dict|list): 查询结果，可以是列表或按类型分组的字典
    """
    if not segments:
        print("未找到匹配的结果")
        return

    # 如果是按类型分组的字典
    if isinstance(segments, dict):
        # 检查是否有结果
        if sum(len(group) for group in segments.values()) == 0:
            print("未找到匹配的结果")
            return

        # 分别显示每种类型的结果
        for segment_type, segment_list in segments.items():
            if not segment_list:
                continue

            print(f"\n{'-' * 60}")
            print(f"类型: {segment_type.upper()} ({len(segment_list)} 个结果)")
            print(f"{'-' * 60}")

            # 根据类型显示不同的表格
            if segment_type == "function":
                print("【函数定义】")
                _print_function_table(segment_list)
            elif segment_type == "file":
                print("【文件】")
                _print_file_table(segment_list)
            elif segment_type == "struct" or segment_type == "interface":
                print("【数据结构】")
                _print_struct_table(segment_list)
            elif segment_type == "api":
                print("【API接口】")
                _print_api_table(segment_list)
            elif segment_type == "function_call":
                print("【函数调用关系】")
                _print_function_call_table(segment_list)
            else:
                print(f"【{segment_type}】")
                _print_general_table(segment_list)

        return

    # 如果是列表但为空
    if len(segments) == 0:
        print("未找到匹配的结果")
        return

    # 如果是列表，则不按类型分组显示
    print("【查询结果】")
    _print_general_table(segments)


def _print_function_table(segments):
    """打印函数类型的表格"""
    table = PrettyTable()
    table.field_names = ["函数名", "包名", "文件路径", "行范围"]
    table.align = "l"
    table.max_width = 30  # 减小列宽以适应终端宽度

    for segment in segments:
        # 获取行范围
        start_line = segment.get("start_line", 0)
        end_line = segment.get("end_line", 0)
        line_range = f"{start_line}-{end_line}" if start_line and end_line else "N/A"

        # 处理长文件路径
        file_path = segment.get("file_path", "N/A")
        if len(file_path) > 30:
            file_path = "..." + file_path[-27:]

        table.add_row([
            segment.get("function", "N/A")[:25],  # 限制长度
            segment.get("package", "N/A")[:15],  # 限制长度
            file_path,
            line_range
        ])

    print(table)


def _print_file_table(segments):
    """打印文件类型的表格"""
    table = PrettyTable()
    table.field_names = ["文件名", "包名", "文件路径", "行数"]
    table.align = "l"
    table.max_width = 30  # 减小列宽以适应终端宽度

    for segment in segments:
        # 获取行数
        start_line = segment.get("start_line", 0)
        end_line = segment.get("end_line", 0)
        line_count = end_line - start_line + 1 if start_line and end_line else "N/A"

        # 处理长文件路径
        file_path = segment.get("file_path", "N/A")
        if len(file_path) > 30:
            file_path = "..." + file_path[-27:]

        # 处理长文件名
        file_name = segment.get("function", "N/A")  # 对于文件类型，function字段存储文件名
        if len(file_name) > 25:
            file_name = file_name[:22] + "..."

        table.add_row([
            file_name,
            segment.get("package", "N/A")[:15],  # 限制长度
            file_path,
            line_count
        ])

    print(table)


def _print_struct_table(segments):
    """打印结构体或接口类型的表格"""
    table = PrettyTable()
    table.field_names = ["结构名", "包名", "文件路径", "行范围"]
    table.align = "l"
    table.max_width = 30  # 减小列宽以适应终端宽度

    for segment in segments:
        # 获取行范围
        start_line = segment.get("start_line", 0)
        end_line = segment.get("end_line", 0)
        line_range = f"{start_line}-{end_line}" if start_line and end_line else "N/A"

        # 处理长文件路径
        file_path = segment.get("file_path", "N/A")
        if len(file_path) > 30:
            file_path = "..." + file_path[-27:]

        table.add_row([
            segment.get("function", "N/A")[:25],  # 对于结构体类型，function字段存储结构体名
            segment.get("package", "N/A")[:15],  # 限制长度
            file_path,
            line_range
        ])

    print(table)


def _print_api_table(segments):
    """打印API接口类型的表格"""
    table = PrettyTable()
    table.field_names = ["方法名", "服务名", "HTTP路径", "请求类型", "响应类型"]
    table.align = "l"
    table.max_width = 20  # 减小列宽以适应终端宽度

    for segment in segments:
        # 截断长字符串
        method_name = segment.get("function", "N/A")
        service_name = segment.get("package", "N/A")
        http_path = segment.get("http_path", "N/A")
        request_type = segment.get("request_type", "N/A")
        response_type = segment.get("response_type", "N/A")

        # 截断超长字符串
        if len(method_name) > 15:
            method_name = method_name[:12] + "..."
        if len(service_name) > 12:
            service_name = service_name[:9] + "..."
        if len(http_path) > 15:
            http_path = http_path[:12] + "..."
        if len(request_type) > 15:
            request_type = request_type[:12] + "..."
        if len(response_type) > 15:
            response_type = response_type[:12] + "..."

        table.add_row([
            method_name,  # 方法名
            service_name,  # 服务名
            http_path,  # HTTP路径
            request_type,  # 请求类型
            response_type  # 响应类型
        ])

    print(table)


def _print_function_call_table(segments):
    """打印函数调用关系类型的表格"""
    table = PrettyTable()
    table.field_names = ["调用者函数", "调用者包", "被调函数", "被调包", "文件路径", "行号"]
    table.align = "l"
    table.max_width = 30  # 减小列宽以适应终端宽度

    for segment in segments:
        # 只截取文件路径的最后部分，以减少显示宽度
        file_path = segment.get("file_path", "N/A")
        if len(file_path) > 30:
            file_path = "..." + file_path[-27:]

        table.add_row([
            segment.get("function", "N/A")[:25],  # 调用者函数
            segment.get("package", "N/A")[:15],  # 调用者包
            segment.get("called_function", "N/A")[:25],  # 被调函数
            segment.get("called_package", "N/A")[:15],  # 被调包
            file_path,  # 文件路径
            segment.get("line", "N/A")  # 行号
        ])

    print(table)


def _print_general_table(segments):
    """打印通用类型的表格"""
    table = PrettyTable()
    table.field_names = ["类型", "名称", "包名", "文件路径"]
    table.align = "l"
    table.max_width = 30  # 减小列宽以适应终端宽度

    for segment in segments:
        # 处理长文件路径
        file_path = segment.get("file_path", "N/A")
        if len(file_path) > 30:
            file_path = "..." + file_path[-27:]

        table.add_row([
            segment.get("type", "unknown")[:15],
            segment.get("function", "N/A")[:25],
            segment.get("package", "N/A")[:15],
            file_path
        ])

    print(table)


def print_api_info(api_info):
    """
    打印API信息
    
    参数:
        api_info (dict): API信息
    """
    if api_info.get("error"):
        print(f"错误: {api_info['error']}")
        return

    print(f"\nAPI路径: {api_info['api_path']}")
    print(f"找到 {len(api_info['definitions'])} 个相关定义")

    for i, definition in enumerate(api_info['definitions']):
        print(f"\n定义 {i + 1}:")
        print(f"  函数: {definition['function']}")
        print(f"  包名: {definition['package']}")
        print(f"  文件: {definition['file_path']}")
        if definition.get('http_method'):
            print(f"  HTTP方法: {definition['http_method']}")

        print("\n  入参:")
        if definition.get('request_type'):
            print(f"  [请求类型: {definition['request_type']}]")

        if definition['input_params']:
            for param in definition['input_params']:
                req_str = "(必填)" if param.get("required") else "(可选)"
                comment = f" // {param.get('comment')}" if param.get('comment') else ""
                print(f"    - {param.get('name', '')}: {param.get('type', '')} {req_str}{comment}")
        else:
            print("    无")

        print("\n  出参:")
        if definition.get('response_type'):
            print(f"  [响应类型: {definition['response_type']}]")

        if definition['output_params']:
            for param in definition['output_params']:
                if 'name' in param and 'type' in param:
                    comment = f" // {param.get('comment')}" if param.get('comment') else ""
                    print(f"    - {param.get('name', '')}: {param.get('type', '')}{comment}")
                else:
                    print(f"    - {param.get('type', '')}")
        else:
            print("    无")

        print("\n  逻辑代码片段:")
        code_lines = definition['logic'].split('\n')
        for line in code_lines[:10]:  # 只显示前10行
            print(f"    {line}")

        if len(code_lines) > 10:
            print(f"    ... (共 {len(code_lines)} 行)")


def print_function_call_chain(call_chain):
    """
    打印函数调用链
    
    参数:
        call_chain (dict): 函数调用链信息
    """
    if call_chain.get("error"):
        print(f"错误: {call_chain['error']}")
        return

    print(f"\n函数: {call_chain['function']}")

    print("\n调用此函数的函数 (callers):")
    if call_chain.get("callers"):
        caller_data = []
        for i, caller in enumerate(call_chain["callers"]):
            caller_data.append([
                i + 1,
                caller.get("function", ""),
                caller.get("package", ""),
                caller.get("file_path", ""),
                caller.get("line", "")
            ])
        print(tabulate(caller_data, headers=["序号", "函数名", "包名", "文件路径", "行号"], tablefmt="grid"))
    else:
        print("  无")

    print("\n此函数调用的函数 (callees):")
    if call_chain.get("callees"):
        callee_data = []
        for i, callee in enumerate(call_chain["callees"]):
            callee_data.append([
                i + 1,
                callee.get("function", ""),
                callee.get("package", ""),
                callee.get("file_path", ""),
                callee.get("line", "")
            ])
        print(tabulate(callee_data, headers=["序号", "函数名", "包名", "文件路径", "行号"], tablefmt="grid"))
    else:
        print("  无")


def print_code_impact(code_impact):
    """
    打印代码影响分析结果
    
    参数:
        code_impact (dict): 代码影响分析结果
    """
    if code_impact.get("error"):
        print(f"错误: {code_impact['error']}")
        return

    print("\n代码片段影响分析:")
    print(f"代码片段: {code_impact['code_snippet']}")

    print("\n受影响的函数:")
    if code_impact.get("affected_functions"):
        affected_data = []
        for i, func in enumerate(code_impact["affected_functions"]):
            affected_data.append([
                i + 1,
                func.get("function", ""),
                func.get("package", ""),
                func.get("file_path", ""),
                func.get("line", ""),
                func.get("relevance", "")
            ])
        print(
            tabulate(affected_data, headers=["序号", "函数名", "包名", "文件路径", "行号", "相关性"], tablefmt="grid"))
    else:
        print("  无")


def safe_read_file(file_path):
    """
    安全地读取文件内容
    
    参数:
        file_path (str): 文件路径
        
    返回:
        str: 文件内容，失败则返回空字符串
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        return ""


def generate_call_chain_topology(function_name, max_depth=5, direction="both", output_file=None):
    """
    生成函数调用链拓扑图，按包名分组，最大深度5层
    
    参数:
        function_name (str): 函数名
        max_depth (int): 最大深度，默认为5
        direction (str): 调用方向，可选值：caller（调用者）, callee（被调用者）, both（双向）
        output_file (str): 输出文件路径
        
    返回:
        dict: 调用链拓扑图数据
    """
    if not function_name:
        return {"error": "函数名不能为空"}

    # 限制最大深度，防止无限递归
    max_depth = min(max(1, max_depth), 5)

    # 初始化拓扑图数据
    topology = {
        "root": function_name,
        "nodes": {},  # 节点信息：{function_name: {package, file_path, ...}}
        "edges": [],  # 边信息：[{source, target, type}, ...]
        "packages": {}  # 按包分组：{package_name: [function_names]}
    }

    # 已访问的函数，避免循环引用
    visited = set()

    # 递归获取调用链
    def build_topology(func, depth, dir):
        if depth > max_depth or func in visited:
            return

        visited.add(func)

        # 获取当前函数的调用关系
        call_chain = get_function_call_chain(func, 100, dir)

        if "error" in call_chain:
            # 如果没有找到函数定义，仍将其添加为节点
            topology["nodes"][func] = {
                "function": func,
                "package": "unknown",
                "file_path": "",
                "is_found": False
            }
            return

        # 添加当前函数节点
        if func not in topology["nodes"]:
            # 尝试获取函数定义信息
            func_defs = query_by_field("function", func, 1, True)

            node_info = {
                "function": func,
                "package": "unknown",
                "file_path": "",
                "is_found": True
            }

            # 首先尝试从函数定义中获取包名
            if func_defs:
                func_def = func_defs[0]
                package = func_def.get("package", "unknown")

                node_info.update({
                    "package": package,
                    "file_path": func_def.get("file_path", ""),
                    "start_line": func_def.get("start_line", 0),
                    "end_line": func_def.get("end_line", 0)
                })
            else:
                # 如果没有找到函数定义，尝试从调用关系中获取包名

                # 检查是否为当前调用链的根函数，如果是则优先从callers中获取
                if func == function_name:
                    # 从调用者中寻找包信息
                    for caller in call_chain.get("callers", []):
                        if caller.get("package") and caller.get("package") != "unknown":
                            node_info["package"] = caller.get("package")
                            break

                # 如果仍是unknown，尝试从callees中获取
                if node_info["package"] == "unknown":
                    for callee in call_chain.get("callees", []):
                        if callee.get("package") and callee.get("package") != "unknown":
                            node_info["package"] = callee.get("package")
                            break

            # 更新包名分组
            package = node_info["package"]
            if package not in topology["packages"]:
                topology["packages"][package] = []

            if func not in topology["packages"][package]:
                topology["packages"][package].append(func)

            topology["nodes"][func] = node_info

        # 处理调用者（谁调用了此函数）
        if dir in ["caller", "both"] and depth < max_depth:
            for caller in call_chain.get("callers", []):
                caller_func = caller.get("function")
                if not caller_func:
                    continue

                # 添加边
                edge = {
                    "source": caller_func,
                    "target": func,
                    "type": "caller"
                }

                if edge not in topology["edges"]:
                    topology["edges"].append(edge)

                # 递归处理调用者
                build_topology(caller_func, depth + 1, "caller")

                # 同时更新节点的包信息
                if caller_func in topology["nodes"] and caller.get("package"):
                    # 如果已有的包名是unknown，则更新
                    if topology["nodes"][caller_func].get("package") == "unknown":
                        package = caller.get("package", "unknown")
                        topology["nodes"][caller_func]["package"] = package

                        # 更新包名分组
                        if package not in topology["packages"]:
                            topology["packages"][package] = []

                        # 从unknown包移除
                        if "unknown" in topology["packages"] and caller_func in topology["packages"]["unknown"]:
                            topology["packages"]["unknown"].remove(caller_func)

                        # 添加到正确的包
                        if caller_func not in topology["packages"][package]:
                            topology["packages"][package].append(caller_func)

        # 处理被调用者（此函数调用了谁）
        if dir in ["callee", "both"] and depth < max_depth:
            for callee in call_chain.get("callees", []):
                callee_func = callee.get("function")
                if not callee_func:
                    continue

                # 添加边
                edge = {
                    "source": func,
                    "target": callee_func,
                    "type": "callee"
                }

                if edge not in topology["edges"]:
                    topology["edges"].append(edge)

                # 递归处理被调用者
                build_topology(callee_func, depth + 1, "callee")

                # 同时更新节点的包信息
                if callee_func in topology["nodes"] and callee.get("package"):
                    # 如果已有的包名是unknown，则更新
                    if topology["nodes"][callee_func].get("package") == "unknown":
                        package = callee.get("package", "unknown")
                        topology["nodes"][callee_func]["package"] = package

                        # 更新包名分组
                        if package not in topology["packages"]:
                            topology["packages"][package] = []

                        # 从unknown包移除
                        if "unknown" in topology["packages"] and callee_func in topology["packages"]["unknown"]:
                            topology["packages"]["unknown"].remove(callee_func)

                        # 添加到正确的包
                        if callee_func not in topology["packages"][package]:
                            topology["packages"][package].append(callee_func)

    # 从根函数开始构建拓扑图
    build_topology(function_name, 1, direction)

    # 如果指定了输出文件，保存为JSON和DOT格式
    if output_file:
        # 保存为JSON格式
        json_file = f"{output_file}.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(topology, f, indent=2, ensure_ascii=False)
            print(f"拓扑图数据已保存为JSON: {json_file}")
        except Exception as e:
            print(f"保存JSON失败: {e}")

        # 生成DOT文件（用于Graphviz可视化）
        dot_file = f"{output_file}.dot"
        try:
            with open(dot_file, 'w', encoding='utf-8') as f:
                f.write('digraph call_chain {\n')
                f.write('  rankdir=LR;\n')  # 从左到右布局
                f.write('  node [shape=box, style=filled, fontname="Arial"];\n')

                # 按包分组
                for package, funcs in topology["packages"].items():
                    if package == "unknown":
                        continue

                    f.write(f'  subgraph cluster_{package.replace(".", "_")} {{\n')
                    f.write(f'    label="{package}";\n')
                    f.write('    style=filled;\n')
                    f.write('    color=lightgrey;\n')

                    for func in funcs:
                        node_color = "lightblue" if func == function_name else "white"
                        f.write(f'    "{func}" [fillcolor="{node_color}"];\n')

                    f.write('  }\n')

                # 未知包的节点
                if "unknown" in topology["packages"]:
                    for func in topology["packages"]["unknown"]:
                        node_color = "lightblue" if func == function_name else "white"
                        f.write(f'  "{func}" [fillcolor="{node_color}"];\n')

                # 添加边
                for edge in topology["edges"]:
                    source = edge["source"]
                    target = edge["target"]
                    edge_type = "solid" if edge["type"] == "callee" else "dashed"
                    f.write(f'  "{source}" -> "{target}" [style={edge_type}];\n')

                f.write('}\n')

            print(f"拓扑图已保存为DOT格式: {dot_file}")
            print(f"提示: 可使用Graphviz渲染DOT文件: dot -Tpng {dot_file} -o {output_file}.png")
        except Exception as e:
            print(f"保存DOT文件失败: {e}")

    return topology


def print_call_chain_topology(topology):
    """
    打印调用链拓扑图
    
    参数:
        topology (dict): 调用链拓扑图数据
    """
    if "error" in topology:
        print(f"错误: {topology['error']}")
        return

    root = topology.get("root", "")
    print(f"\n函数 '{root}' 的调用链拓扑图:")

    # 打印按包分组的函数
    print("\n按包名分组的函数:")
    for package, funcs in topology.get("packages", {}).items():
        print(f"- 包: {package}")
        for func in funcs:
            is_root = "√" if func == root else ""
            print(f"  - {func} {is_root}")

    # 打印调用关系
    print("\n调用关系:")
    for edge in topology.get("edges", []):
        edge_type = "→" if edge["type"] == "callee" else "←"
        print(f"  {edge['source']} {edge_type} {edge['target']}")

    print(f"\n共有 {len(topology.get('nodes', {}))} 个函数节点, {len(topology.get('edges', []))} 条调用关系")


def analyze_code_impact_advanced(code_snippet, limit=10):
    """
    高级代码影响分析 - 分析代码片段影响的函数、API和业务逻辑
    
    参数:
        code_snippet (str): 代码片段
        limit (int): 结果数量限制
        
    返回:
        dict: 包含详细影响分析的结果
    """
    if not code_snippet:
        return {"error": "代码片段不能为空"}

    result = {
        "code_snippet": code_snippet[:MAX_CONTENT_LENGTH] + "..." if len(
            code_snippet) > MAX_CONTENT_LENGTH else code_snippet,
        "affected_functions": [],
        "affected_apis": [],
        "business_logic_impact": [],
        "related_structs": []
    }

    # 1. 提取关键元素
    # 提取函数名
    function_pattern = r'func\s+(\w+)\s*\('
    function_matches = re.findall(function_pattern, code_snippet)

    # 提取API路径
    api_pattern = r'(\/v\d+\/[a-zA-Z0-9\/\-_]+)'
    api_matches = re.findall(api_pattern, code_snippet)

    # 提取结构体名
    struct_pattern = r'([A-Z][a-zA-Z0-9]+(?:Req|Resp|Request|Response))'
    struct_matches = re.findall(struct_pattern, code_snippet)

    # 提取模型名称和特殊条件
    model_pattern = r'([A-Z][a-zA-Z0-9]+(?:Chat|Model|GPT))'
    model_matches = re.findall(model_pattern, code_snippet)

    # 提取错误处理
    error_pattern = r'(Err[a-zA-Z0-9]+)'
    error_matches = re.findall(error_pattern, code_snippet)

    # 提取所有其他函数调用
    calls_pattern = r'(\w+)\s*\('
    calls_matches = re.findall(calls_pattern, code_snippet)

    # 2. 查询相关元素
    # 查询API定义
    for api in api_matches:
        api_info = search_api_info(api, 1, False)
        if "error" not in api_info:
            result["affected_apis"].append(api_info)

    # 如果没找到API，尝试从结构体名推断
    if not result["affected_apis"]:
        for struct in struct_matches:
            # 检查是否是请求或响应结构体
            if struct.endswith(("Req", "Request")):
                # 查找使用此请求结构体的API
                api_mappings = query_idl_api_mapping_by_request(struct, limit)
                for mapping in api_mappings:
                    api_info = search_api_info(mapping.get("http_path", ""), 1, True)
                    if "error" not in api_info:
                        result["affected_apis"].append(api_info)
            elif struct.endswith(("Resp", "Response")):
                # 查找返回此响应结构体的API
                api_mappings = query_idl_api_mapping_by_response(struct, limit)
                for mapping in api_mappings:
                    api_info = search_api_info(mapping.get("http_path", ""), 1, True)
                    if "error" not in api_info:
                        result["affected_apis"].append(api_info)

    # 查询函数定义
    for func in function_matches + calls_matches:
        if len(func) > 3 and func not in ['if', 'len', 'for', 'range', 'switch', 'case', 'func']:  # 忽略关键字和太短的函数名
            func_info = get_function_call_chain(func, 1, "both")
            if "error" not in func_info:
                result["affected_functions"].append(func_info)

    # 查询结构体定义
    for struct in struct_matches:
        struct_info = query_idl_struct(struct, 1, True)
        if struct_info:
            result["related_structs"].append(struct_info[0])

    # 3. 分析业务逻辑影响
    # 分析条件分支的影响
    if "if " in code_snippet:
        condition_parts = code_snippet.split("if ")[1].split("{")[0].strip()
        result["business_logic_impact"].append({
            "condition": condition_parts,
            "impact_type": "conditional_check",
            "description": f"业务逻辑在满足条件 '{condition_parts}' 时执行特定操作"
        })

    # 分析错误返回的影响
    if "return " in code_snippet and "err" in code_snippet:
        for error in error_matches:
            result["business_logic_impact"].append({
                "error_type": error,
                "impact_type": "error_handling",
                "description": f"当条件满足时返回错误 '{error}', 影响API调用结果"
            })

    # 分析模型限制的影响
    for model in model_matches:
        result["business_logic_impact"].append({
            "model": model,
            "impact_type": "model_limitation",
            "description": f"代码对模型 '{model}' 施加了特定限制或行为"
        })

    return result


# 辅助函数：根据请求结构体查询API
def query_idl_api_mapping_by_request(request_type, limit=5):
    """
    根据请求结构体名称查询API映射
    
    参数:
        request_type (str): 请求结构体名称
        limit (int): 结果数量限制
        
    返回:
        list: API映射列表
    """
    if not request_type:
        return []

    limit = validate_limit(limit)

    graphql_query = f"""
    {{
      Get {{
        IdlApiMapping(
          where: {{
            path: ["request_type"],
            operator: Equal,
            valueString: "{request_type}"
          }}
          limit: {limit}
        ) {{
          method_name
          http_path
          http_method
          idl_file
          service_name
          request_type
          response_type
        }}
      }}
    }}
    """

    response = execute_graphql_query(graphql_query)
    if not response or "errors" in response:
        return []

    return response.get("data", {}).get("Get", {}).get("IdlApiMapping", [])


# 辅助函数：根据响应结构体查询API
def query_idl_api_mapping_by_response(response_type, limit=5):
    """
    根据响应结构体名称查询API映射
    
    参数:
        response_type (str): 响应结构体名称
        limit (int): 结果数量限制
        
    返回:
        list: API映射列表
    """
    if not response_type:
        return []

    limit = validate_limit(limit)

    graphql_query = f"""
    {{
      Get {{
        IdlApiMapping(
          where: {{
            path: ["response_type"],
            operator: Equal,
            valueString: "{response_type}"
          }}
          limit: {limit}
        ) {{
          method_name
          http_path
          http_method
          idl_file
          service_name
          request_type
          response_type
        }}
      }}
    }}
    """

    response = execute_graphql_query(graphql_query)
    if not response or "errors" in response:
        return []

    return response.get("data", {}).get("Get", {}).get("IdlApiMapping", [])


def print_advanced_code_impact(analysis_result):
    """
    打印高级代码影响分析结果
    
    参数:
        analysis_result (dict): 分析结果
    """
    if "error" in analysis_result:
        print(f"错误: {analysis_result['error']}")
        return

    print("\n============ 代码影响分析 ============")
    print(f"代码片段:\n{analysis_result['code_snippet']}\n")

    # 打印影响的API
    print("影响的API接口:")
    if analysis_result["affected_apis"]:
        for i, api in enumerate(analysis_result["affected_apis"]):
            print(f"  {i + 1}. API路径: {api.get('api_path', 'unknown')}")
            for definition in api.get("definitions", []):
                print(f"     - 函数: {definition.get('function', '')}")
                print(f"     - HTTP方法: {definition.get('http_method', '')}")
                print(f"     - 请求类型: {definition.get('request_type', '')}")
                print(f"     - 响应类型: {definition.get('response_type', '')}")
    else:
        print("  未找到直接影响的API")

    # 打印影响的函数
    print("\n影响的函数:")
    if analysis_result["affected_functions"]:
        for i, func in enumerate(analysis_result["affected_functions"]):
            print(f"  {i + 1}. 函数: {func.get('function', '')}")
            if func.get("callers"):
                print(f"     - 被调用者: {len(func['callers'])} 个函数")
            if func.get("callees"):
                print(f"     - 调用: {len(func['callees'])} 个函数")
    else:
        print("  未找到直接影响的函数")

    # 打印相关的结构体
    print("\n相关的数据结构:")
    if analysis_result["related_structs"]:
        for i, struct in enumerate(analysis_result["related_structs"]):
            print(f"  {i + 1}. 结构体: {struct.get('struct_name', '')}")
            print(f"     - 文件: {struct.get('idl_file', '')}")
    else:
        print("  未找到相关的数据结构")

    # 打印业务逻辑影响
    print("\n业务逻辑影响:")
    if analysis_result["business_logic_impact"]:
        for i, impact in enumerate(analysis_result["business_logic_impact"]):
            print(f"  {i + 1}. 类型: {impact.get('impact_type', '')}")
            print(f"     - 描述: {impact.get('description', '')}")

            if "condition" in impact:
                print(f"     - 条件: {impact['condition']}")
            if "error_type" in impact:
                print(f"     - 错误类型: {impact['error_type']}")
            if "model" in impact:
                print(f"     - 模型: {impact['model']}")
    else:
        print("  未发现明显的业务逻辑影响")

    print("\n=====================================")


def get_function_detail(function_name, exact=True):
    """
    获取函数的详细信息，包括完整代码实现、注释、导入依赖等
    
    参数:
        function_name (str): 函数名
        exact (bool): 是否精确匹配
        
    返回:
        dict: 函数详细信息
    """
    if not function_name:
        return {"error": "函数名不能为空"}

    # 首先精确匹配查询函数定义
    func_defs = query_by_field("function", function_name, 1, exact)

    if not func_defs:
        return {"error": f"未找到函数: {function_name}"}

    func_def = func_defs[0]

    # 获取函数所在包的其他信息
    package_name = func_def.get("package", "")
    file_path = func_def.get("file_path", "")

    # 获取函数调用关系
    call_chain = get_function_call_chain(function_name, 10, "both")

    # 查询函数是否被API调用
    api_usages = query_function_in_api(function_name)

    # 构建详细信息
    result = {
        "function_name": function_name,
        "package": package_name,
        "file_path": file_path,
        "code": func_def.get("code", ""),
        "comments": func_def.get("comments", ""),
        "imports": func_def.get("imports", []),
        "start_line": func_def.get("start_line", 0),
        "end_line": func_def.get("end_line", 0),
        "callers": call_chain.get("callers", []),
        "callees": call_chain.get("callees", []),
        "api_usages": api_usages
    }

    return result


def query_function_in_api(function_name):
    """
    查询函数是否被API调用或实现
    
    参数:
        function_name (str): 函数名
        
    返回:
        list: API使用情况列表
    """
    if not function_name:
        return []

    # 查询IdlApiMapping中方法名与函数名匹配的记录
    graphql_query = f"""
    {{
      Get {{
        IdlApiMapping(
          where: {{
            path: ["method_name"],
            operator: Equal,
            valueString: "{function_name}"
          }}
          limit: 5
        ) {{
          method_name
          http_path
          http_method
          service_name
          idl_file
        }}
      }}
    }}
    """

    response = execute_graphql_query(graphql_query)
    if not response or "error" in response:
        return []

    api_mappings = response.get("data", {}).get("Get", {}).get("IdlApiMapping", [])

    # 格式化结果
    api_usages = []
    for mapping in api_mappings:
        api_usages.append({
            "api_path": mapping.get("http_path", ""),
            "http_method": mapping.get("http_method", ""),
            "service": mapping.get("service_name", ""),
            "idl_file": mapping.get("idl_file", "")
        })

    return api_usages


def print_function_detail(func_detail):
    """
    打印函数详细信息
    
    参数:
        func_detail (dict): 函数详细信息
    """
    if "error" in func_detail:
        print(f"错误: {func_detail['error']}")
        return

    print("\n" + "=" * 80)
    print(f"函数: {func_detail['function_name']}")
    print("=" * 80)

    print(f"\n包名: {func_detail['package']}")
    print(f"文件路径: {func_detail['file_path']}")
    print(f"行范围: {func_detail['start_line']}-{func_detail['end_line']}")

    # 打印导入信息
    if func_detail.get("imports"):
        print("\n导入依赖:")
        for imp in func_detail["imports"]:
            print(f"  {imp}")

    # 打印注释
    if func_detail.get("comments"):
        print("\n函数注释:")
        for line in func_detail["comments"].split("\n"):
            print(f"  {line}")

    # 打印代码实现
    print("\n代码实现:")
    print("-" * 80)
    for line in func_detail["code"].split("\n"):
        print(line)
    print("-" * 80)

    # 打印调用关系摘要
    print("\n调用关系摘要:")
    print(f"  被调用次数: {len(func_detail['callers'])}")
    print(f"  调用其他函数次数: {len(func_detail['callees'])}")

    # 打印前3个调用者
    if func_detail.get("callers"):
        print("\n主要调用者:")
        for i, caller in enumerate(func_detail["callers"][:3]):
            print(f"  {i + 1}. {caller['function']} (包: {caller['package']})")
        if len(func_detail["callers"]) > 3:
            print(f"  ... 共{len(func_detail['callers'])}个调用者")

    # 打印前3个被调用者
    if func_detail.get("callees"):
        print("\n主要被调用者:")
        for i, callee in enumerate(func_detail["callees"][:3]):
            print(f"  {i + 1}. {callee['function']} (包: {callee['package']})")
        if len(func_detail["callees"]) > 3:
            print(f"  ... 共{len(func_detail['callees'])}个被调用者")

    # 打印API使用情况
    if func_detail.get("api_usages"):
        print("\nAPI接口实现:")
        for i, api in enumerate(func_detail["api_usages"]):
            print(f"  {i + 1}. {api['http_method']} {api['api_path']} (服务: {api['service']})")


def query_main(input_content=None, input_type=None, limit=DEFAULT_LIMIT, exact=False, output=None,
         advanced=False, depth=3, direction="both"):
    """
    主函数，处理输入并执行对应操作
    
    参数:
        input_content (str): 查询内容
        input_type (str): 指定输入类型 (API, FUNC, CODE, ANY, FUNC_DETAIL)
        limit (int): 结果数量限制
        exact (bool): 精确匹配模式
        output (str): 输出文件路径，用于保存函数调用图谱
        advanced (bool): 使用高级代码影响分析
        depth (int): 调用链深度
        direction (str): 调用链方向，可选值: caller, callee, both
        
    返回:
        dict: 查询结果
    """
    # 如果没有输入内容，通过命令行参数处理
    if input_content is None:
        import argparse

        parser = argparse.ArgumentParser(description="代码搜索与分析工具")
        parser.add_argument("input", nargs="?", help="查询内容")
        parser.add_argument("--type", choices=[TYPE_API, TYPE_FUNC, TYPE_CODE, TYPE_ANY, TYPE_FUNC_DETAIL],
                            help="指定输入类型 (API, FUNC, CODE, ANY, FUNC_DETAIL)")
        parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="结果数量限制")
        parser.add_argument("--exact", action="store_true", help="精确匹配模式")
        parser.add_argument("--output", help="输出文件路径，用于保存函数调用图谱")
        parser.add_argument("--read-file", help="从文件读取输入内容")
        parser.add_argument("--depth", type=int, default=3, help="调用链深度，默认为3，最大为5")
        parser.add_argument("--direction", choices=["caller", "callee", "both"], default="both",
                            help="调用链方向，可选值: caller(调用者), callee(被调用者), both(双向)")
        parser.add_argument("--advanced", action="store_true", help="使用高级代码影响分析")

        args = parser.parse_args()

        # 处理输入内容
        input_content = args.input

        # 如果指定了从文件读取
        if args.read_file:
            input_content = safe_read_file(args.read_file)
            if not input_content:
                sys.exit(1)

        # 检查参数
        if not input_content:
            parser.print_help()
            sys.exit(1)

        # 其他参数
        input_type = args.type
        limit = validate_limit(args.limit)
        exact = args.exact
        output = args.output
        advanced = args.advanced
        depth = args.depth
        direction = args.direction

    # 验证limit参数
    limit = validate_limit(limit)

    # 识别输入类型
    if not input_type:
        input_type = detect_input_type(input_content)

    # 结果集
    result = {}

    # 如果指定了查询函数详情，或输入类型为FUNC_DETAIL
    if input_type == TYPE_FUNC_DETAIL:
        if input_type != TYPE_FUNC and input_type != TYPE_FUNC_DETAIL:
            if DEBUG:
                print(f"警告: 将输入内容 '{input_content}' 视为函数名")
        input_type = TYPE_FUNC

        func_detail = get_function_detail(input_content, exact)
        if DEBUG:
            print_function_detail(func_detail)
        return func_detail

    # 基于输入类型执行操作
    if input_type == TYPE_API:
        api_info = search_api_info(input_content, limit, exact)
        if DEBUG:
            print_api_info(api_info)
        return api_info

    elif input_type == TYPE_FUNC:
        # 检查是否需要生成拓扑图
        if depth > 1:
            topology = generate_call_chain_topology(
                input_content,
                max_depth=depth,
                direction=direction,
                output_file=output
            )
            if DEBUG:
                print_call_chain_topology(topology)
            return topology
        else:
            # 只需要获取直接调用关系
            call_chain = get_function_call_chain(input_content, limit, direction)
            if DEBUG:
                print_function_call_chain(call_chain)
            if output:
                generate_function_call_graph(call_chain, output)
            return call_chain

    elif input_type == TYPE_CODE:
        if advanced:
            advanced_impact = analyze_code_impact_advanced(input_content, limit)
            if DEBUG:
                print_advanced_code_impact(advanced_impact)
            return advanced_impact
        else:
            code_impact = analyze_code_impact(input_content, limit)
            if DEBUG:
                print_code_impact(code_impact)
            return code_impact

    else:  # TYPE_ANY
        if DEBUG:
            print(f"执行模糊搜索: '{input_content}' {'(精确匹配)' if exact else '(模糊匹配)'}")
        results = query_all_types(input_content, limit, exact)

        if not results and DEBUG:
            print(f"未找到与 '{input_content}' 相关的结果")
        elif DEBUG:
            print_summary_table(results)

        return results


# if __name__ == "__main__":
#     # 单元测试1：查询API
#     # print("\n" + "=" * 80)
#     # print("测试1: 查询API路径 '/v1/text/chatcompletion'")
#     # print("=" * 80)
#     # main(input_content="/v1/text/chatcompletion", input_type=TYPE_API, limit=10, exact=False)
#     #
#     # # 单元测试2：查询函数
#     # print("\n" + "=" * 80)
#     # print("测试2: 查询函数 'chatCompletion'")
#     # print("=" * 80)
#     # main(input_content="chatCompletion", input_type=TYPE_FUNC, limit=10, exact=False)
#
#     # 单元测试3：查询函数详情
#     print("\n" + "=" * 80)
#     print("测试3: 查询函数详情 'chatCompletion'")
#     print("=" * 80)
#     query_main(input_content="chatCompletion", input_type=TYPE_FUNC_DETAIL, limit=10, exact=False)
