"""
coding:utf-8
@Software: PyCharm
@Time: 2024/8/21 上午11:25
@Author: xingyun
"""
import configparser
import json
import os
import subprocess
import sys
import pytz
import importlib.resources
import pkgutil

from datetime import datetime


class Utils:
    @staticmethod
    def get_env_info():
        if 'bedrock' in os.environ:
            print(os.environ['bedrock'])
            if 'env' in json.loads(os.environ['bedrock']):
                return json.loads(os.environ['bedrock'])['env'], json.loads(os.environ['bedrock'])['business']
        return Utils.get_conf("common", "env"), Utils.get_conf("common", "business")

    @staticmethod
    def get_conf(section, key):
        if os.environ.get(key, None):
            return os.environ[key]
        else:
            file = Utils.get_conf_abspath()
            config = configparser.ConfigParser()
            config.read(file)
            try:
                return config[section][key]
            except KeyError:
                raise KeyError(f"conf.ini, section:{section},key:{key} not fould, please check!")

    @staticmethod
    def set_conf(section, key, value):
        """
        设置或更新配置文件中的指定项。
        :param section: 配置文件中的 section 名称
        :param key: 配置项名称
        :param value: 配置值
        """
        file = Utils.get_conf_abspath()
        config = configparser.ConfigParser()

        # 读取现有配置文件（如果存在）
        if os.path.exists(file):
            config.read(file)

        # 如果 section 不存在，创建新的 section
        if not config.has_section(section):
            config.add_section(section)

        # 设置或更新 key 的值
        config.set(section, key, value)
        # 写回配置文件
        with open(file, "w") as configfile:
            config.write(configfile)

    @staticmethod
    def get_conf_abspath():
        # 首先尝试从包资源中读取配置
        try:
            # 检查配置是否作为包资源存在
            if pkgutil.find_loader("minimax_qa_mcp.conf"):
                conf_content = pkgutil.get_data("minimax_qa_mcp.conf", "conf.ini")
                if conf_content:
                    # 创建临时文件并写入配置内容
                    temp_dir = os.path.join(os.path.expanduser("~"), ".minimax_qa_mcp")
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_file = os.path.join(temp_dir, "conf.ini")
                    
                    # 如果文件不存在或需要更新，则写入内容
                    if not os.path.exists(temp_file):
                        with open(temp_file, "wb") as f:
                            f.write(conf_content)
                    
                    return temp_file
        except Exception as e:
            print(f"从包资源读取配置失败: {e}")
        
        # 如果从包资源读取失败，尝试通过路径查找
        runner_abspath_dirname = os.path.dirname(os.path.abspath(sys.argv[-1]))
        now_abspath_dirname = runner_abspath_dirname
        for i in range(10):
            for root, dirs, files in os.walk(now_abspath_dirname):
                if "conf" in dirs:
                    conf_path = os.path.join(now_abspath_dirname, "conf", "conf.ini")
                    if os.path.exists(conf_path):
                        return conf_path
            now_abspath_dirname = os.path.dirname(now_abspath_dirname)
        
        # 最后，尝试从当前工作目录查找
        local_conf = os.path.join(os.getcwd(), "conf", "conf.ini") 
        if os.path.exists(local_conf):
            return local_conf
            
        raise Exception("not found /conf/conf.ini")

    @staticmethod
    def get_link_conf_abspath():
        # 首先尝试从包资源中读取配置
        try:
            # 检查配置是否作为包资源存在
            if pkgutil.find_loader("minimax_qa_mcp.conf"):
                conf_content = pkgutil.get_data("minimax_qa_mcp.conf", "link_api.txt")
                if conf_content:
                    # 创建临时文件并写入配置内容
                    temp_dir = os.path.join(os.path.expanduser("~"), ".minimax_qa_mcp")
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_file = os.path.join(temp_dir, "link_api.txt")
                    
                    # 如果文件不存在或需要更新，则写入内容
                    if not os.path.exists(temp_file):
                        with open(temp_file, "wb") as f:
                            f.write(conf_content)
                    
                    return temp_file
        except Exception as e:
            print(f"从包资源读取配置失败: {e}")
        
        # 如果从包资源读取失败，尝试通过路径查找
        runner_abspath_dirname = os.path.dirname(os.path.abspath(sys.argv[-1]))
        now_abspath_dirname = runner_abspath_dirname
        for i in range(10):
            for root, dirs, files in os.walk(now_abspath_dirname):
                if "conf" in dirs:
                    link_path = os.path.join(now_abspath_dirname, "conf", "link_api.txt")
                    if os.path.exists(link_path):
                        return link_path
            now_abspath_dirname = os.path.dirname(now_abspath_dirname)
        
        # 最后，尝试从当前工作目录查找
        local_conf = os.path.join(os.getcwd(), "conf", "link_api.txt")
        if os.path.exists(local_conf):
            return local_conf
        
        return None

    @staticmethod
    def get_json_data(path):
        with open(path, 'r') as f:
            load_dict = json.load(f)
        return load_dict

    @staticmethod
    def write_json(json_data, json_path):
        with open(json_path, "w") as fp:
            fp.write(json.dumps(json_data, indent=4))

    @staticmethod
    def replace_bool_values(data):
        if isinstance(data, dict):
            return {k: Utils.replace_bool_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [Utils.replace_bool_values(item) for item in data]
        elif data is False:
            return False
        elif data is True:
            return True
        else:
            return data

    @staticmethod
    def get_report_path() -> str:
        if 'lib' in os.getcwd():
            root_path = os.path.dirname(os.path.abspath(os.getcwd()))
        # 命令行处理
        else:
            root_path = os.getcwd()
        report_path = root_path + '/allure/'

        return report_path

    @staticmethod
    def time_formatted() -> str:
        # 获取当前日期和时间
        current_date = datetime.now()
        # 获取上海时区
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        # 将当前日期和时间转换为上海时区
        shanghai_time = current_date.astimezone(shanghai_tz)
        # 格式化日期为 YYYYMMDD 格式
        formatted_date = shanghai_time.strftime('%Y%m%d')
        return formatted_date

    @staticmethod
    def time_formatted_shanghai() -> str:
        # 获取当前日期和时间
        current_date = datetime.now()
        # 获取上海时区
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        # 将当前日期和时间转换为上海时区
        shanghai_time = current_date.astimezone(shanghai_tz)
        # 格式化日期为 YYYYMMDD 格式
        formatted_date = shanghai_time.strftime('%Y%m%d%H%M%S')
        return formatted_date

    @staticmethod
    def run_cmd(cmd):
        """运行cmd 命令"""

        # 运行CMD命令并获取输出
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        # 打印命令的输出
        print("Output:", result.stdout)
        print("Error:", result.stderr)


if __name__ == '__main__':
    utils = Utils()
    req = {
        "cid": 180114436932074,
        "user_id": 160633434722592,
        "npc_id": 174392236024298,
        "mid": 180115467682152,
        "suggest_count": 0,
        "scene": 1,
        "use_safe_model": False,  # 这里是 False 而不是 false
        "user_msg_text": "（语气平静）多谢。",
        "base_req": {
            "AppID": 600,
            "os": 2,
            "sys_language": "zh",
            "ip_region": "cn",
            "channel": "xy_XIAOMI",
            "bus_data": {},
            "Extra": {
                "UserID": "160633434722592",
                "DeviceID": "160634651599227",
                "VersionCode": 1350003
            }
        }
    }

    # 调用函数进行替换
    req = utils.replace_bool_values(req)

    print(req)