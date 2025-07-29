import logging
import os
from logging.handlers import RotatingFileHandler

# 创建日志目录（如果不存在）
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'agent_service.log')

# 配置日志格式
log_format = '[%(asctime)s]-[%(process)d]-[%(levelname)s]- %(message)s'
formatter = logging.Formatter(log_format)

# 创建logger
logger = logging.getLogger("agent_service")
logger.setLevel(logging.INFO)

# 清除已有的处理器，避免重复
if logger.handlers:
    logger.handlers.clear()

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 添加文件处理器（使用RotatingFileHandler支持日志轮转）
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 避免日志传播到根logger
logger.propagate = False