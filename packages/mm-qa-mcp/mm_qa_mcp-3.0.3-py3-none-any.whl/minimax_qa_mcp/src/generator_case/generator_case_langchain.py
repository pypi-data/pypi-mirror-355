"""
coding:utf-8
@Software: PyCharm
@Time: 2025/4/11 14:03
@Author: xingyun
@Desc: 使用LangChain框架实现的case自动生成工具
"""
import os
import json
import re
import requests
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Dict
from datetime import datetime, timedelta, timezone

from langchain.tools import tool
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.runnables import Runnable
from langchain.schema.runnable import RunnableMap, RunnableLambda

# 确保导入项目相关模块
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

from minimax_qa_mcp.src.grafana.service import GetFromGrafana
from minimax_qa_mcp.src.query_segments.query_segments import query_main as query_segments_main
from minimax_qa_mcp.utils.utils import Utils
from minimax_qa_mcp.utils.logger import logger


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

    def call_model(self, params):
        """调用模型API
        
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

        # 打印发送到API的请求内容
        logger.info(f"发送请求到API，payload: {json.dumps(payload, ensure_ascii=False)}")

        # 添加verify=False参数，禁用SSL证书验证
        response = requests.post(self.api_url, json=payload, headers={'Content-Type': 'application/json'}, verify=False)

        logger.info(f"API响应状态码: {response.status_code}")

        # 打印API响应的完整内容
        logger.info(f"API响应内容: {response.text}")

        if response.status_code == 200:
            # 尝试解析JSON响应
            try:
                resp_json = response.json()
                logger.info(f"解析后的JSON: {json.dumps(resp_json, ensure_ascii=False)}")

                if 'response' in resp_json:
                    # 解析二层JSON
                    try:
                        model_response = json.loads(resp_json['response'])
                        logger.info(f"解析二层JSON: {json.dumps(model_response, ensure_ascii=False)}")

                        # 从content中提取文本
                        if 'content' in model_response and isinstance(model_response['content'], list):
                            text_content = ""
                            for item in model_response['content']:
                                if item.get('type') == 'text':
                                    text_content += item.get('text', '')
                            logger.info(f"提取的文本内容: {text_content}")
                            return text_content
                        return str(model_response)
                    except Exception as e:
                        logger.error(f"解析二层JSON失败: {e}")
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


class LinkCaseTools:
    """提供链路测试用例生成所需的工具函数集合"""
    
    def __init__(self, business: str, is_need_save: bool = False):
        """初始化工具类
        
        Args:
            business: 业务名称，如xingye、hailuo等
            is_need_save: 是否需要保存生成的测试用例
        """
        self.business = business
        self.is_need_save = is_need_save
        self.workspace_dir = Path(os.getcwd())
        self.link_case_conf_path = Utils.get_link_conf_abspath()
        self.result_dir = self.workspace_dir / "case_results"
        self.result_dir.mkdir(exist_ok=True)
        self.repo_dir = self.workspace_dir / "git_repos" / business
        
        # 设置时间范围
        now = datetime.now(timezone(timedelta(hours=8)))
        self.to_time = now.isoformat()
        self.from_time = (now - timedelta(hours=3)).isoformat()
        
        # 设置场景映射
        self.scene_mapping = {
            "xingye": "xingye_prod",
            "hailuo": "hailuo_video_cn_prod",
            "kaiping": "talkie_prod"
        }
        self.scene = self.scene_mapping.get(business, "xingye_prod")
        logger.info(f"初始化LinkCaseTools: business={business}")
    
    @tool
    def read_link_api_relations(self, api_name: str) -> Dict:
        """读取本地的link_api.txt文件，获取指定API的依赖关系
        
        Args:
            api_name: API名称
            
        Returns:
            dict: API依赖关系，格式为 {"pre_api": [...], "post_api": [...]}
        """
        logger.info(f"正在读取API依赖关系: {api_name}")
        link_api_path = Path(self.link_case_conf_path)
        if not link_api_path.exists():
            logger.warning(f"link_api.txt文件不存在: {link_api_path}")
            return {"pre_api": [], "post_api": []}
        
        try:
            api_deps = {}
            with open(link_api_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    parts = line.split("|")
                    if len(parts) >= 3:
                        api_part = parts[0].strip()
                        api = api_part.replace("[api]", "").strip()
                        
                        pre_api_part = parts[1].strip()
                        pre_api_part = pre_api_part.replace("[pre_api]", "").strip()
                        pre_apis = [pre_api.strip() for pre_api in pre_api_part.split(",") if pre_api.strip()]
                        
                        post_api_part = parts[2].strip()
                        post_api_part = post_api_part.replace("[post_api]", "").strip()
                        post_apis = [post_api.strip() for post_api in post_api_part.split(",") if post_api.strip()]
                        
                        api_deps[api] = {"pre_api": pre_apis, "post_api": post_apis}
            
            # 返回指定API的依赖关系或空字典
            api_relation = api_deps.get(api_name, {"pre_api": [], "post_api": []})
            logger.info(f"获取到API '{api_name}' 的依赖关系: {api_relation}")
            return api_relation
        
        except Exception as e:
            logger.error(f"读取link_api.txt文件失败: {e}")
            return {"pre_api": [], "post_api": []}
    
    @tool
    def get_grafana_data(self, api_name: str) -> Dict:
        """从Grafana获取API的请求和响应数据
        
        Args:
            api_name: API名称
            
        Returns:
            dict: API的请求和响应数据
        """
        logger.info(f"从Grafana获取API数据: {api_name}, scene={self.scene}")
        try:
            grafana_client = GetFromGrafana(
                scene=self.scene,
                from_time=self.from_time,
                to_time=self.to_time
            )
            api_data = grafana_client.post_grafana(msgs=[api_name])
            return {"raw_data": api_data}
        except Exception as e:
            logger.error(f"从Grafana获取API数据失败: {e}")
            return {"raw_data": None}
    
    @tool
    def get_code_repo(self) -> Dict:
        """获取业务对应的代码仓库，并获取link case的demo
        
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
        
        # 处理代码仓库
        if self.repo_dir.exists():
            logger.info(f"删除已存在的仓库目录: {self.repo_dir}")
            shutil.rmtree(str(self.repo_dir))
        
        self.repo_dir.parent.mkdir(exist_ok=True)
        self.repo_dir.mkdir(exist_ok=True)
        
        demo_cases = {}
        pre_demos = {}
        if not git_url:
            error_msg = f"未找到 {self.business} 的git仓库地址配置"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # 克隆仓库
            logger.info(f"克隆代码仓库: {git_url} -> {self.repo_dir}")
            subprocess.run(
                ["git", "clone", git_url, str(self.repo_dir)],
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
            
            # 构建demo case的完整路径
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
            
            return {
                "repo_info": f"{self.business} repository at {git_url}, branch: {branch}",
                "demo_cases": demo_cases,
                "pre_demos": pre_demos
            }
        
        except Exception as e:
            # 如果发生异常，尝试清理已创建的目录
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
    
    @tool
    def query_code_segments(self, api_name: str) -> Dict:
        """调用query_code_segments，获取API相关的出入参数以及业务逻辑
        
        Args:
            api_name: API名称
            
        Returns:
            dict: API相关的代码段信息
        """
        # 确保API名称格式一致
        if not api_name.startswith('/'):
            api_name = f"/{api_name}"
        
        logger.info(f"获取API代码段: {api_name}")
        
        try:
            # 直接调用main函数
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
            
            return {"raw_segments": code_segments}
        
        except Exception as e:
            logger.error(f"获取API代码段失败: {e}")
            return {"raw_segments": None}
    
    @tool
    def save_case_to_file(self, case_code: str, api_name: str, case_type: str = "link") -> str:
        """将生成的case保存到本地
        
        Args:
            case_code: 生成的测试用例代码
            api_name: API名称
            case_type: 测试用例类型，默认为link
            
        Returns:
            str: 保存的文件路径
        """
        if not self.is_need_save:
            logger.info("不需要保存测试用例")
            return ""
        
        # 格式化输出的代码内容
        case_code = self._format_output_file(case_code)
        
        case_type_dir = self.result_dir / case_type
        case_type_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        file_name = f"test_{api_name.replace('.', '_').replace('/', '_')}_{self.business}.py"
        file_path = case_type_dir / file_name
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(case_code)
        
        logger.info(f"测试用例已保存到: {file_path}")
        return str(file_path)
        
    def _format_output_file(self, code: str) -> str:
        """格式化输出的文件内容，修复常见格式问题
        
        Args:
            code: 代码内容
            
        Returns:
            str: 修复后的代码
        """
        logger.info("开始格式化生成的代码文件")
        
        # 将字符串包含的原始转义序列解码为Python字符串
        try:
            code = bytes(code, 'utf-8').decode('unicode_escape')
        except Exception as e:
            logger.warning(f"转义字符解码失败，将使用备用方法: {e}")
            
            # 备用方法：逐个替换常见的转义序列
            # 修复开头的转义问题
            if code.startswith('\\n'):
                code = code[2:]
                
            # 修复引号的转义问题
            code = code.replace("\\'\\'\\'", "'''")  # 三引号
            code = code.replace("\\'", "'")  # 单引号
            code = code.replace('\\"', '"')  # 双引号
            
            # 修复换行符的转义问题
            code = code.replace("\\n", "\n")
            
            # 修复制表符的转义问题
            code = code.replace("\\t", "\t")
            
            # 修复反斜杠的转义问题
            code = code.replace("\\\\", "\\")
            
            # 修复其他常见转义字符
            for escape_char in ['\\r', '\\f', '\\v', '\\a', '\\b']:
                char_value = eval(f'"{escape_char}"')
                code = code.replace(escape_char, char_value)
        
        logger.info("完成格式化生成的代码文件")
        return code


# 设置提示词模板，包含更多上下文信息
prompt_template = """
你是一个资深的Python测试用例工程师，请根据以下信息，为API {target_api} 生成一个场景化的链路测试用例：

## 业务基本信息
- 业务名称: {business}
- API名称: {target_api}

## API依赖关系
{api_relations}

## 前置API数据
{pre_api_data}

## 后置API数据
{post_api_data}

## 代码仓库信息
{repo_info}

## API代码分析
{code_segments}

## 参考的Demo Case格式
```python
{demo_case}
```

请按照上面的demo case格式，为API {target_api} 生成一个完整的Python测试用例。
请确保生成的测试用例结构、导入方式、类和方法定义、测试步骤等都与demo case保持一致，只修改具体的测试内容和API调用。
保持相同的代码风格、错误处理方式和断言格式。

请遵循以下Python代码格式规范:
1. 使用四个空格进行缩进，不要使用制表符
2. 类定义后空两行，方法定义后空一行
3. 使用单引号表示字符串，除非字符串中包含单引号
4. 注释应该是完整的句子，并以句号结尾
5. 导入模块应该一行一个，并按照标准库、第三方库、本地库的顺序排列
6. 确保代码中没有过长的行（最好不超过100个字符）
7. 变量和方法使用小写字母和下划线命名法

如果demo case中有特定的导入、工具函数或基类，请在生成的代码中保留这些元素。
"""


class GeneratorCaseLangChain:
    """使用LangChain框架的测试用例生成器"""
    
    def __init__(self, input_data, is_need_save: bool = True, case_type: str = "link"):
        """初始化测试用例生成器
        
        Args:
            input_data: JSON格式的输入数据，包含Business、API和Case信息
            is_need_save: 是否需要保存生成的测试用例
            case_type: 测试用例类型
        """
        # 初始化基本属性
        self.is_need_save = is_need_save
        self.case_type = case_type
        self.workspace_dir = Path(os.getcwd())
        
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
        
        # 设置默认的时间范围为3小时
        now = datetime.now(timezone(timedelta(hours=8)))
        self.to_time = now.isoformat()
        self.from_time = (now - timedelta(hours=3)).isoformat()

        # 根据业务名称确定场景
        self.scene_mapping = {
            "xingye": "xingye_prod",
            "hailuo": "hailuo_video_cn_prod",
            "kaiping": "talkie_prod"
        }
        self.scene = self.scene_mapping.get(self.business, "xingye_prod")
        
        # 设置默认值
        self.is_need_module = True
        
        # 初始化工具类
        self.tools = LinkCaseTools(business=self.business, is_need_save=is_need_save)
        
        # 初始化模型
        self.model = CustomRunnable()
        
        # 创建提示词模板
        self.prompt = PromptTemplate(
            template=prompt_template,
            input_variables=[
                "target_api", 
                "business", 
                "api_relations", 
                "pre_api_data", 
                "post_api_data", 
                "repo_info", 
                "code_segments", 
                "demo_case"
            ]
        )
        
        # 创建测试用例生成链
        self.chain = LLMChain(llm=self.model, prompt=self.prompt)
        
        logger.info(f"初始化GeneratorCaseLangChain: api_name={self.api_name}, business={self.business}, case_type={case_type}")
    
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
    
    def _get_api_relations(self, api_name: str) -> Dict:
        """获取API依赖关系"""
        return self.tools.read_link_api_relations(api_name)
    
    def _process_pre_api_data(self, api_relations: Dict) -> Dict:
        """处理前置API数据"""
        pre_api_data = {}
        for pre_api in api_relations.get("pre_api", []):
            pre_api_data[pre_api] = {
                "grafana_info": self.tools.get_grafana_data(pre_api),
                "code_segments": self.tools.query_code_segments(pre_api)
            }
        return pre_api_data
    
    def _process_post_api_data(self, api_relations: Dict) -> Dict:
        """处理后置API数据"""
        post_api_data = {}
        for post_api in api_relations.get("post_api", []):
            post_api_data[post_api] = {
                "grafana_info": self.tools.get_grafana_data(post_api),
                "code_segments": self.tools.query_code_segments(post_api)
            }
        return post_api_data
    
    def _extract_demo_case(self, repo_info: Dict) -> str:
        """从仓库信息中提取demo case内容"""
        demo_cases = repo_info.get("demo_cases", {})
        if demo_cases:
            return list(demo_cases.values())[0]
        return ""
    
    def _extract_python_code(self, response: str) -> str:
        """从模型响应中提取Python代码块"""
        python_code_blocks = re.findall(r'```python\s*(.*?)\s*```', response, re.DOTALL)
        if python_code_blocks:
            return python_code_blocks[0]
        return response
    
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
   - 格式应参考demo case

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

# 测试用例文件(test_{case_name}.py):
```python
# 测试用例文件内容
```
"""

        # 直接使用模型生成
        raw_response = self.chain.run(
            target_api=self.api_name,
            business=self.business,
            api_relations="",
            pre_api_data="",
            post_api_data="",
            repo_info="",
            code_segments="",
            demo_case=template
        )
        logger.info(f"模型返回的响应: {raw_response}")

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
    
    def _save_cases_to_files(self, case_results):
        """将生成的cases和pres保存到本地
        
        Args:
            case_results: 包含case和pre代码的列表
            
        Returns:
            list: 保存的文件路径列表
        """
        # 创建案例根目录
        case_root_dir = self.result_dir / self.case_type / f"{self.api_name.replace('.', '_').replace('/', '_')}_{self.business}"
        case_root_dir.mkdir(exist_ok=True, parents=True)
        
        saved_paths = []
        
        for result in case_results:
            case_name = result.get("case_name", "unknown")
            case_index = result.get("case_index", 0)
            pre_code = result.get("pre_code", "")
            case_code = result.get("case_code", "")
            
            # 格式化输出的代码内容
            pre_code = self.tools._format_output_file(pre_code)
            case_code = self.tools._format_output_file(case_code)
            
            # 为每个case创建单独的目录
            case_dir = case_root_dir / f"{case_index:02d}_{case_name}"
            case_dir.mkdir(exist_ok=True)
            
            # 保存前置操作文件
            pre_file_path = case_dir / f"pre_{case_name}.py"
            with open(pre_file_path, "w", encoding="utf-8") as f:
                f.write(pre_code)
            logger.info(f"前置操作已保存到: {pre_file_path}")
            saved_paths.append(str(pre_file_path))
            
            # 保存测试用例文件
            case_file_path = case_dir / f"test_{case_name}.py"
            with open(case_file_path, "w", encoding="utf-8") as f:
                f.write(case_code)
            logger.info(f"测试用例已保存到: {case_file_path}")
            saved_paths.append(str(case_file_path))
        
        return saved_paths
    
    def generator_case(self) -> Dict:
        """生成测试用例，完全基于JSON解析的内容
        
        Returns:
            dict: 生成结果
        """
        try:
            logger.info(f"开始生成测试用例: APIs={self.all_apis}, business={self.business}, type={self.case_type}")

            # step1: 获取所有API的出入参数和业务逻辑
            api_data = {}
            # 平等处理所有API
            for api in self.all_apis:
                api_data[api] = {}
                grafana_data = self.tools.get_grafana_data(api)
                code_segments = self.tools.query_code_segments(api)
                api_data[api]["grafana_info"] = grafana_data
                api_data[api]["code_segments"] = code_segments
                logger.info(f"获取到API数据: {api}")

            # step2: 获取业务对应的代码仓库，并获取link case和pre的demo
            repo_info = self.tools.get_code_repo()
            logger.info(f"获取到业务对应的代码仓库信息: {repo_info}")

            # 准备API信息，包含所有API
            api_info = {
                "all_apis": self.all_apis,
                "api_descriptions": self.api_descriptions,
                "business": self.business
            }

            # step3: 为每个case生成测试用例和前置操作
            case_results = []
            try:
                for i, case_item in enumerate(self.case_items):
                    logger.info(f"处理第 {i+1}/{len(self.case_items)} 个case")
                    case_result = self._generate_case_with_model(
                        api_info,
                        api_data,
                        repo_info,
                        case_item,
                        i+1
                    )
                    case_results.append(case_result)
                    
            except Exception as e:
                logger.error(f"生成测试用例失败: {e}")
                # 继续处理已生成的结果

            # step4: 将生成的cases和pres保存到对应的文件夹中
            if self.is_need_save and case_results:
                saved_paths = self._save_cases_to_files(case_results)
                
                return {
                    "status": "success",
                    "message": "测试用例生成成功",
                    "saved_paths": saved_paths,
                    "case_results": case_results,
                    "api_name": self.api_name,
                    "business": self.business,
                    "pre_apis": self.pre_apis,
                    "cases": self.cases
                }
            
            if not case_results:
                return {
                    "status": "error",
                    "message": "没有生成任何测试用例"
                }

            return {
                "status": "success",
                "message": "测试用例生成成功",
                "case_results": case_results,
                "api_name": self.api_name,
                "business": self.business,
                "pre_apis": self.pre_apis,
                "cases": self.cases
            }
        
        except Exception as e:
            logger.error(f"生成测试用例失败: {e}")
            return {
                "status": "error",
                "message": f"生成测试用例失败: {str(e)}"
            }


# 运行示例
if __name__ == "__main__":
    # 使用JSON格式的输入
    test_input = {
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
                "普通卡池-免费抽卡": {
                    "PRE": {
                        "每日免费": "def daily_free()， return uid，使用该uid，则享受每日免费权益",
                        "月卡免费次数": "def vip_free()， return uid，使用该uid，则享受月卡免费权益",
                        "星炉熔卡次数": "def reback_free()， return uid，使用该uid，则享受熔炉抽卡权益"
                    },
                    "TEST": "/weaver/api/v1/collection/card/get_all_direct_card -> weaver/api/v1/collection/card/list/list_my_story_card_by_npc"
                }
            }
        ]
    }
    
    generator = GeneratorCaseLangChain(test_input)
    result = generator.generator_case()
    logger.info(f"生成结果: {result['status']}")
    
    if result["status"] == "success" and "saved_paths" in result:
        print("\n生成的测试用例文件路径:\n")
        for path in result["saved_paths"]:
            print(f"- {path}")
