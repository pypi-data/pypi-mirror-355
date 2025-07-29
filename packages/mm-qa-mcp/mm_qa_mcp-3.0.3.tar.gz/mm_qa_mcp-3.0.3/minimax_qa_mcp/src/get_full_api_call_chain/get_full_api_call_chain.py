"""
coding:utf-8
@Software: PyCharm
@Time: 2025/6/8 14:37
@Author: xingyun
@description:
 根据api_path 获取完整的API调用链
 输入：api_path
 输出：完整的API调用链（包括所有下游调用）
"""


from minimax_qa_mcp.utils.mysql_op import MysqlOp
from minimax_qa_mcp.utils.logger import logger

default_service = "weaver.gateway.weaver"


class GetFullApiCallChain:
    def __init__(self, api_path):
        """
        初始化调用链获取类
        :param api_path:  /path/to/endpoint (HTTP路径格式)
        """
        self.api_path = api_path
        self.mysql_op = MysqlOp()
        # API路径，获取服务名和方法名
        self.caller_service = default_service
        self.caller_method = api_path
        # 存储已访问的调用路径，避免循环调用
        self.visited_paths = set()
        # 存储最终的调用链结果
        self.call_chain_results = []

    def get_downstream_calls(self, service, method):
        """
        获取指定服务和方法的所有下游调用
        :param service: 服务名称
        :param method: 方法名称
        :return: 下游调用列表
        """
        sql = """
        SELECT caller_service, caller_method, callee_service, callee_method, call_type, code_chain 
        FROM qa_tools.code_call_chain 
        WHERE caller_service = %s AND caller_method = %s
        """

        result = self.mysql_op.connect(sql_=sql, data=(service, method), op='select')
        return result if result else []

    def _build_call_path(self, call_record, level=0, path=None):
        """
        递归构建调用路径
        :param call_record: 当前调用记录
        :param level: 当前调用层级
        :param path: 当前已构建的路径
        :return: 构建完成的调用路径
        """
        caller_service = call_record[0]
        caller_method = call_record[1]
        callee_service = call_record[2]
        callee_method = call_record[3]
        call_type = call_record[4]

        # 构建调用路径标识
        call_id = f"{caller_service}.{caller_method} -> {callee_service}.{callee_method}"

        # 检查是否已经访问过该路径，避免循环调用
        if call_id in self.visited_paths:
            return

        self.visited_paths.add(call_id)

        # 初始化路径
        if path is None:
            path = []

        # 添加当前调用到路径
        current_call = {
            "level": level,
            "caller_service": caller_service,
            "caller_method": caller_method,
            "callee_service": callee_service,
            "callee_method": callee_method,
            "call_type": call_type
        }

        path.append(current_call)

        # 复制当前路径，添加到结果中
        self.call_chain_results.append(path.copy())

        # 递归获取下游调用
        downstream_calls = self.get_downstream_calls(callee_service, callee_method)
        for downstream_call in downstream_calls:
            self._build_call_path(downstream_call, level + 1, path.copy())

    def get_full_call_chain(self):
        """
        获取完整的API调用链
        :return: 字典，包含原始API信息和完整调用链
        """
        # 先清空之前的结果
        self.visited_paths = set()
        self.call_chain_results = []

        # 获取起始API的下游调用
        downstream_calls = self.get_downstream_calls(self.caller_service, self.caller_method)

        if not downstream_calls:
            logger.info(f"未找到API {self.caller_service}.{self.caller_method} 的下游调用")
            return {
                "api_path": self.api_path,
                "service": self.caller_service,
                "method": self.caller_method,
                "downstream_calls_count": 0,
                "downstream_calls": [],
                "call_tree": {},
                "statistics": {
                    "total_calls": 0,
                    "max_depth": 0,
                    "service_count": 0,
                    "call_type_distribution": {}
                }
            }

        # 构建每个下游调用的完整路径
        for call in downstream_calls:
            self._build_call_path(call)

        # 构建树形结构
        call_tree = self._build_call_tree()

        # 计算统计信息
        statistics = self._calculate_statistics()

        # 格式化结果
        formatted_results = []
        for path in self.call_chain_results:
            formatted_path = {
                "path_length": len(path),
                "calls": []
            }
            for call in path:
                formatted_path["calls"].append({
                    "level": call["level"],
                    "caller": f"{call['caller_service']}.{call['caller_method']}",
                    "callee": f"{call['callee_service']}.{call['callee_method']}",
                    "call_type": call["call_type"],
                    "detail": f"{call['caller_service']}.{call['caller_method']} -> {call['callee_service']}.{call['callee_method']} ({call['call_type']})"
                })
            formatted_results.append(formatted_path)

        return {
            "api_path": self.api_path,
            "service": self.caller_service,
            "method": self.caller_method,
            "downstream_calls_count": len(self.call_chain_results),
            "downstream_calls": formatted_results,
            "call_tree": call_tree,
            "statistics": statistics
        }

    def _build_call_tree(self):
        """
        构建调用树形结构
        """
        tree = {}

        for path in self.call_chain_results:
            current_node = tree
            for call in path:
                key = f"{call['callee_service']}.{call['callee_method']}"
                if key not in current_node:
                    current_node[key] = {
                        "service": call['callee_service'],
                        "method": call['callee_method'],
                        "call_type": call['call_type'],
                        "caller": f"{call['caller_service']}.{call['caller_method']}",
                        "children": {}
                    }
                current_node = current_node[key]["children"]

        return tree

    def _calculate_statistics(self):
        """
        计算调用链的统计信息
        """
        # 统计各种信息
        service_set = set()
        call_type_count = {}
        max_depth = 0

        for path in self.call_chain_results:
            # 更新最大深度
            if len(path) > max_depth:
                max_depth = len(path)

            # 收集服务和调用类型
            for call in path:
                service_set.add(call['callee_service'])
                call_type = call['call_type']
                call_type_count[call_type] = call_type_count.get(call_type, 0) + 1

        # 统计每个服务被调用的次数
        service_call_count = {}
        for path in self.call_chain_results:
            for call in path:
                service_key = f"{call['callee_service']}.{call['callee_method']}"
                service_call_count[service_key] = service_call_count.get(service_key, 0) + 1

        # 找出被调用最多的服务
        top_called_services = sorted(service_call_count.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_calls": len(self.call_chain_results),
            "max_depth": max_depth,
            "service_count": len(service_set),
            "call_type_distribution": call_type_count,
            "top_called_services": top_called_services
        }

    def print_call_chain(self):
        """
        以可读性强的格式打印完整的调用链
        """
        result = self.get_full_call_chain()

        # 打印基本信息
        print(f"\n{'=' * 100}")
        print(f"📍 API调用链分析报告")
        print(f"{'=' * 100}")
        print(f"🔗 API路径: {result['api_path']}")
        print(f"🏢 服务名: {result['service']}")
        print(f"📋 方法名: {result['method']}")
        print(f"\n{'=' * 100}")

        # 打印统计信息
        stats = result['statistics']
        print(f"📊 统计信息:")
        print(f"  • 总调用链数: {stats['total_calls']}")
        print(f"  • 最大调用深度: {stats['max_depth']}")
        print(f"  • 涉及服务数量: {stats['service_count']}")
        print(f"  • 调用类型分布: {stats['call_type_distribution']}")

        if stats.get('top_called_services'):
            print(f"\n  • 🔥 高频调用服务 TOP5:")
            for service, count in stats['top_called_services']:
                print(f"    - {service} (被调用 {count} 次)")

        print(f"\n{'=' * 100}")

        if result.get('downstream_calls_count', 0) == 0:
            print("❌ 没有找到下游调用")
            print(f"{'=' * 100}\n")
            return result

        # 打印树形结构
        print("🌳 调用树形结构:")
        print(f"{'-' * 100}")
        self._print_tree(result['call_tree'], indent=0)

        return result

    def _print_tree(self, tree, indent=0, prefix=""):
        """
        递归打印树形结构
        """
        items = list(tree.items())
        for i, (key, node) in enumerate(items):
            is_last = i == len(items) - 1

            # 打印当前节点
            connector = "└── " if is_last else "├── "
            type_symbol = {"HTTP": "🌐", "RPC": "⚡", "LOCAL": "🏠"}.get(node['call_type'], "📡")
            print(f"{prefix}{connector}{type_symbol} {key}")

            # 打印子节点
            if node['children']:
                extension = "    " if is_last else "│   "
                self._print_tree(node['children'], indent + 1, prefix + extension)


if __name__ == '__main__':
    # 使用示例 - HTTP路径格式
    api_path_ = "/weaver/api/v1/ugc/get_npc_list_by_user_id"
    call_chain = GetFullApiCallChain(api_path_)
    result = call_chain.print_call_chain()
    print("结果:")
    print(result)
