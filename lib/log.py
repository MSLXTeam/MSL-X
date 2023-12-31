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
LOG_FILE_LATEST = os.path.join(parent_dir, 'logs', 'latest.log')
LOG_FILE = os.path.join(parent_dir, 'logs', f'mslx-{datetime.datetime.now().strftime("%Y-%m-%d")}.log')

# 删除原先的日志
if os.path.exists(LOG_FILE_LATEST):
    os.remove(LOG_FILE_LATEST)

# 配置Loguru日志记录器
# logger.add(LOG_FILE, encoding='utf-8', backtrace=True, diagnose=True)
logger.add(LOG_FILE_LATEST, encoding='utf-8', backtrace=True, diagnose=True)
