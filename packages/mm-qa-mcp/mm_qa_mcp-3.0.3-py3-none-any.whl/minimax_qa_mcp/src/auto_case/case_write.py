import functools
import re
from minimax_qa_mcp.src.get_weaviate_info.get_weaviate_info import GetWeaviateInfo
from minimax_qa_mcp.src.auto_case.pdf_jiexi import read_pdf_text
import logging
import requests
import json
import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('生成日志case')


def retry(max_attempts=3, wait=2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"第{attempt}次请求异常：{e}")
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(wait)
            logger.error(f"请求失败，已重试{max_attempts}次。")
            return f"请求失败，已重试{max_attempts}次，最后异常：{last_exception}"

        return wrapper

    return decorator


class PDFWeaviateInfo(GetWeaviateInfo):
    def __init__(self, prd_path, input_question,use_moxing, is_need_module=False):
        super().__init__(input_question, is_need_module)
        self.prd_path = prd_path
        self.timeout = 120
        self.use_moxing = use_moxing

    def get_pdf_and_weaviate_info(self):
        # 解析PDF内容
        pdf_text = read_pdf_text(self.prd_path)
        # 获取Weaviate信息
        weaviate_info = self.get_knowledge()
        # 拼接结果
        result = {
            'pdf_text': pdf_text,
            'weaviate_info': weaviate_info
        }

        case_response = self.call_model(result)
        return case_response

    def call_model(self, prd_content, max_attempts=5, wait=6):
        """
            调用模型，给出参考case
        Args:
            prd_content: prd信息+参考case
            max_attempts: 最大重试次数
            wait: 重试等待时间（秒）

        Returns:
            content内容拼接后的字符串，或错误信息
        """
        prd_case = prd_content.get("pdf_text", "")
        prompt = f"需求内容：{prd_case}"
        cankao_case = prd_content.get("weaviate_info", {}).get("results", [])
        for i, content in enumerate(cankao_case):
            case_content = content.get('content', '').strip()
            case_content_clean = re.sub(r'\s+', ' ', case_content)
            prompt += f"参考用例{i + 1}、用例名称：{content.get('title', 'N/A')}、用例内容：{case_content_clean}\n\n"
            break

        prompt += " 帮我写一份测试用例，参考用例若与本次需求相关可借鉴其设计思路和细节，不相关则忽略，用例设计需覆盖功能、边界、异常、安全、兼容性、性能、数据一致性、UI等多个维度，每个测试用例需包含：用例名称、用例编号、前置条件、测试步骤、预期结果、测试环境，用例内容要具体、细致，测试步骤要可操作，预期结果要明确"
        # prompt += "帮我写一份测试用例，参考用例若与本次需求相关可借鉴其设计思路和细节，不相关则忽略"
        clean_params = prompt.replace('\\"', "'")
        prd_prompt = clean_params.replace("\n", " ").strip()

        if not self.use_moxing:
            return prd_prompt

        payload = {
            "scene": "qa_agent",
            "params": {
                "user_content": prd_prompt
            }
        }

        logger.info(f"==== 发送请求调用模型 ======")
        # print(payload)
        last_exception = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    verify=False,
                    timeout=self.timeout
                )

                # logger.info(f"API响应状态码: {response.status_code}")
                # logger.info(f"API响应内容: {response.text}")

                if response.status_code != 200:
                    logger.error(f"API请求失败，状态码: {response.status_code}")
                    raise Exception(f"API请求失败，状态码: {response.status_code}")

                try:
                    resp_json = response.json()
                    if 'response' in resp_json:
                        try:
                            model_response = json.loads(resp_json['response'])
                            if 'choices' in model_response and isinstance(model_response['choices'], list):
                                # 兼容OpenAI/Claude等大模型返回结构
                                for choice in model_response['choices']:
                                    message = choice.get('message', {})
                                    content = message.get('content')
                                    if content:
                                        content += "\n- 需求内容" + f"{prd_case}"
                                        return content
                                # 如果没找到content，兜底返回整个choices
                                return str(model_response['choices'])
                            elif 'content' in model_response and isinstance(model_response['content'], list):
                                # 兼容content直接在顶层的情况
                                text_content = ""
                                for item in model_response['content']:
                                    if item.get('type') == 'text':
                                        text_content += item.get('text', '')
                                text_content += "\n- 需求内容" + f"{prd_case}"
                                return text_content
                            else:
                                return str(model_response)
                        except json.JSONDecodeError as json_e:
                            logger.error(f"解析二层JSON失败: {json_e}")
                            # 抛出异常，触发重试机制
                            raise Exception(f"解析二层JSON失败: {json_e}")
                        except Exception as e:
                            logger.error(f"处理二层JSON时发生未知错误: {e}")
                            # 抛出异常，触发重试机制  
                            raise Exception(f"处理二层JSON时发生未知错误: {e}")
                    
                    # 如果没有response字段，直接返回原始响应
                    return response.text
                    
                except json.JSONDecodeError as json_e:
                    logger.error(f"解析一层JSON失败: {json_e}")
                    # 抛出异常，触发重试机制
                    raise Exception(f"解析一层JSON失败: {json_e}")
                except Exception as e:
                    logger.error(f"处理响应时发生未知错误: {e}")
                    # 抛出异常，触发重试机制
                    raise Exception(f"处理响应时发生未知错误: {e}")
                    
            except requests.RequestException as e:
                logger.warning(f"第{attempt}次网络请求异常：{e}")
                last_exception = e
                if attempt < max_attempts:
                    time.sleep(wait)
                    continue
                else:
                    break
            except Exception as e:
                logger.warning(f"第{attempt}次请求处理异常：{e}")
                last_exception = e
                if attempt < max_attempts:
                    time.sleep(wait)
                    continue
                else:
                    break
                    
        logger.error(f"请求失败，已重试{max_attempts}次。最后异常：{last_exception}")
        return f"请求失败，已重试{max_attempts}次，最后异常：{last_exception}"


if __name__ == '__main__':
    a = PDFWeaviateInfo(prd_path="支持搜索用户功能.pdf", input_question="星野支持搜索用户功能的相关用例")
    print(a.get_pdf_and_weaviate_info())
    # read_pdf_text(prd_path = "注销流程优化.pdf")