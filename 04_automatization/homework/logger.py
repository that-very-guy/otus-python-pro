import logging
import os

_log_path = 'logs'
_name = 'OTUServer'

if not os.path.exists(_log_path):
    os.mkdir(_log_path)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
fh = logging.FileHandler(f'{_log_path}/{_name}.log', encoding='utf-8')
formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)
