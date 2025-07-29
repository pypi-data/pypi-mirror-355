# 标准库导入
import asyncio
import sys
import os
import json

# 将项目根目录添加到Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# MCP相关导入
from mcp.server.fastmcp import FastMCP

# 本地模块导入
from minimax_qa_mcp.utils.logger import logger

from minimax_qa_mcp.src.generator_case.generator_case import GeneratorCase
from minimax_qa_mcp.src.get_weaviate_info.get_weaviate_info import GetWeaviateInfo
from minimax_qa_mcp.src.grafana.service import GetFromGrafana, GetApiFromGrafana
from minimax_qa_mcp.src.gateway_case.get_case import CaseGrafanaService
from minimax_qa_mcp.src.query_segments.query_segments import query_main, TYPE_API, TYPE_FUNC, TYPE_CODE, TYPE_ANY, \
    TYPE_FUNC_DETAIL
from minimax_qa_mcp.src.auto_case.case_write import PDFWeaviateInfo
from minimax_qa_mcp.src.get_full_api_call_chain.get_full_api_call_chain import GetFullApiCallChain

# Initialize FastMCP server
mcp = FastMCP("mcp")


@mcp.tool()
async def get_grafana_data(scene: str, psm: str = "", msg: list = [], from_time: str = None,
                           to_time: str = None) -> str:
    """ 获取业务的grafana日志

    Args:
        scene: 枚举值，可选为[xingye_prod、xingye_test、talkie_prod、talkie_test、hailuo_video_cn_pre、hailuo_video_cn_prod、hailuo_video_us_test、hailuo_video_us_prod]其中xingye为星野业务、talkie为talkie业务、hailuo_video为海螺视频业务分国内(cn)和海外(us)，prod代表线上环境，test/pre代表线下环境
        psm: 服务名称，可选
        msg: 筛选关键字，可以是多个值的list，需要按照文本(比如trace_id)筛选日志时使用
        from_time: 可选，但用户提到时间则必填，日志筛选时间区间-开始时间，时间是UTC+8标准格式，如：2025-03-17T15:22:42.885430+08:00
        to_time: 可选，但用户提到时间则必填，日志筛选时间区间-结束时间，时间是UTC+8标准格式，如：2025-03-17T15:22:42.885430+08:00
    """
    # First get the forecast grid endpoint
    resp = GetFromGrafana(scene, psm, from_time, to_time).post_grafana(msg)

    return resp


@mcp.tool()
async def get_top_methods(scene: str, psm: str = "") -> list:
    """ 获取服务存在调用的接口列表，以及接口基本说明

    Args:
        scene: 枚举值，选项列表为[xingye_rpc、talkie_rpc、xingye_http、talkie_http、hailuo_video_cn_http、hailuo_video_us_http]其中xingye为星野业务、talkie为talkie业务、hailuo_video为海螺视频业务分国内(cn)和海外(us)，默认http，用户显示要求时再拼接rpc
        psm: 服务名称，可选，在用户显示指定时传递
    """
    # First get the forecast grid endpoint
    resp = GetApiFromGrafana(scene, psm).get_need_method()

    return resp


@mcp.tool()
async def get_http_data(scene: str, psm: str = "", api_path: str = "", from_time: str = None,
                        to_time: str = None) -> str:
    """ 获取业务http接口流量日志，包含req、resp等信息，会存为csv文件，返回文件访问地址

    Args:
        scene: 枚举值，可选为[xingye_http_prod、talkie_http_prod、hailuo_video_cn_pre、hailuo_video_cn_prod、hailuo_video_us_test、hailuo_video_us_prod]其中xingye为星野业务、talkie为talkie业务、hailuo_video为海螺视频业务分国内(cn)和海外(us)，prod代表线上环境，test/pre代表线下环境
        psm: 需要查询的具体服务名称，可选参数
        api_path: 需要查询的接口路径，必填参数
        from_time: 日志筛选时间区间-开始时间，时间是UTC+8标准格式，如：2025-03-17T15:22:42.885430+08:00
        to_time: 日志筛选时间区间-结束时间，时间是UTC+8标准格式，如：2025-03-17T15:22:42.885430+08:00
    """

    # 调用并行处理方法
    results = CaseGrafanaService(scene, psm, from_time, to_time).process_qps_file(api_path)
    return {"file_path": results}


@mcp.tool()
async def query_code_segments(query: str, query_type: str = None, limit: int = 10, exact: bool = False,
                              advanced: bool = False,
                              depth: int = 1, direction: str = "both", output: str = None) -> dict:
    """ 查询代码片段，支持多种查询模式

    Args:
        query: 查询的内容，可以是API路径、函数名、包名、文件路径或其他代码内容
        query_type: 查询类型，可选值：API(接口定义), FUNC(函数调用关系), CODE(代码变动的影响), FUNC_DETAIL(函数详情), ANY(所有类型，默认)
            -- API：接口定义的说明
            -- FUNC：函数之间的调用关系
            -- CODE：代码变动带来的影响
            -- FUNC_DETAIL：函数的具体实现
            -- ANY：模糊匹配，所有可能的结果返回

        limit: 返回结果的最大数量，默认10条
        exact: 是否精确匹配，默认False表示模糊匹配
        advanced: 使用高级代码影响分析，仅在查询类型为CODE时有效
        depth: 调用链深度，默认为1层，仅在查询类型为FUNC时有效
        direction: 调用链方向，可选值：caller(调用者), callee(被调用者), both(双向)，仅在查询类型为FUNC时有效
        output: 输出文件路径，用于保存函数调用图谱，仅在查询类型为FUNC时有效

    返回值说明:
        - 当查询API时: 返回API的路径、入参、出参和实现逻辑
        - 当查询函数时: 返回函数的调用链关系，谁调用了此函数，此函数调用了谁
        - 当查询代码片段时: 返回代码影响的函数列表
        - 当模糊查询时: 返回按类型分组的查询结果
        - 当查询函数详情时(FUNC_DETAIL): 返回函数的详细实现代码、所在文件位置及调用关系
    """
    # 转换query_type参数
    if query_type:
        query_type = query_type.upper()
        # 确保query_type是有效值
        if query_type not in [TYPE_API, TYPE_FUNC, TYPE_CODE, TYPE_ANY, TYPE_FUNC_DETAIL]:
            query_type = None

    # 调用main函数处理查询
    result = query_main(
        input_content=query,
        input_type=query_type,
        limit=limit,
        exact=exact,
        depth=depth,
        direction=direction,
        advanced=advanced,
        output=output
    )

    return result


@mcp.tool()
async def gen_case(input_data: dict, pwd: str) -> list:
    """
    link_case 生成
    Args:
        input_data: JSON格式的输入数据，包含Business、API和Case信息
        pwd: 用户当前的目录地址
    Return:
        列表，模型返回的具体信息以及具体需要保存的路径地址，[{"pre_case_dir": "xxxxx", "pre_case_result", "case_dir": "xxx", "case_result": "xxx"}]
        pre_case_dir:前置case需要保存的地址，你需要创建这个文件并写入：pre_case_result的内容
        case_dir：真正case需要保存的地址，你需要创建这个文件并写入：case_result的内容
    """
    # 在线程池中执行阻塞操作
    import concurrent.futures
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        generator = GeneratorCase(input_data, pwd)
        logger.info(f"===== The input params is :{input_data}, pwd is :{pwd}")
        result = await loop.run_in_executor(pool, generator.generator_case)
    return result


@mcp.tool()
async def get_weaviate_info(input_data: str) -> dict:
    """
    检索知识库 获取业务相关信息
    Args:
        input_data: str，用户问题
    Return:
        业务信息
    """
    weaviate_client = GetWeaviateInfo(input_data)
    result = weaviate_client.get_knowledge()
    return result


@mcp.tool()
async def get_auto_case(file_path: str, ref_case_name: str, use_moxing: bool = True) -> dict:
    """
    根据给定的文件路径和参考case名称，自动生成case

    Args:
        file_path: 需要处理的文件路径
        ref_case_name: 参考的case名称
        use_moxing: 是否使用模型，开关默认开启    
    Returns:
        包含自动生成case的相关信息的字典
    """
    # 调用 PDFWeaviateInfo.get_pdf_and_weaviate_info 方法
    prd_case = PDFWeaviateInfo(file_path, ref_case_name, use_moxing=use_moxing)
    case_response = prd_case.get_pdf_and_weaviate_info()
    return case_response


@mcp.tool()
async def get_full_api_call_chain(api_path: str) -> dict:
    """
    获取API调用链
    Args:
        api_path: str，API路径(demo:/weaver/api/v1/ugc/get_npc_list_by_user_id)
    Return:
        API调用链信息
    """
    # 判断api_path是不是'/'开头 不是的话 拼接
    if not api_path.startswith('/'):
        api_path = '/' + api_path
    logger.info(f"===== The input params is :{api_path}")

    api_call_chain = GetFullApiCallChain(api_path)
    result = api_call_chain.get_full_call_chain()
    logger.info(f"===== The result of get_full_api_call_chain is :{result}")
    return result


def main():
    print("Starting Minimax QA MCP server")
    """Run the Minimax QA MCP server"""
    mcp.run()


def run_server():
    """命令行入口点函数，用于PyPI包安装后的命令行调用"""
    # 确保当前工作目录在sys.path中
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    # 输出启动信息
    print("Starting Minimax QA MCP server from CLI")

    # 调用主函数
    main()


if __name__ == "__main__":
    run_server()
