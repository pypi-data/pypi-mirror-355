from minimax_qa_mcp.utils.logger import logger
import os
import re
import pandas as pd
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from minimax_qa_mcp.src.grafana.service import GetFromGrafana
from concurrent.futures import as_completed
import requests

class CaseGrafanaService(GetFromGrafana):
    """
    继承自GetFromGrafana类，用于获取案例相关的grafana日志
    """
    def __init__(self, scene, psm="", from_time=None, to_time=None):
        """
        初始化CaseGrafanaService

        Args:
            scene: 枚举值，可选为[ ]
            psm: 服务名，可选
            from_time: 日志筛选时间区间-开始时间
            to_time: 日志筛选时间区间-结束时间
        """
            
        # 调用父类初始化方法
        self.scene = scene
        if scene in ['xingye_http_prod','talkie_http_prod']:
            self.psm = 'ingress'
        else:
            self.psm = psm
        self.from_time = from_time
        self.to_time = to_time
        super().__init__(scene=self.scene, psm=psm, from_time=from_time, to_time=to_time)

    def get_case_logs(self,msgs):
        """
        获取案例相关的日志
        
        Returns:
            处理后的案例日志信息
        """
        try:
            # 调用父类方法获取原始日志
            raw_logs = self.post_grafana(msgs)
            
            # 处理日志数据
            processed_logs = self.process_logs(raw_logs)
            
            return processed_logs
        except Exception as e:
            logger.error(f"获取日志时发生错误: {e},业务：{self.scene},服务：{self.psm}")
            return []

    def process_logs(self, logs):
        """
        处理原始日志数据，提取消息内容
        
        Args:
            logs: 原始日志数据列表
            
        Returns:
            处理后的日志消息列表或结构化日志数据
        """
        # 处理logs为空的情况
        if logs is None:
            logger.warning(f"接收到的日志为None,业务：{self.scene},服务：{self.psm}")
            return []
        try:
            # 提取消息内容
            messages = [item.get('msg', '') for item in logs if isinstance(item, dict) and item.get('msg')]
            
            # 如果没有提取到任何消息
            if not messages:
                logger.warning(f"接收到的日志为None,业务：{self.scene},服务：{self.psm}")
                return []
                
            return messages
        except Exception as e:
            logger.error(f"处理日志时发生错误: {e},业务：{self.scene},服务：{self.psm}")
            # 返回空列表作为兜底
            return []
    def extract_req_details(self, response, match_field):
        """
        从日志内容中提取请求的详细信息
        
        :param response: 日志内容字符串
        :param match_field: 匹配的字段，例如 "req: http://hailuoai.video" 或 "req: http://hailuoai.video/v3/api/multimodal/video/like"
        :return: 请求体字典
        """
        try:
            # 使用正则表达式匹配请求URL和请求体
            domain_path_match = re.search(r'(req: http?://[^/]+)(/.*)?', match_field)
            if not domain_path_match:
                logger.error(f"无法解析match_field: {match_field}")
                return {}
            
            domain_part = domain_path_match.group(1)
            path_part = domain_path_match.group(2) or ""
            
            # 构建用于匹配的模式，直接匹配到响应体部分
            pattern = rf'{re.escape(domain_part + path_part)}.*?:(.*?)$'
            
            match = re.search(pattern, response)
            
            if match:
                # 提取请求体部分
                body_str = match.group(1).strip()
                
                # 解析请求体
                try:
                    body_params = json.loads(body_str) if body_str else {}
                    return body_params
                except json.JSONDecodeError:
                    logger.error(f"无法解析请求体JSON字符串,请求信息: {match_field},对应的服务：{self.psm}")
                    return {}
            else:
                logger.error(f"未找到匹配的请求信息: {match_field}，对应的服务：{self.psm}，完整日志: {response[:100]}...")
                return {}
                
        except Exception as e:
            logger.error(f'提取请求详细信息失败，错误：{e}，match_field: {match_field}')
            return {}

    def extract_resp_details(self, response, match_field):
        """
        从日志内容中提取响应的详细信息
        
        :param response: 日志内容字符串
        :param match_field: 匹配的字段，例如 "resp: http://hailuoai.video" 或 "resp: http://hailuoai.video/v3/api/multimodal/video/like"
        :return: 元组 (trace_id, path, query_params, resp_body)，分别是跟踪ID、路径、查询参数和响应体
        """
        try:
            # 提取trace_id
            trace_id_match = re.search(r'INFO 1 1 (\w+)', response)
            trace_id = trace_id_match.group(1) if trace_id_match else ""
            
            # 使用正则表达式匹配响应URL和响应体
            # 提取域名部分和路径部分
            domain_path_match = re.search(r'(resp: http?://[^/]+)(/.*)?', response.split('?')[0])
            if not domain_path_match:
                logger.error(f"无法解析response: {response}")
                return trace_id, "", "", {}
            
            domain_part = domain_path_match.group(1)
            path_part = domain_path_match.group(2) or ""
            
            # 提取路径
            path = path_part.split('?')[0] if '?' in path_part else path_part
            if path != match_field[1] and path != '/' + match_field[1]: raise Exception(f"路径不匹配，期望：{match_field[1]}，实际：{path}")
            
            # 构建用于匹配的模式
            if path_part:
                # 如果response包含路径部分，精确匹配这个路径后面的查询参数和响应体
                pattern = rf'{re.escape(domain_part + path_part)}\?([^:]*):(.*)$'
            else:
                # 如果response只包含域名，匹配任何路径及其后面的查询参数和响应体
                pattern = rf'{re.escape(domain_part)}([^?]*\?[^:]*):(.*)$'
            
            match = re.search(pattern, response)
            
            if match:
                if path_part:
                    # 如果match_field包含路径，匹配的是查询参数和响应体
                    query_params = match.group(1).strip()
                    resp_body_str = match.group(2).strip()
                else:
                    # 如果match_field只有域名，匹配的是路径+查询参数和响应体
                    path_query = match.group(1).strip()
                    resp_body_str = match.group(2).strip()
                    
                    # 分离路径和查询参数
                    if '?' in path_query:
                        path, query_params = path_query.split('?', 1)
                    else:
                        path = path_query
                        query_params = ""
                
                # 过滤掉指定的字段
                filtered_params = []
                unwanted_fields = [
                    'yy_platform', 'device_type', 'brand', 'biz_id', 
                    'device_brand', 'os_version', 'channel', 
                    'version_name', 'device_id', 'sys_region', 
                    'lang', 'unix', 'server_version',"uuid","os_name","browser_name","browser_platform","screen_width","screen_height","device_memory","cpu_core_num","browser_language"
                ]
                
                if query_params:
                    param_pairs = query_params.split('&')
                    for pair in param_pairs:
                        key_value = pair.split('=', 1)
                        if len(key_value) > 0 and key_value[0] not in unwanted_fields:
                            filtered_params.append(pair)
                
                # 重新构建查询参数字符串
                filtered_query_params = '&'.join(filtered_params)
                
                # 解析响应体
                try:
                    resp_body = json.loads(resp_body_str) if resp_body_str else {}
                except json.JSONDecodeError:
                    logger.error(f"无法解析响应体JSON字符串,响应信息: {match_field},对应的服务：{self.psm}")
                    resp_body = {}
                
                return trace_id, path, filtered_query_params, resp_body
            else:
                logger.error(f"未找到匹配的响应信息: {match_field}，对应的服务：{self.psm}，完整日志: {response[:100]}...")
                return trace_id, "", "", {}
                
        except Exception as e:
            logger.error(f'提取响应详细信息失败，错误：{e}，match_field: {match_field}')
            return "", "", "", {}

    def process_logs_extract_resp_details(self, match_field=None):
        """
        获取日志并遍历调用extract_resp_details函数提取响应详情
        
        Args:
            match_field: 匹配的字段，默认为None时会使用self.msg的第一个元素
            
        Returns:
            处理后的响应详情列表，每个元素为(trace_id, path, query_params, resp_body)元组
        """
        try:
            if not match_field:
                logger.error("未提供匹配字段，无法提取响应详情")
                return []
                
            # 确保match_field以"resp: http"开头
            if not match_field[0].startswith("resp"):
                logger.error(f"匹配字段不包含'resp'，无法提取响应详情: {match_field}")
                return []
                
            # 获取日志
            logs = self.get_case_logs(match_field)
            
            if not logs:
                logger.warning(f"未获取到日志，无法提取响应详情，业务：{self.scene}，服务：{self.psm}")
                return []
            
            # 存储提取的响应详情
            resp_details = []
            
            # 遍历日志，提取响应详情
            for log in logs:
                try:
                    # 调用extract_resp_details函数提取响应详情
                    trace_id, path, query_params, resp_body = self.extract_resp_details(log, match_field)
                    
                    # 如果成功提取到查询参数或响应体，则添加到结果列表
                    if query_params or resp_body:
                        resp_details.append((trace_id, path, query_params, resp_body))
                except Exception as inner_e:
                    logger.error(f"处理单条日志时出错: {inner_e}")
                    continue
            
            # 去重（使用查询参数作为唯一键）
            unique_details = []
            seen = set()
            
            for detail in resp_details:
                key = detail[2]  # query_params
                if key not in seen:
                    seen.add(key)
                    unique_details.append(detail)
            
            logger.info(f"从 {len(logs)} 条日志中提取了 {len(resp_details)} 条响应详情，去重后剩余 {len(unique_details)} 条")
            return unique_details
            
        except Exception as e:
            logger.error(f"遍历日志提取响应详情时出错: {e}")
            return []

    def get_req_by_traceid(self, trace_id, api_path):
        """
        根据trace_id和API路径获取请求详情
        
        Args:
            trace_id: 跟踪ID
            api_path: API路径
            
        Returns:
            请求体字典
        """
        try:
            # 构建匹配字段
            if self.scene == "hailuo_video_cn_pre":
                match_field = f"req: http://hailuo-pre.xaminim.com{api_path}"
            elif self.scene == "hailuo_video_cn_prod":
                match_field = f"req: http://hailuoai.com{api_path}"
            elif self.scene == "hailuo_video_us_test":
                match_field = f"req: http://hailuoai-video-test.xaminim.com{api_path}"
            elif self.scene == "hailuo_video_us_prod":
                match_field = f"req: http://hailuoai.video{api_path}"
            else:
                # 保留原来的默认行为
                match_field = f"req: http://hailuoai.video{api_path}"
            

            # 获取日志
            logs = self.get_case_logs([match_field, trace_id])
            
            if not logs:
                logger.warning(f"未获取到日志，无法根据trace_id获取请求详情，业务：{self.scene}，服务：{self.psm}，trace_id：{trace_id}")
                return {}
            
            # 遍历日志，直接提取请求体
            for log in logs:
                try:
                    # 确认日志包含trace_id
                    if trace_id in log:
                        # 提取请求体部分
                        req_body_match = re.search(rf'{re.escape(match_field)}.*?:(.*?)$', log)
                        if req_body_match:
                            req_body_str = req_body_match.group(1).strip()
                            try:
                                # 直接解析请求体JSON
                                return json.loads(req_body_str) if req_body_str else {}
                            except json.JSONDecodeError:
                                logger.error(f"无法解析请求体JSON字符串，trace_id：{trace_id}")
                                return {}
                except Exception as inner_e:
                    logger.error(f"处理单条日志时出错: {inner_e}")
                    continue
            
            logger.warning(f"未找到包含trace_id为{trace_id}的请求详情，业务：{self.scene}，服务：{self.psm}")
            return {}
            
        except Exception as e:
            logger.error(f"根据trace_id获取请求详情时出错: {e}")
            return {}

    def process_logs_extract_req_details(self, match_field=None):
        """
        获取日志并遍历调用extract_req_details函数提取请求详情
        
        Args:
            match_field: 匹配的字段，默认为None时会使用self.msg的第一个元素
            
        Returns:
            处理后的请求详情列表，每个元素为请求体字典
        """
        try:
            # 获取日志
            logs = self.get_case_logs(match_field)
            
            if not logs:
                logger.warning(f"未获取到日志，无法提取请求详情，业务：{self.scene}，服务：{self.psm}")
                return []
            
            # 存储提取的请求详情
            req_details = []
            
            # 遍历日志，提取请求详情
            for log in logs:
                try:
                    # match_field为uri原文，做一层全匹配校验，确保值接口一致
                    uri = re.search(r'"uri":\s*"([^\"]+)"', log).group(1)
                    if match_field[0] != uri and f"\\{match_field[0]}" != uri:
                        break

                    request_body = re.search(r'\"request_body\":\s*\"({.*?})"', log).group(1)
                    args = re.search(r'"args":\s*"([^\"]+)"', log).group(1)
                    req_details.append((uri, args, request_body,{},"" ))

                except Exception as inner_e:
                    logger.error(f"处理单条日志时出错: {inner_e}")
                    continue
            
            logger.info(f"从 {len(logs)} 条日志中提取了 {len(req_details)} 条请求详情")
            return req_details
            
        except Exception as e:
            logger.error(f"遍历日志提取请求详情时出错: {e}")
            return []

    def process_api_path_with_service(self, api_path):
        """
        处理单个API路径的辅助方法
        
        Args:
            api_path: API路径

        Returns:
            元组 (api_path, results)，其中results是请求详情列表
        """
        complete_results = []
        try:
            # if self.scene == "hailuo_video_cn_pre":
            #     match_field = f"resp: http://hailuo-pre.xaminim.com/{api_path}"
            # elif self.scene == "hailuo_video_cn_prod":
            #     match_field = f"resp: http://hailuoai.com/{api_path}"
            # elif self.scene == "hailuo_video_us_test":
            #     match_field = f"resp: http://hailuoai-video-test.xaminim.com/{api_path}"
            # elif self.scene == "hailuo_video_us_prod":
            #     match_field = f"resp: http://hailuoai.video/{api_path}"
            # else:
            #     # 保留原来的默认行为或者添加错误处理
            #     match_field = f"resp: http://hailuoai.video/{api_path}"

            #TX业务目前只能获取req
            if self.scene in ["xingye_http_prod","talkie_http_prod"]:
                complete_results = self.process_logs_extract_req_details([api_path])
            #海螺业务目前可以获得所有req、resp
            else:
                # 获取响应详情
                resp_results = self.process_logs_extract_resp_details(["resp: http",api_path])
                with ThreadPoolExecutor(max_workers=10) as executor:
                    # 创建任务列表
                    future_to_data = {}
                    for trace_id, path, query_params, resp_body in resp_results:
                        future = executor.submit(
                            self.get_req_by_traceid,
                            trace_id=trace_id,
                            api_path=path
                        )
                        future_to_data[future] = (trace_id, path, query_params, resp_body)

                    # 收集所有完成的任务结果
                    for future in as_completed(future_to_data):
                        try:
                            req_body = future.result()
                            trace_id, path, query_params, resp_body = future_to_data[future]
                            complete_results.append((path, query_params, req_body, resp_body, trace_id))
                        except Exception as e:
                            logger.error(f"获取请求体时出错: {e}")

        except Exception as e:
            logger.error(f"处理API路径时出错: {e}, api_path: {api_path}")

        # 存入文件
        return complete_results
        # self.write_results_to_excel_pandas(complete_results, filename)

    def process_qps_file(self, api_path=""):
        """
        处理HTTP接口路径
        
        Args:
            from_time: 开始时间，可选
            to_time: 结束时间，可选
            
        Returns:
            字典，键为API路径，值为该路径的请求详情列表
        """
        try:
            if api_path is None or len(api_path) <=0:
                return {"write_result":False,"msg":"api_path is null"}
            logger.info(f"待处理path {api_path}")

            # 保存到文件
            current_dir = os.path.abspath(os.path.dirname(__file__))

            # 确保输出目录存在
            output_dir = current_dir
            os.makedirs(output_dir, exist_ok=True)

            # 处理API路径，替换斜杠为下划线，使其成为有效的文件名
            safe_api_path = api_path.replace('/', '_')
            
            # 创建完整的文件路径
            filename = os.path.join(output_dir, f"{self.scene}_{safe_api_path}.csv")

            complete_results = self.process_api_path_with_service(api_path)
            self.write_results_to_excel_pandas(complete_results, filename)

            # 上传文件到COS
            files = {
                'file': (os.path.basename(filename), open(filename, 'rb'), 'text/csv')
            }
            cos_path = f'/http_api_logs/{datetime.now().strftime("%Y%m%d")}/'
            data = {
                'cos_path': cos_path
            }
            res = requests.post(
                url="http://swing.xaminim.com/save/cos",
                data=data,
                files=files
            )
            if res.status_code == 200:
                return f"https://qa-tool-1315599187.cos.ap-shanghai.myqcloud.com/{cos_path}/{self.scene}_{safe_api_path}.csv"
            else:
                logger.error(f"上传文件到COS失败，错误信息: {res.text}")
                return ""

        except Exception as e:
            logger.error(f"处理API路径{api_path}时出错: {e}")
            return  ""
            
        
        
    def write_results_to_excel_pandas(self, results, filename):
        """
        使用pandas将结果写入Excel文件
        
        Args:
            results: 处理结果字典，键为API路径，值为该路径的请求详情列表
            filename: 存入文件名
        
        Returns:
            None
        """
        try:
            # 准备数据
            all_req_info = []
            
            for result in results:
                # 解包结果元组，确保获取正确的字段
                if len(result) >= 5:
                    path, query_params, req_body, resp_body, trace_id = result
                else:
                    continue

                # 判断HTTP方法
                method = "post" if req_body else "get"

                # 构建参数字符串
                params_str = f"{query_params}"

                # 添加到列表
                all_req_info.append({
                    "path": path,
                    "method_for": method,
                    "params": params_str,
                    "req": json.dumps(req_body) if req_body else "{}",
                    "resp": json.dumps(resp_body) if resp_body else "{}"
                })
            
            # 创建新数据的DataFrame
            new_df = pd.DataFrame(all_req_info)
            
            # 如果DataFrame为空，添加列名
            if new_df.empty:
                new_df = pd.DataFrame(columns=["path", "params", "req", "resp", "trace"])
            
            # 检查文件是否已存在
            if os.path.exists(filename):
                try:
                    # 读取现有文件
                    existing_df = pd.read_csv(filename)
                    
                    # 合并现有数据和新数据
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    
                    # 写入合并后的数据
                    combined_df.to_csv(filename, index=False)
                    logger.info(f"已将结果追加到现有文件 {filename}")
                except Exception as read_error:
                    logger.error(f"读取现有文件出错，将覆盖写入: {read_error}")
                    new_df.to_csv(filename, index=False)
                    logger.info(f"已将结果保存到 {filename}（覆盖模式）")
            else:
                # 文件不存在，直接写入
                new_df.to_csv(filename, index=False)
                logger.info(f"已将结果保存到新文件 {filename}")

        except Exception as e:
            logger.error(f"写入CSV文件时出错: {e}")


if __name__ == "__main__":
    to_time_str = '2025-03-25T19:57:57.567593+08:00'
    from_time_str = '2025-03-25T19:00:57.567593+08:00'

    print(CaseGrafanaService(scene="hailuo_video_us_prod", psm="moss-gateway",from_time=from_time_str, to_time=to_time_str).process_qps_file(api_path="v3/api/multimodal/video/detail"))
    # print(CaseGrafanaService(scene="xingye_http_prod", psm="",from_time=from_time_str, to_time=to_time_str).process_qps_file(api_path="/weaver/api/v1/relation/get_item_list"))

    # # 测试响应日志处理功能
    # print("测试3: 响应日志处理")
    # resp_service = CaseGrafanaService(
    #     scene="hailuo_video_us_prod",
    #     psm="moss-gateway",
    #     msg=["resp: http://hailuoai.video/v3/api/multimodal/video/like"],
    #     from_time=from_time_str,
    #     to_time=to_time_str
    # )
    #
    # # 测试场景3：响应日志解析
    # resp_log = '2025-03-19 17:26:59.474    INFO 1 1 475e33d2fb07fcbbfaaf4bf6d3e85bcf /app/common/log_middileware.go:24 {} : [100.127.128.118] resp: http://hailuoai.video/v3/api/multimodal/video/like?device_platform=web&app_id=3001&version_code=22202&biz_id=0&lang=en&uuid=1c90e957-0060-4a7c-8e74-23a0e23f010e&device_id=300764012298178569&os_name=Mac&browser_name=chrome&device_memory=8&cpu_core_num=8&browser_language=zh-CN&browser_platform=MacIntel&screen_width=1152&screen_height=2048&unix=1742376419000: {"data":{},"statusInfo":{"code":0,"httpCode":0,"message":"Success","serviceTime":1742376419,"requestID":"bd306209-dcde-4dbd-80bb-c7ae34c78cb4","debugInfo":"Success","serverAlert":0}}'
    # resp_result = resp_service.extract_resp_details(resp_log, "resp: http://hailuoai.video/v3/api/multimodal/video/like")
    # print(f"响应日志处理结果: {resp_result}\n")
    
    # 测试请求日志处理功能
    # print("测试4: 请求日志处理")
    # req_service = CaseGrafanaService(
    #     scene="hailuo_video_us_prod",
    #     psm="moss-gateway",
    #     msg=["req: http://hailuoai.video/v3/api/multimodal/video/like"],
    #     from_time=from_time_str,
    #     to_time=to_time_str
    # )
    #
    # # 测试场景4：请求日志解析
    # req_log = '2025-03-18 15:25:17.546    INFO 1 1 74bc348ca6bf4e8d4b447f4ee3fea4c6 /app/common/log_middileware.go:21 {} : [100.127.128.113] req: http://hailuoai.video/v3/api/multimodal/video/like?device_platform=web&app_id=3001&version_code=22202&biz_id=0&lang=en&uuid=cde11186-0f9b-4c0f-9809-9be1a1b98a01&device_id=357566914493747208&os_name=Android&browser_name=chrome&device_memory=2&cpu_core_num=4&browser_language=en-BD&browser_platform=Linux+armv7l&screen_width=360&screen_height=800&unix=1742282716000: {"id":"dsadasada"}'
    # req_result = req_service.extract_req_details(req_log, "req: http://hailuoai.video/v3/api/multimodal/video/like")
    # print(f"请求日志处理结果: {req_result}\n")
    #
    # # 测试跟踪ID获取请求体功能
    # print("测试5: 通过trace_id获取请求体")
    # req_body = resp_service.get_req_by_traceid("475e33d2fb07fcbbfaaf4bf6d3e85bcf", "/v3/api/multimodal/video/like")
    # print(f"通过trace_id获取的请求体: {req_body}\n")
    #
    # 测试完整流程
    print("测试6: 完整流程测试")

    # 打印结果
    print("\n所有测试完成!")