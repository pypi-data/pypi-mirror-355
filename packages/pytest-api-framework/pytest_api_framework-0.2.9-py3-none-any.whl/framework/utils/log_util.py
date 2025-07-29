import logging

# 创建一个logger

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)  # 设置日志级别为INFO，这样INFO及以上级别的日志都会被记录

# 创建一个handler，用于写入日志文件
handler = logging.FileHandler('info.log')  # 注意这里用的是'log.info'，如果你想让它以.log扩展名结尾，可以改为'log.log'
handler.setLevel(logging.INFO)

# 创建一个formatter，用于设置日志的格式
formatter = logging.Formatter('%(asctime)s:%(msecs)03d [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

# 将handler添加到logger中
logger.addHandler(handler)
