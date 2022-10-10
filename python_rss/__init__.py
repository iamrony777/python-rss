from json import load
from sys import stdout
from loguru import logger

try:
    from dotenv import load_dotenv

    load_dotenv(".env")
except ImportError:
    pass

# LOGGER_CONFIG = {
#     "handlers": [
#         {
#             "sink": stdout,
#             "format": "<level>{level:<6}</level>:  <cyan>{file}</cyan>.<blue>{function}</blue>:<cyan>{line}</cyan> - <level>{message}</level>",
#             "enqueue": True,
#             "colorize": True,
#             "level": 20,
#         }
#     ]
# }

# logger.configure(**LOGGER_CONFIG)
