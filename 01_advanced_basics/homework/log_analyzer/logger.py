import logging
import os

log_path = 'logs'

if not os.path.exists(log_path):
    os.mkdir(log_path)
logger = logging.getLogger('log_analyzer')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(f'{log_path}/log_analyzer.log', encoding='utf-8')
formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)
