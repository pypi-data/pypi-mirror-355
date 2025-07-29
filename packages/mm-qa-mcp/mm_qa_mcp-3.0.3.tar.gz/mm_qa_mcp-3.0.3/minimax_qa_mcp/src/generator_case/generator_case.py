"""
coding:utf-8
@Software: PyCharm
@Time: 2025/4/8 17:02
@Author: xingyun
@Desc: case自动生成tools
"""
import os
import json
import requests
import subprocess
import sys
import re
import shutil
from pathlib import Path

import concurrent.futures
import threading
from typing import Type, Union, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from datetime import datetime, timedelta, timezone
from langchain_core.runnables import Runnable
from minimax_qa_mcp.src.query_segments.query_segments import query_main as query_segments_main
from minimax_qa_mcp.src.gateway_case.get_case import CaseGrafanaService
from minimax_qa_mcp.utils.utils import Utils
from minimax_qa_mcp.utils.logger import logger

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

# 添加线程锁用于日志
log_lock = threading.Lock()


# 添加重试装饰器函数
def retry_on_exception(
        max_attempts: int = 3,
        retry_exceptions: Union[Type[Exception], List[Type[Exception]]] = (Exception,),
        min_wait: float = 1,
        max_wait: float = 10
):
    """为函数添加重试能力的装饰器
    
    Args:
        max_attempts: 最大重试次数 
        retry_exceptions: 需要重试的异常类型
        min_wait: 最小等待时间(秒)
        max_wait: 最大等待时间(秒)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_exceptions),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            f"重试操作 ({retry_state.attempt_number}/{max_attempts}): "
            f"{retry_state.fn.__name__} 因为 {retry_state.outcome.exception()}"
        )
    )


class ModuleClient:
    """模型调用客户端"""

    def __init__(self):
        # 从配置文件读取API URL，如果不存在则使用默认值
        try:
            self.api_url = Utils.get_conf("generator_case_conf", "module_api_url")
            logger.info(f"从配置读取模型API地址: {self.api_url}")
        except KeyError:
            # 默认API URL
            self.api_url = "http://swing-babel-ali-prod.xaminim.com/swing/api/get_module_result"
            logger.info(f"未找到API地址配置，使用默认地址: {self.api_url}")

        # 增加请求超时设置
        self.timeout = int(Utils.get_conf("generator_case_conf", "model_timeout"))
        logger.info(f"模型请求超时设置: {self.timeout}秒")

    @retry_on_exception(
        max_attempts=3,
        retry_exceptions=(requests.RequestException, json.JSONDecodeError, KeyError),
        min_wait=2,
        max_wait=15
    )
    def call_model(self, params):
        """调用模型API，添加了重试机制
        
        Args:
            params: 模型输入参数
            
        Returns:
            模型返回的结果
        """
        # 使用更简单的字符串替换处理，减少转义层级
        clean_params = params.replace('\\"', "'")  # 替换嵌套双引号为单引号
        clean_params = clean_params.replace("\n", " ").strip()

        payload = {
            "scene": "qa_agent",
            "params": {
                "user_content": clean_params
            }
        }

        # 使用线程锁保护日志
        with log_lock:
            # logger.info(f"==== 发送请求到API，payload: {json.dumps(payload, ensure_ascii=False)}")
            logger.info(f"==== 发送请求调用模型 ======")

        # 添加timeout参数，增加请求超时控制
        response = requests.post(
            self.api_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            verify=False,
            timeout=self.timeout
        )

        with log_lock:
            logger.info(f"API响应状态码: {response.status_code}")
            # logger.info(f"API响应内容: {response.text}")

        # 检查响应状态
        if response.status_code != 200:
            raise requests.RequestException(f"API请求失败，状态码: {response.status_code}")

        if response.status_code == 200:
            # 尝试解析JSON响应
            try:
                resp_json = response.json()
                # logger.info(f"解析后的JSON: {json.dumps(resp_json, ensure_ascii=False)}")

                if 'response' in resp_json:
                    # 解析二层JSON
                    try:
                        model_response = json.loads(resp_json['response'])
                        # logger.info(f"解析二层JSON: {json.dumps(model_response, ensure_ascii=False)}")

                        # 从content中提取文本
                        if 'content' in model_response and isinstance(model_response['content'], list):
                            text_content = ""
                            for item in model_response['content']:
                                if item.get('type') == 'text':
                                    text_content += item.get('text', '')
                            # logger.info(f"提取的文本内容: {text_content}")
                            return text_content
                        return str(model_response)
                    except Exception as e:
                        logger.error(f"解析二层JSON失败: {e}")
                        # 直接返回原始响应，避免额外解码可能导致的编码问题
                        return resp_json['response']
                return response.text
            except Exception as e:
                logger.error(f"解析JSON失败: {e}")
                return response.text

        return response.text


class CustomRunnable(Runnable):
    """自定义Runnable接口，用于langchain调用"""

    def __init__(self):
        self.client = ModuleClient()

    def invoke(self, input, config=None):
        """调用模型API
        
        Args:
            input: 可以是字符串或字典
            config: 配置参数
        
        Returns:
            生成的文本
        """
        if isinstance(input, dict):
            # 如果输入是字典，尝试构建提示词
            prompt = input.get("text", "")
            for key, value in input.items():
                if key != "text" and isinstance(value, str):
                    prompt = prompt.replace(f"{{{key}}}", value)
        elif isinstance(input, str):
            prompt = input
        else:
            prompt = str(input)

        # 打印模型输入
        logger.info(f"调用模型API，输入：{prompt}")

        # 调用模型
        response = self.client.call_model(prompt)

        # 打印模型输出
        logger.info(f"调用模型API，输出：{response}")

        # 直接返回解析后的响应
        return response


class GeneratorCase:
    def __init__(self, input_data, pwd):
        """初始化GeneratorCase类
        
        Args:
            input_data: JSON格式的输入数据，包含Business、API和Case信息
            pwd: 用户当前的目录地址
        """
        # 初始化基本属性
        self.model = CustomRunnable()
        self.pwd = pwd
        self.workspace_dir = Path(os.getcwd())

        # 设置访问令牌
        try:
            self.access_token = Utils.get_conf("generator_case_conf", "git_access_token")
            logger.info("从配置读取 git access token")
        except KeyError:
            logger.warning("未找到 git access token 配置，将使用无认证方式")
            self.access_token = None

        # 如果输入是字符串，尝试解析为JSON对象
        if isinstance(input_data, str):
            try:
                self.input_data = json.loads(input_data)
            except json.JSONDecodeError as e:
                logger.error(f"输入数据不是有效的JSON格式: {e}")
                raise ValueError(f"输入数据不是有效的JSON格式: {str(e)}")
        else:
            self.input_data = input_data

        # 解析API和Case信息
        self._parse_input_data()

        # 初始化其他依赖于业务类型的属性
        self.result_dir = self.workspace_dir / "case_results"
        self.result_dir.mkdir(exist_ok=True)
        self.repo_dir = self.workspace_dir / "git_repos" / self.business

        # 设置默认的时间范围为1天
        now = datetime.now(timezone(timedelta(hours=8)))
        self.to_time = now.isoformat()
        self.from_time = (now - timedelta(hours=3)).isoformat()

        # 根据业务名称确定场景
        self.scene_mapping = {
            "xingye": "xingye_http_prod",
            "hailuo": "hailuo_video_cn_prod",
            "kaiping": "talkie_prod"
        }
        self.scene = self.scene_mapping.get(self.business, "xingye_prod")

        # 设置默认值
        self.is_need_module = True
        self.case_type = "link"
        self.is_need_save = True

        # 增加并发配置
        try:
            self.max_workers = int(Utils.get_conf("generator_case_conf", "max_workers"))
            logger.info(f"设置最大并发数: {self.max_workers}")
        except (ValueError, KeyError):
            self.max_workers = 4
            logger.info(f"使用默认最大并发数: {self.max_workers}")

        logger.info(
            f"初始化GeneratorCase: api_name={self.api_name}, business={self.business}, case_type={self.case_type}")

    def _parse_input_data(self):
        """解析输入的JSON数据，提取API和Case信息"""
        # 检查输入数据结构是否符合预期
        required_fields = ['Business', 'API', 'Case']
        for field in required_fields:
            if field not in self.input_data:
                logger.error(f"输入数据格式错误，必须包含'{field}'字段")
                raise ValueError(f"输入数据格式错误，必须包含'{field}'字段")

        # 从JSON中提取业务类型
        self.business = self.input_data.get('Business')
        if not self.business:
            logger.error("Business字段值为空")
            raise ValueError("Business字段值为空，必须指定业务类型")
        logger.info(f"从JSON中提取业务类型: {self.business}")

        # 提取API信息
        api_info = self.input_data['API']
        if not api_info:
            logger.error("API信息为空")
            raise ValueError("API信息为空")

        # 设置所有API列表
        self.all_apis = list(api_info.keys())
        if not self.all_apis:
            logger.error("API列表为空")
            raise ValueError("API列表为空，至少需要提供一个API")

        # 所有API都是平等的，但仍需要一个api_name用于日志和文件名
        self.api_name = self.all_apis[0] if self.all_apis else ""
        self.api_descriptions = api_info

        # 解析Case信息
        case_info = self.input_data['Case']
        if not case_info or not isinstance(case_info, list):
            logger.error("Case信息为空或格式错误")
            raise ValueError("Case信息为空或格式错误")

        # 提取前置操作和测试场景
        self.pre_apis = []
        self.cases = []
        self.detailed_pre_info = {}
        self.detailed_case_info = {}
        self.case_items = []  # 保存原始的case项

        for case_item in case_info:
            self.case_items.append(case_item)  # 保存完整的case item
            for case_name, case_data in case_item.items():
                # 添加case名称
                self.cases.append(case_name)

                # 提取前置操作
                if 'PRE' in case_data and isinstance(case_data['PRE'], dict):
                    for pre_name, pre_desc in case_data['PRE'].items():
                        if pre_name not in self.pre_apis:
                            self.pre_apis.append(pre_name)
                        # 保存详细前置信息
                        if pre_name not in self.detailed_pre_info:
                            self.detailed_pre_info[pre_name] = []
                        self.detailed_pre_info[pre_name].append(pre_desc)

                # 提取测试步骤
                if 'TEST' in case_data:
                    # 保存详细测试信息
                    self.detailed_case_info[case_name] = {
                        'steps': [],
                        'pre': list(case_data.get('PRE', {}).keys()),
                        'test': [case_data['TEST']]
                    }

        # 设置API详细信息的格式
        self.detailed_api_info = {}
        for api_path, api_desc in self.api_descriptions.items():
            # 提取API名称（可能作为分组）
            api_name = api_path.split('/')[-1] if '/' in api_path else api_path
            self.detailed_api_info[api_name] = [{
                'path': api_path,
                'description': api_desc
            }]

        logger.info(f"解析输入数据完成: API数量={len(self.all_apis)}, 前置操作={self.pre_apis}, Cases={self.cases}")

    def _get_api_data_from_grafana(self, api_name):
        """从Grafana获取API的请求和响应数据
        
        Args:
            api_name: API名称
            
        Returns:
            dict: API的请求和响应数据
        """
        logger.info(
            f"从Grafana获取API数据: {api_name}, scene={self.scene}, 时间范围: {self.from_time} 至 {self.to_time}")
        grafana_client = CaseGrafanaService(
            scene=self.scene,
            from_time=self.from_time,
            to_time=self.to_time
        )
        api_data = grafana_client.process_api_path_with_service(api_name)
        logger.info(f"== 从Grafana获取API数据完成: {api_data}")

        # 不再在这里进行模型总结，而是由 _summarize_api_data_concurrently 并发处理
        return {"raw_data": api_data}

    def _get_code_repo(self):
        """获取业务对应的代码仓库，并获取link case和pre的demo
        
        Returns:
            dict: 代码仓库信息和demo case
        """
        # 从配置文件获取git仓库地址
        git_url = Utils.get_conf("generator_case_conf", f"{self.business}_git_url")
        logger.info(f"获取代码仓库: {self.business}, git_url={git_url}")

        # 从配置文件获取分支信息
        branch = "main"  # 默认使用main分支
        try:
            branch = Utils.get_conf("generator_case_conf", f"{self.business}_branch")
            logger.info(f"获取代码分支: {branch}")
        except KeyError:
            logger.info(f"未找到分支配置，将使用默认分支: {branch}")

        # 从配置文件获取demo case路径和pre demo路径
        demo_case_path_key = f"{self.business}_link_case_demo_path"
        pre_demo_path_key = f"{self.business}_pre_demo_case_path"

        try:
            demo_case_path = Utils.get_conf("generator_case_conf", demo_case_path_key)
            logger.info(f"获取demo case路径: {demo_case_path}")
        except KeyError:
            logger.error(f"未找到demo case路径配置: {demo_case_path_key}")
            raise ValueError(f"未指定{self.business}业务的demo case路径，请在conf.ini中配置{demo_case_path_key}")

        try:
            pre_demo_path = Utils.get_conf("generator_case_conf", pre_demo_path_key)
            logger.info(f"获取pre demo路径: {pre_demo_path}")
        except KeyError:
            logger.warning(f"未找到pre demo路径配置: {pre_demo_path_key}，将使用空内容")
            pre_demo_path = None

        # 删除并重新创建存放代码仓库的目录
        if self.repo_dir.exists():
            logger.info(f"删除已存在的仓库目录: {self.repo_dir}")
            shutil.rmtree(str(self.repo_dir))

        # 创建存放代码仓库的目录
        self.repo_dir.parent.mkdir(exist_ok=True)
        self.repo_dir.mkdir(exist_ok=True)
        logger.info(f"创建新的仓库目录: {self.repo_dir}")

        # 克隆或更新代码仓库
        demo_cases = {}
        pre_demos = {}
        if not git_url:
            error_msg = f"未找到 {self.business} 的git仓库地址配置"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # 修改git URL格式，如果有访问令牌则使用HTTPS方式
            clone_url = git_url
            if self.access_token:
                if git_url.startswith("git@"):
                    # 将SSH格式(git@gitlab.xaminim.com:qa/repo.git)转换为
                    # HTTPS格式(https://oauth2:token@gitlab.xaminim.com/qa/repo.git)
                    domain = git_url.split('@')[1].split(':')[0]
                    repo_path = git_url.split(':')[1]
                    clone_url = f"https://oauth2:{self.access_token}@{domain}/{repo_path}"
                    logger.info(f"已将SSH格式URL转换为HTTPS格式并添加access token")
                elif git_url.startswith("http://") or git_url.startswith("https://"):
                    # 处理HTTPS格式URL: https://gitlab.xaminim.com/qa/repo.git
                    # 转换为: https://oauth2:token@gitlab.xaminim.com/qa/repo.git
                    protocol = git_url.split('://')[0]
                    rest_url = git_url.split('://')[1]
                    
                    # 检查URL中是否已经包含认证信息
                    if '@' not in rest_url:
                        clone_url = f"{protocol}://oauth2:{self.access_token}@{rest_url}"
                        logger.info(f"已向HTTPS格式URL添加access token")
                    else:
                        logger.info(f"URL已包含认证信息，不再添加access token")
                else:
                    logger.warning(f"无法识别的git URL格式: {git_url}，将使用原始URL")
            else:
                logger.warning(f"未提供access token，将使用原始git URL进行克隆")
            
            # 克隆仓库
            logger.info(f"克隆代码仓库: {clone_url} -> {self.repo_dir}")
            subprocess.run(
                ["git", "clone", clone_url, str(self.repo_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 如果不是默认分支，需要切换分支
            if branch != "main" and branch != "master":
                logger.info(f"切换到分支: {branch}")
                subprocess.run(
                    ["git", "checkout", branch],
                    cwd=str(self.repo_dir),
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            # 构建demo case的完整路径（相对于仓库根目录）
            full_demo_path = self.repo_dir / demo_case_path
            logger.info(f"查找指定的demo case: {full_demo_path}")

            # 读取指定的demo case文件
            if os.path.isfile(full_demo_path):
                with open(full_demo_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    demo_cases[os.path.basename(full_demo_path)] = content
                    logger.info(f"找到demo case文件: {full_demo_path}")
            else:
                logger.warning(f"指定的demo case路径不存在或不是文件: {full_demo_path}")
                # 直接抛出异常，不再尝试创建默认demo文件
                error_msg = f"指定的demo case路径 '{demo_case_path}' 不存在或不是文件，请检查配置"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

            # 如果有pre demo path，也读取它
            if pre_demo_path:
                full_pre_demo_path = self.repo_dir / pre_demo_path
                logger.info(f"查找指定的pre demo: {full_pre_demo_path}")

                if os.path.isfile(full_pre_demo_path):
                    with open(full_pre_demo_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        pre_demos[os.path.basename(full_pre_demo_path)] = content
                        logger.info(f"找到pre demo文件: {full_pre_demo_path}")
                else:
                    logger.warning(f"指定的pre demo路径不存在或不是文件: {full_pre_demo_path}")

            # 获取完demo后删除git仓库
            logger.info(f"已读取必要的demo文件，删除git仓库: {self.repo_dir}")
            shutil.rmtree(str(self.repo_dir))

            # 检查父目录是否为空，如果为空也删除
            parent_dir = self.repo_dir.parent
            if parent_dir.exists() and not any(parent_dir.iterdir()):
                logger.info(f"父目录为空，一并删除: {parent_dir}")
                shutil.rmtree(str(parent_dir))

        except Exception as e:
            logger.error(f"获取代码仓库失败: {e}")
            # 删除仓库目录
            if self.repo_dir.exists():
                logger.info(f"由于错误，删除仓库目录: {self.repo_dir}")
                shutil.rmtree(str(self.repo_dir))

                # 检查父目录是否为空，如果为空也删除
                parent_dir = self.repo_dir.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    logger.info(f"父目录为空，一并删除: {parent_dir}")
                    shutil.rmtree(str(parent_dir))
            # 直接抛出异常，不再尝试创建本地备用文件
            error_msg = f"获取代码仓库失败: {str(e)}，请检查git配置和网络连接"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return {
            "repo_info": f"{self.business} repository at {git_url}, branch: {branch}",
            "demo_cases": demo_cases,
            "pre_demos": pre_demos
        }

    def _get_api_code_segments(self, api_name=None):
        """调用query_code_segments，获取API相关的出入参数以及业务逻辑
        Args:
            api_name: api名称
        
        Returns:
            dict: API相关的代码段信息
        """
        if api_name is None:
            api_name = self.api_name

        # 确保API名称格式一致
        if not api_name.startswith('/'):
            api_name = f"/{api_name}"

        logger.info(f"获取API代码段: {api_name}")

        # 直接调用main函数，参照server.py中的调用方式
        code_segments = query_segments_main(
            input_content=api_name,
            input_type="API",
            limit=10,
            exact=False,
            depth=1,
            direction="both",
            advanced=False,
            output=None
        )

        # 不再在这里进行模型总结，而是由_summarize_api_data_concurrently并发处理
        return {"raw_segments": code_segments}

    def _get_api_data_concurrently(self):
        """并发获取所有API的数据
        
        Returns:
            dict: 所有API的数据，包含Grafana信息和代码段
        """
        logger.info(f"开始并发获取 {len(self.all_apis)} 个API的数据")
        api_data = {}

        def process_single_api(api):
            """处理单个API的数据获取
            
            Args:
                api: API名称
                
            Returns:
                tuple: (API名称, API数据)
            """
            with log_lock:
                logger.info(f"开始获取API数据: {api}")

            api_result = {}
            try:
                # 获取Grafana信息
                api_result["grafana_info"] = self._get_api_data_from_grafana(api)
                # 获取代码段信息
                api_result["code_segments"] = self._get_api_code_segments(api)

                with log_lock:
                    logger.info(f"成功获取API数据: {api}")

                return api, api_result
            except Exception as e:
                with log_lock:
                    logger.error(f"获取API {api} 数据失败: {e}")
                return api, {"error": str(e)}

        # 使用线程池并发处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有API数据获取任务
            future_to_api = {executor.submit(process_single_api, api): api for api in self.all_apis}

            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_api):
                api = future_to_api[future]
                try:
                    api_name, api_result = future.result()
                    api_data[api_name] = api_result
                except Exception as e:
                    with log_lock:
                        logger.error(f"处理API {api} 结果时出错: {e}")
                    api_data[api] = {"error": f"处理结果时出错: {str(e)}"}

        logger.info(f"并发获取所有API数据完成，共 {len(api_data)} 个API")
        return api_data

    def _summarize_api_data_concurrently(self, api_data):
        """并发使用模型总结API数据
        
        Args:
            api_data: 所有API的原始数据
            
        Returns:
            dict: 添加了模型总结的API数据
        """
        if not self.is_need_module:
            return api_data

        logger.info(f"开始并发总结 {len(api_data)} 个API的数据")

        def summarize_single_api(api_name, data):
            """使用模型总结单个API的数据
            
            Args:
                api_name: API名称
                data: API数据
                
            Returns:
                tuple: (API名称, 总结结果)
            """
            with log_lock:
                logger.info(f"开始总结API数据: {api_name}")

            try:
                if "grafana_info" in data and "raw_data" in data["grafana_info"]:
                    raw_data = data["grafana_info"]["raw_data"]

                    # 使用模型总结API数据
                    summary_prompt = """请总结分析以下API的请求和响应数据，提取关键信息：
                        
                        API数据:
                        {api_data}
                        
                        请提供：
                        1. 请求参数的结构和关键字段
                        2. 响应数据的结构和关键字段
                        3. 可能的业务逻辑和数据流向
                        """

                    # 使用简单的替换方式
                    summary = self.model.invoke(
                        summary_prompt.replace("{api_data}", json.dumps(raw_data, ensure_ascii=False))
                    )

                    # 添加总结到数据中
                    data["grafana_info"]["summary"] = summary

                if "code_segments" in data and "raw_segments" in data["code_segments"]:
                    raw_segments = data["code_segments"]["raw_segments"]

                    # 使用模型总结代码段
                    code_prompt = """请分析以下API相关的代码段，提取关键信息：
                        
                        代码段:
                        {code_segments}
                        
                        请提供：
                        1. API的输入参数定义及其数据类型
                        2. API的输出参数定义及其数据类型
                        3. API的主要业务逻辑
                        4. 关键的依赖和调用关系
                        """

                    # 使用简单的替换方式
                    summary = self.model.invoke(
                        code_prompt.replace("{code_segments}", json.dumps(raw_segments, ensure_ascii=False))
                    )

                    # 添加总结到数据中
                    data["code_segments"]["summary"] = summary

                with log_lock:
                    logger.info(f"完成API数据总结: {api_name}")

                return api_name, data
            except Exception as e:
                with log_lock:
                    logger.error(f"总结API {api_name} 数据失败: {e}")
                return api_name, data  # 返回原始数据，确保流程不中断

        # 使用线程池并发处理
        summarized_data = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有API总结任务
            future_to_api = {
                executor.submit(summarize_single_api, api_name, data): api_name
                for api_name, data in api_data.items()
            }

            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_api):
                api_name = future_to_api[future]
                try:
                    _, summarized = future.result()
                    summarized_data[api_name] = summarized
                except Exception as e:
                    with log_lock:
                        logger.error(f"处理API {api_name} 总结结果时出错: {e}")
                    summarized_data[api_name] = api_data[api_name]  # 保留原始数据

        logger.info(f"并发总结所有API数据完成")
        return summarized_data

    def _generate_case_with_model(self, api_info, api_data, repo_info, case_item, case_index):
        """为单个case生成测试用例
        
        Args:
            api_info: API信息，包含所有API的基本信息
            api_data: 所有API的数据，包含Grafana信息和代码段信息
            repo_info: 代码仓库信息，包含demo cases和pre demos
            case_item: 当前case的信息
            case_index: case的索引
            
        Returns:
            dict: 包含case和pre代码的字典
        """
        case_name = list(case_item.keys())[0]
        case_data = case_item[case_name]

        logger.info(f"为case {case_name} 生成测试用例, type={self.case_type}")

        # 获取demo案例作为参考
        demo_cases = repo_info.get("demo_cases", {})
        pre_demos = repo_info.get("pre_demos", {})

        demo_case_content = ""
        pre_demo_content = ""

        if demo_cases:
            # 使用第一个demo作为参考
            demo_case_content = list(demo_cases.values())[0]
            logger.info(f"找到demo case作为参考，长度: {len(demo_case_content)}")
        else:
            logger.warning("未找到demo case作为参考，将生成标准格式的测试用例")

        if pre_demos:
            # 使用第一个pre demo作为参考
            pre_demo_content = list(pre_demos.values())[0]
            logger.info(f"找到pre demo作为参考，长度: {len(pre_demo_content)}")
        else:
            logger.warning("未找到pre demo作为参考，将使用标准格式生成前置操作")

        # 提取当前case的前置操作信息
        pre_apis = list(case_data.get('PRE', {}).keys())
        pre_details = {}
        for pre_name, pre_desc in case_data.get('PRE', {}).items():
            pre_details[pre_name] = pre_desc

        # 提取当前case的测试步骤
        test_steps = case_data.get('TEST', '')

        # 定义示例代码，避免在f-string中嵌套三重反引号
        expect_example = """'expect': {
    'base_resp': {
        'status_code': 0,
        'status_msg': 'success'
    },
    'user_card_list': {
        'contain': {'card_choice_id': card_id}  # 验证card_id存在于返回的卡牌列表中
    }
}"""

        # 根据JSON提取的信息构建场景化的模板
        template = f"""你是一个资深的python代码工程师，请针对以下单个测试场景，生成两个独立的Python文件：一个是前置操作文件，一个是测试用例文件。

业务: {self.business}
所有API: {', '.join(api_info['all_apis'])}

当前需要实现的测试场景：

场景名称: {case_name}
前置操作: {json.dumps(pre_apis, ensure_ascii=False)}
前置操作详情: {json.dumps(pre_details, ensure_ascii=False)}
测试步骤: {test_steps}

API基本描述: {json.dumps(self.api_descriptions, ensure_ascii=False)}
所有API数据: {json.dumps(api_data, ensure_ascii=False)}
代码仓库信息: {json.dumps(repo_info, ensure_ascii=False)}

## 参考的demo case格式:
```python
{demo_case_content}
```

## 参考的pre demo格式:
```python
{pre_demo_content}
```

请生成以下两个文件：

1. 前置操作文件 (pre_file)：
   - 文件应该包含所有必要的前置操作函数实现，如daily_free(), vip_free()等
   - 格式应参考pre demo
   - 作为独立文件能被测试用例导入和使用

2. 测试用例文件 (case_file)：
   - 针对具体的测试场景"{case_name}"
   - 实现该场景的完整测试流程
   - 导入并使用前置操作文件中的函数
   - 所有的初始化的参数 都应该放在 setup_class 里面
   - 格式应参考demo case
   - 【非常重要】必须为每个子测试场景单独创建独立的test_方法，例如:
     * 如果有多种类型测试，应该为每种类型单独创建一个test_方法
     * 每个test_方法应该有明确的命名、注释和完整测试流程
     * 不要在一个test_方法中循环执行多个测试场景
   - 【非常重要】确保API之间的数据关联性和验证：
     * 每个API方法不仅要检查base_resp成功状态，还应从响应中提取关键数据并返回
     * 例如，get_all_direct_card方法应该提取并返回card_choice_id或card_id
     * list_my_story_card_by_npc方法应该返回完整的卡牌列表响应
     * 测试方法中，必须验证前一个API返回的数据在后续API中是否正确使用或出现
   -【非常重要】验证应放在API调用的expect字典中，demo_case 里面有expect支持的所有类型，切勿自己自定义类型，如果不支持的expect，可以允许自己写 assert进行校验

3. 关于测试链路的实现 (LINK链路)：
   - 【非常重要】请严格按照测试步骤中指定的API链路顺序执行
   - 例如，如果测试步骤为 "API1 -> API2 -> API3"，则在同一个测试方法中依次调用这些API
   - 确保在每个单独的test_方法中都实现完整的API调用链路
   - 测试方法应该实现完整的业务流程，从获取用户ID，到依次调用各个API，再到最终验证整个流程

4. 数据验证要求：
   -【非常重要】验证应放在API调用的expect字典中，demo_case里面有expect支持的所有类型，切勿自己自定义类型，如果不支持的expect，可以允许自己写 assert进行校验
   -【非常重要】你需要结合IDL和API相关描述等有关于API的相关信息 来进行合理的数据校验，而不是自己去杜撰接口的返回参数！！并且尽可能多的对返回的数据的字段进行assert校验！！
   - 如果API调用生成了重要数据(如card_id)，后续API必须验证这些数据
   - 所有的校验都应该放在请求以后
   - 例如，验证card_id存在于卡牌列表中应该这样实现：
   
{expect_example}


请确保生成的两个文件互相配合，测试用例文件能够正确导入和使用前置操作文件中的功能。
前置操作方法应参考pre demo的格式实现，如果pre demo为空，则使用标准格式实现前置操作。
保持相同的代码风格、错误处理方式和断言格式。

请遵循以下Python代码格式规范:
1. 使用四个空格进行缩进，不要使用制表符
2. 类定义后空两行，方法定义后空一行
3. 使用单引号表示字符串，除非字符串中包含单引号
4. 注释应该是完整的句子，并以句号结尾
5. 导入模块应该一行一个，并按照标准库、第三方库、本地库的顺序排列
6. 确保代码中没有过长的行（最好不超过100个字符）
7. 变量和方法使用小写字母和下划线命名法

在你的回复中，请清晰地用markdown代码块分别标记这两个文件的内容，例如：

# 前置操作文件(pre_{case_name}.py):
```python
# 前置操作文件内容
```

# 测试用例文件(test_link_{case_name}.py):
```python
# 测试用例文件内容
```
"""

        # 直接使用模型生成
        raw_response = self.model.invoke(template)
        # logger.info(f"模型返回的响应: {raw_response}")

        # 如果响应为空，返回空字符串
        if not raw_response:
            logger.warning("模型返回的响应为空")
            return {"case_code": "", "pre_code": ""}

        # 提取前置操作文件的Python代码块
        pre_code_blocks = re.findall(r'# 前置操作文件.*?```python\s*(.*?)\s*```', raw_response, re.DOTALL)
        # 提取测试用例文件的Python代码块
        case_code_blocks = re.findall(r'# 测试用例文件.*?```python\s*(.*?)\s*```', raw_response, re.DOTALL)

        # 如果没有找到明确标记的代码块，尝试提取所有Python代码块
        if not pre_code_blocks or not case_code_blocks:
            all_code_blocks = re.findall(r'```python\s*(.*?)\s*```', raw_response, re.DOTALL)
            if len(all_code_blocks) >= 2:
                pre_code_blocks = [all_code_blocks[0]]
                case_code_blocks = [all_code_blocks[1]]
            elif len(all_code_blocks) == 1:
                # 只有一个代码块，假设是测试用例
                case_code_blocks = [all_code_blocks[0]]
                pre_code_blocks = ["# 未找到前置操作代码"]

        pre_code = pre_code_blocks[0] if pre_code_blocks else "# 未找到前置操作代码"
        case_code = case_code_blocks[0] if case_code_blocks else "# 未找到测试用例代码"

        logger.info(f"为case {case_name} 生成的前置操作代码长度: {len(pre_code)}")
        logger.info(f"为case {case_name} 生成的测试用例代码长度: {len(case_code)}")

        return {
            "pre_code": pre_code,
            "case_code": case_code,
            "case_name": case_name,
            "case_index": case_index
        }

    def _format_output_files(self, pre_code, case_code, case_name):
        """格式化输出的文件内容，修复常见格式问题
        
        Args:
            pre_code: 前置操作代码
            case_code: 测试用例代码
            case_name: 测试用例名称
            
        Returns:
            tuple: 修复后的(pre_code, case_code)
        """
        logger.info(f"开始格式化生成的代码文件: {case_name}")

        # 修复开头的转义问题
        if pre_code.startswith('\\n'):
            pre_code = pre_code[2:]
        if case_code.startswith('\\n'):
            case_code = case_code[2:]

        # 直接处理常见转义字符，避免unicode_escape造成中文乱码
        # 修复引号的转义问题
        pre_code = pre_code.replace("\\'\\'\\'", "'''")  # 三引号
        case_code = case_code.replace("\\'\\'\\'", "'''")
        pre_code = pre_code.replace("\\'", "'")  # 单引号
        case_code = case_code.replace("\\'", "'")
        pre_code = pre_code.replace('\\"', '"')  # 双引号
        case_code = case_code.replace('\\"', '"')

        # 修复换行符的转义问题
        pre_code = pre_code.replace("\\n", "\n")
        case_code = case_code.replace("\\n", "\n")

        # 修复制表符的转义问题
        pre_code = pre_code.replace("\\t", "\t")
        case_code = case_code.replace("\\t", "\t")

        # 修复反斜杠的转义问题
        pre_code = pre_code.replace("\\\\", "\\")
        case_code = case_code.replace("\\\\", "\\")

        # 修复日志输出中的换行符问题
        # 匹配类似 logger.info('文本: \n' + xxx) 这样的模式
        case_code = re.sub(r"logger\.info\('([^']*?):\\s*\\n'\s*\+", r"logger.info('\1: ' +", case_code)
        case_code = re.sub(r"logger\.info\(\"([^\"]*?):\\s*\\n\"\s*\+", r"logger.info(\"\1: \" +", case_code)

        # 修复代码中使用反斜杠续行导致的换行问题
        # 匹配类似 logger.info('文本:\' + xxx) 这样的模式
        case_code = re.sub(r"logger\.info\('([^']*?):\\\s*'\s*\+", r"logger.info('\1: ' +", case_code)
        case_code = re.sub(r"logger\.info\(\"([^\"]*?):\\\s*\"\s*\+", r"logger.info(\"\1: \" +", case_code)

        # 修复日志输出中直接使用\n换行符的问题
        # 匹配类似 logger.info('文本:
        # ' + xxx) 这样的模式
        case_code = re.sub(r"logger\.info\('([^']*?):\s*\n'\s*\+", r"logger.info('\1: ' +", case_code)
        case_code = re.sub(r"logger\.info\(\"([^\"]*?):\s*\n\"\s*\+", r"logger.info(\"\1: \" +", case_code)

        # 修复导入名称问题
        from_import = f"from card_operations_pre import"
        if from_import in case_code:
            file_prefix = f"pre_{case_name}"
            new_import = f"from {file_prefix} import"
            case_code = case_code.replace(from_import, new_import)

        logger.info(f"完成格式化生成的代码文件: {case_name}")
        return pre_code, case_code

    def _save_cases_to_files(self, case_results):
        """将生成的cases和pres保存到本地
        
        Args:
            case_results: 包含case和pre代码的列表
            
        Returns:
            list: 保存的文件路径列表
        """
        file_result = []
        # 创建案例根目录
        case_root_dir = self.result_dir / self.case_type / f"{self.api_name.replace('.', '_').replace('/', '_')}_{self.business}"
        case_root_dir.mkdir(exist_ok=True, parents=True)

        for result in case_results:
            file_result_one = {}  # 在循环内创建新的字典，避免复用同一个引用
            case_name = result.get("case_name", "unknown")
            case_index = result.get("case_index", 0)
            pre_code = result.get("pre_code", "")
            case_code = result.get("case_code", "")

            # 格式化输出的代码内容
            pre_code, case_code = self._format_output_files(pre_code, case_code, case_name)

            # 为每个case创建单独的目录
            # 将字符串转换为Path对象，然后进行路径拼接
            case_dir = Path(self.pwd) / f"{case_name}"

            pre_file_path = case_dir / f"pre_{case_name}.py"
            file_result_one["pre_case_dir"] = str(pre_file_path)
            file_result_one['pre_case_result'] = pre_code
            case_file_path = case_dir / f"test_link_{case_name}.py"
            file_result_one["case_dir"] = str(case_file_path)
            file_result_one['case_result'] = case_code

            file_result.append(file_result_one)

            # case_dir.mkdir(exist_ok=True)

            # # 保存前置操作文件，明确使用UTF-8 编码
            # pre_file_path = case_dir / f"pre_{case_name}.py"
            # with open(pre_file_path, "w", encoding="utf-8") as f:
            #     f.write(pre_code)
            # logger.info(f"前置操作已保存到: {pre_file_path}")
            # saved_paths.append(str(pre_file_path))
            #
            # # 保存测试用例文件，明确使用UTF-8 编码
            # case_file_path = case_dir / f"test_{case_name}.py"
            # with open(case_file_path, "w", encoding="utf-8") as f:
            #     f.write(case_code)
            # logger.info(f"测试用例已保存到: {case_file_path}")
            # saved_paths.append(str(case_file_path))

        return file_result

    def _process_case_concurrently(self, api_info, api_data, repo_info):
        """并发处理多个case任务
        
        Args:
            api_info: API信息
            api_data: API数据
            repo_info: 仓库信息
            
        Returns:
            list: 包含所有case结果的列表
        """
        logger.info(f"启动并发处理 {len(self.case_items)} 个case任务，最大并发数: {self.max_workers}")
        results = []

        # 创建线程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有case生成任务到线程池
            future_to_case = {
                executor.submit(
                    self._generate_case_with_model,
                    api_info,
                    api_data,
                    repo_info,
                    case_item,
                    i + 1
                ): (case_item, i + 1) for i, case_item in enumerate(self.case_items)
            }

            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_case):
                case_item, case_index = future_to_case[future]
                try:
                    case_result = future.result()
                    with log_lock:
                        logger.info(f"Case {case_index}/{len(self.case_items)} 生成完成")
                    results.append(case_result)
                except Exception as e:
                    case_name = list(case_item.keys())[0] if case_item else "unknown"
                    with log_lock:
                        logger.error(f"处理case {case_name} (索引: {case_index}) 时出错: {e}")
                    # 创建部分结果记录错误
                    results.append({
                        "case_name": case_name,
                        "case_index": case_index,
                        "pre_code": f"# Error generating pre code: {str(e)}",
                        "case_code": f"# Error generating case code: {str(e)}"
                    })

        # 按原始顺序排序结果
        results.sort(key=lambda x: x.get("case_index", 0))
        return results

    def generator_case(self):
        """
        desc:
        使用langchain进行生成，生成case，完全基于JSON解析的内容
        :return: dict: 生成结果
        """
        try:
            logger.info(f"开始生成测试用例: APIs={self.all_apis}, business={self.business}, type={self.case_type}")

            # step1: 并发获取所有API的出入参数和业务逻辑
            api_data = self._get_api_data_concurrently()

            # step1.1: 并发使用模型总结API数据
            if self.is_need_module:
                api_data = self._summarize_api_data_concurrently(api_data)

            # step2: 获取业务对应的代码仓库，并获取link case和pre的demo
            repo_info = self._get_code_repo()
            # logger.info(f"获取到业务对应的代码仓库信息: {repo_info}")
            logger.info(f"获取到业务对应的代码仓库信息成功===")

            # 准备API信息，包含所有API
            api_info = {
                "all_apis": self.all_apis,
                "api_descriptions": self.api_descriptions,
                "business": self.business
            }

            # step3: 使用并发方式为每个case生成测试用例和前置操作
            case_results = self._process_case_concurrently(api_info, api_data, repo_info)

            # step4: 将生成的cases和pres保存到对应的文件夹中
            if self.is_need_save and case_results:
                file_result = self._save_cases_to_files(case_results)

                return file_result

            if not case_results:
                return [{
                    "status": "error",
                    "message": "没有生成任何测试用例"
                }]

            return []

        except Exception as e:
            logger.error(f"生成测试用例失败: {e}")
            return {
                "status": "error",
                "message": f"生成测试用例失败: {str(e)}"
            }


if __name__ == "__main__":
    # 使用JSON格式的输入
    input_data = {
        "Business": "xingye",
        "API": {
            "/weaver/api/v1/collection/card/get_all_direct_card": "- 直抽接口，抽卡并直接收下",
            "weaver/api/v1/collection/card/list/list_my_story_card_by_npc": "- 许愿池，我的卡牌",
            "/weaver/api/v1/collection/card/query_card_choice_history": "- 抽卡记录列表，我所有抽卡记录，按时间倒序排列"
        },
        "Case": [
            {
                "许愿池抽卡": {
                    "PRE": {
                        "每日免费": "def daily_free()， return uid，使用该uid，则享受每日免费权益",
                        "月卡免费次数": "def vip_free()， return uid，使用该uid，则享受月卡免费权益",
                        "星炉熔卡次数": "def reback_free()， return uid，使用该uid，则享受熔炉抽卡权益"
                    },
                    "TEST": "/weaver/api/v1/collection/card/get_all_direct_card -> weaver/api/v1/collection/card/list/list_my_story_card_by_npc"
                }
            },
            {
                "E卡增发": {
                    "PRE": {
                        "每日免费": "def daily_free()， return uid，使用该uid，则享受每日免费权益",
                        "月卡免费次数": "def vip_free()， return uid，使用该uid，则享受月卡免费权益",
                        "星炉熔卡次数": "def reback_free()， return uid，使用该uid，则享受熔炉抽卡权益"
                    },
                    "TEST": "/weaver/api/v1/collection/card/get_all_direct_card -> weaver/api/v1/collection/card/list/list_my_story_card_by_npc -> weaver/api/v1/collection/card/list/list_my_story_card_by_npc"
                }
            }
        ]
    }
    pwd = "/Users/xingyun/PycharmProjects/qa_tools/agent_mcp_link_case/agent_service/demo_file"

    generator_case = GeneratorCase(input_data, pwd)
    result = generator_case.generator_case()
    logger.info(f"生成结果: {result}")
