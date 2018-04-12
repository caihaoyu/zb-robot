import logging
import sys
import os


logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)

# 指定logger输出格式
formatter = logging.Formatter('%(asctime)s - [%(levelname)-5s] : %(message)s')

# 控制台日志
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)  # 也可以直接给formatter赋值

# 文件日志
file_handler = logging.FileHandler(os.path.join(os.getcwd(), "log/robot.log"))
file_handler.setFormatter(formatter)  # 可以通过setFormatter指定输出格式

# 为logger添加的日志处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 输出不同级别的log
# logger.debug('this is debug info')
# logger.info('this is information')
# logger.warning('this is warning message')
# logger.error('this is error message')
# logger.fatal('this is fatal message, it is same as logger.critical')
# logger.critical('this is critical message')
