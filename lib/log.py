import datetime
import os

from loguru import logger

# logger.add('../logs/MSLX-{time:YYYY-MM-DD}.log', encoding='utf-8',
#                    backtrace=True, diagnose=True)

# 获取log.py文件所在的目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 获取相邻目录的路径
parent_dir = os.path.dirname(current_dir)

# 设置日志文件的路径
log_file_latest = os.path.join(parent_dir, 'logs', 'latest.log')
log_file = os.path.join(parent_dir, 'logs', f'mslx-{datetime.datetime.now().strftime("%Y-%m-%d")}.log')

# 删除原先的日志
try:
    os.remove(log_file_latest)
except FileNotFoundError:
    pass

# 配置Loguru日志记录器
# logger.add(log_file, encoding='utf-8', backtrace=True, diagnose=True)
logger.add(log_file_latest, encoding='utf-8', backtrace=True, diagnose=True)
