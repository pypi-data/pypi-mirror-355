"""
coding:utf-8
@Software: PyCharm
@Time: 2025/4/27 18:19
@Author: xingyun
"""
import json
import logging
import requests
import os

from minimax_qa_mcp.utils.utils import Utils

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('知识库检索')

# ===== Weaviate参数配置 =====
os.environ["WEAVIATE_GRPC_ENABLED"] = "False"  # 禁用gRPC，使用HTTP协议
HTTP_HOST = Utils.get_conf("weaviate_url", "url")
HTTP_PORT = Utils.get_conf("weaviate_url", "port")
COLLECTION_NAME = "BusinessDocs_Auto"


class GetWeaviateInfo:
    """
    获取Weaviate信息的类
    """

    def __init__(self, input_question, is_need_module: bool = False):
        """
        初始化Weaviate信息获取器
        :param input_question: 用户输入
        :param is_need_module: 是否调用模型分析
        """
        self.input_question = input_question
        self.is_need_module = is_need_module
        # 模型API配置
        self.api_url = Utils.get_conf("generator_case_conf", "module_api_url")
        self.timeout = 120  # 设置超时时间

        # 懒加载Weaviate客户端
        self.client = None
        self._init_weaviate_client()

    def _init_weaviate_client(self):
        """
        初始化Weaviate客户端，延迟导入以避免循环导入问题
        使用Weaviate 3.x版本的API
        """
        try:
            # 在方法内部延迟导入weaviate的client模块，避免导入整个包
            from weaviate import client
            from urllib.parse import urlparse

            # 获取主机地址，确保不重复http://
            http_host_value = HTTP_HOST
            if http_host_value and (http_host_value.startswith('http://') or http_host_value.startswith('https://')):
                # 如果配置已经包含协议，则提取主机部分
                parsed_url = urlparse(http_host_value)
                http_host_value = parsed_url.netloc
                logger.info(f"从URL '{HTTP_HOST}'中提取主机部分: '{http_host_value}'")

            logger.info(f"尝试连接到Weaviate服务器: {http_host_value}:{HTTP_PORT}")

            # 使用Weaviate 3.x的客户端连接方式
            self.client = client.Client(f"http://{http_host_value}:{HTTP_PORT}")

            # 检查连接
            self.client.is_ready()
            logger.info("Weaviate客户端初始化成功")
        except Exception as e:
            logger.error(f"Weaviate客户端初始化失败: {e}")
            raise

    def get_info(self):
        """
        获取Weaviate信息
        :return: Weaviate信息字典
        """
        try:
            # 使用3.x版本的方式获取元数据
            meta = self.client.get_meta()

            info = {
                "version": meta.get("version", "未知"),
                "schema": self.client.schema.get(),
                "status": "已连接" if self.client.is_ready() else "未连接"
            }
            return info
        except Exception as e:
            logger.error(f"获取Weaviate信息失败: {e}")
            return {
                "version": "未知",
                "schema": {},
                "status": "错误",
                "error": str(e)
            }

    def search_documents(self, limit=5):
        """
        基于相似度的语义搜索
        
        Args:
            limit: 返回结果数量
            
        Returns:
            包含查询结果的字典列表
        """
        try:
            # 使用Weaviate 3.x版本的查询方式
            properties = [
                "title", "summary", "content", "category", "doc_id", "file_path", "doc_type",
                "submitter", "business_tags"  # 添加其他可能的属性字段，但不包含时间字段
            ]

            # 创建查询构建器
            query_builder = (
                self.client.query
                .get(COLLECTION_NAME, properties)
                .with_limit(limit)
                .with_near_text({"concepts": [self.input_question]})
                .with_additional(["certainty"])
            )

            # 执行查询
            results = query_builder.do()

            # 处理结果
            data = results.get("data", {}).get("Get", {}).get(COLLECTION_NAME, [])
            logger.info(f"搜索到 {len(data)} 个结果")

            processed_results = []
            for item in data:
                result = dict(item)

                # 添加相似度分数
                if "_additional" in item and "certainty" in item["_additional"]:
                    result["similarity"] = item["_additional"]["certainty"]
                    del result["_additional"]

                processed_results.append(result)

            return processed_results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def call_model(self, content_list):
        """调用模型API，添加了重试机制
        
        Args:
            content_list: 待总结的内容列表
            
        Returns:
            模型返回的结果
        """
        # 构建给模型的输入
        prompt = f"请对以下文档内容进行总结，提取关键信息：\n\n"
        for i, doc in enumerate(content_list):
            prompt += f"文档{i + 1}：{doc.get('title', 'N/A')}\n"
            prompt += f"内容：{doc.get('content', '')[:1000]}...\n\n"

        prompt += "请提供一个简洁的总结，包含这些文档的核心要点。"

        # 使用更简单的字符串替换处理
        clean_params = prompt.replace('\\"', "'")  # 替换嵌套双引号为单引号
        clean_params = clean_params.replace("\n", " ").strip()

        payload = {
            "scene": "qa_agent",
            "params": {
                "user_content": clean_params
            }
        }

        # 使用线程锁保护日志
        logger.info(f"==== 发送请求调用模型 ======")

        try:
            # 添加timeout参数，增加请求超时控制
            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                verify=False,
                timeout=self.timeout
            )

            logger.info(f"API响应状态码: {response.status_code}")
            logger.info(f"API响应内容: {response.text}")

            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"API请求失败，状态码: {response.status_code}")
                return None

            # 尝试解析JSON响应
            try:
                resp_json = response.json()

                if 'response' in resp_json:
                    # 解析二层JSON
                    try:
                        model_response = json.loads(resp_json['response'])

                        # 从content中提取文本
                        if 'content' in model_response and isinstance(model_response['content'], list):
                            text_content = ""
                            for item in model_response['content']:
                                if item.get('type') == 'text':
                                    text_content += item.get('text', '')
                            return text_content
                        return str(model_response)
                    except Exception as e:
                        logger.error(f"解析二层JSON失败: {e}")
                        return resp_json['response']
                return response.text
            except Exception as e:
                logger.error(f"解析JSON失败: {e}")
                return response.text

        except requests.RequestException as e:
            logger.error(f"请求异常: {e}")
            return None

    def get_knowledge(self, limit=5):
        """
        获取知识库信息
        
        Args:
            limit: 检索结果数量限制
            
        Returns:
            检索结果或模型总结的JSON
        """
        # 首先检索文档
        search_results = self.search_documents(limit=limit)

        # 构建基本返回结果
        result = {
            "query": self.input_question,
            "result_count": len(search_results),
            "results": search_results
        }

        # 根据is_need_module决定是否调用模型总结
        if self.is_need_module and search_results:
            try:
                summary = self.call_model(search_results)
                if summary:
                    result["model_summary"] = summary
            except Exception as e:
                logger.error(f"调用模型总结失败: {e}")
                result["model_summary_error"] = str(e)

        return result

    def __del__(self):
        """析构函数，确保在对象销毁时关闭连接"""
        if hasattr(self, 'client') and self.client is not None:
            try:
                # 在3.x版本中可能没有显式的close方法
                pass
            except:
                pass


if __name__ == "__main__":
    print("开始测试GetWeaviateInfo...")

    try:
        # 确保连接成功
        print("实例化GetWeaviateInfo...")
        get_weaviate_info = GetWeaviateInfo("海螺视频 图生视频 测试case", is_need_module=True)
        print("已成功实例化GetWeaviateInfo")

        # 测试获取基本信息
        print("测试获取Weaviate基本信息...")
        basic_info = get_weaviate_info.get_info()
        print(f"Weaviate版本: {basic_info.get('version')}")
        print(f"Weaviate状态: {basic_info.get('status')}")

        # 测试知识库搜索
        print("\n测试知识库搜索...")
        search_results = get_weaviate_info.get_knowledge(limit=3)
        print(f"查询: {search_results.get('query')}")
        print(f"结果数量: {search_results.get('result_count')}")

        # 打印每个结果的标题和相似度分数
        for i, result in enumerate(search_results.get('results', [])):
            print(f"结果 {i + 1}: {result.get('title')} (相似度: {result.get('similarity', 0):.3f})")

        print("\n完整结果:")
        print(search_results)
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
