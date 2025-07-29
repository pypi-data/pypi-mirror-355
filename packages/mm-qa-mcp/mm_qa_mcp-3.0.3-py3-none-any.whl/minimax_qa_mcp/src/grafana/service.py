import requests
from datetime import datetime, timedelta, timezone
from minimax_qa_mcp.utils.logger import logger
from minimax_qa_mcp.utils.utils import Utils


class GetFromGrafana:
    def __init__(self, scene, psm="", from_time=None, to_time=None):

        self.cluster = Utils.get_conf(f"{scene}_business_info", "grafana_cluster")
        self.name_space = Utils.get_conf(f"{scene}_business_info", "grafana_name_space")
        self.psm = psm.replace('.', '-')
        # 拉取一天前的日志
        self.url = Utils.get_conf('common', 'grafana_url')
        if to_time is None and from_time is None:
            to_formatted_time = datetime.now(timezone(timedelta(hours=8))).isoformat()
            # 获取一天前的时间
            # 格式化为 ISO 8601 格式的字符串，包含微秒和时区信息
            from_formatted_time = (datetime.now(timezone(timedelta(hours=8))) - timedelta(hours=23)).isoformat()
            self.to_time = str(to_formatted_time)
            self.from_time = str(from_formatted_time)
        else:
            self.to_time = to_time
            self.from_time = from_time

    def post_grafana(self, msgs: list):
        query = f"_namespace_:\"{self.name_space}\" "
        if self.psm:
            query += f"and app:\"{self.psm}\" "
        if len(msgs) > 0:
            for msg in msgs:
                query += f"and msg:\"{msg}\" "
        data = {
            "from": self.from_time,
            "to": self.to_time,
            "query": query,
            "limit": 20,
            "topic_name": f"_mlogs_{self.cluster}/{self.name_space}"
        }
        logger.info(f"grafana的入参为：{data}")
        try:
            grafana_resp = requests.post(self.url, json=data)
            if grafana_resp.status_code == 200:
                return grafana_resp.json()['data']['items']
        except Exception as e:
            logger.error(f'get grafana resp error, psm is:{self.psm}, method is: {msgs}, error is: {e}')
            return []


class GetApiFromGrafana:

    def __init__(self, scene, psm):
        self.psm = psm
        self.scene = scene
        self.url = Utils.get_conf('common', 'swing_url')
        logger.info(f"GetApiFromGrafana init psm:{psm},scene:{scene}")

    def get_method_list(self):
        try:
            res = requests.get(url=self.url + "/swing/api/fetch_api_by_psm?psm=" + str(self.psm.replace("-", ".")))
            if res.status_code == 200:
                return res.json()["data"]["apis"]
        except Exception as e:
            logger.error(f"get_method_list error: {e}")
            return [e]

    def get_top_qps(self):
        try:
            res = requests.get(url=self.url + "/swing/api/get_top_qps?scene=" + str(self.scene))
            if self.psm is None or len(self.psm) <= 0:
                res_data = res.json()["data"]
                return {key: value for psm in res_data for key, value in res_data[psm].items()}
            else:
                return res.json()["data"][str(self.psm)]
        except Exception as e:
            logger.error(f"get_top_qps error: {e}")
            return [e]

    def get_need_method(self):
        try:
            qps_method_list = self.get_top_qps()
            # 如果是明确增加某个psm的rpc方法，则关注psm idl，并返回接口定义
            if "rpc" in self.scene and self.psm is not None and len(self.psm) > 0:
                res_list = []
                psm_method_list = self.get_method_list()
                for method in psm_method_list:
                    if method["method"] in list(qps_method_list.keys()):
                        method["qps"] = qps_method_list[method["method"]]
                        res_list.append(method)
                return res_list
            else:
                return list([{"method": key, "qps": value} for key, value in qps_method_list.items()])

        except Exception as e:
            logger.error(f"get_top_qps error: {e}")
            return [e]


if __name__ == '__main__':
    scene = "hailuo_video_cn_pre"
    # from_time = "2024-05-15T00:00:00.000+08:00"
    # to_time = "2024-05-15T23:59:59.999+08:00"
    msgs = ["5208af62da70dbe9a308b3b98d696a29"]
    # print("test")
    print(GetFromGrafana(scene).post_grafana(msgs))
    # print(GetApiFromGrafana("hailuo_video_us_http","").get_need_method())
    # print(GetApiFromGrafana("xingye_prod", "weaver-account-account").get_need_method())
