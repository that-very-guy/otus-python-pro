import os
import gzip
import re
import argparse
from statistics import mean, median
from string import Template
from datetime import datetime
from configparser import ConfigParser

from logger import logger


DEFAULT_CONFIG = {
        "REPORT_SIZE": 1000,
        "REPORT_DIR": "./reports",
        "LOG_DIR": "./log",
        "ERRORS_THRESHOLD": 0.2
    }


def get_last_logfile_info(log_dir: str) -> tuple:
    log_files = []
    for log_name in os.listdir(log_dir):
        ext = log_name.split('.')[-1]
        if ext == 'gz' or ext.startswith('log'):
            log_files.append(log_name)
    if log_files:
        last_log_path = f'{log_dir}/{sorted(log_files)[-1]}'
        date = datetime.strptime(re.findall(r'\d{8}', last_log_path)[0], '%Y%m%d')
        return last_log_path, date
    else:
        return None, None


def read_lines(log_path: str) -> str:
    log_reader = gzip.open if log_path.endswith(".gz") else open
    for line in log_reader(log_path, 'r'):
        yield line.decode()


def process_logfile(logfile_path: str, report_size: int, errors_threshold: float) -> list:
    # urls_info = defaultdict(lambda: defaultdict(int))
    urls_info = {}
    total_lines_counter = 0
    parsing_errors_counter = 0
    total_urls_time = 0
    regexp = re.compile(r'\"\w{3,4} (/.+?) ')
    for line in read_lines(logfile_path):
        total_lines_counter += 1
        url_section = regexp.findall(line)
        if url_section:
            url = url_section[0]
            request_time = float(line.split()[-1])
            total_urls_time += request_time
            urls_info[url] = {
                'count': urls_info.get(url, {}).get('count', 0) + 1,
                'time_sum': urls_info.get(url, {}).get('time_sum', 0) + request_time,
                'timings': urls_info.get(url, {}).get('timings', []) + [request_time],
            }
        else:
            parsing_errors_counter += 1
    parsing_errors_ratio = round(parsing_errors_counter / total_lines_counter, 2)
    if parsing_errors_ratio > errors_threshold:
        raise SystemError(
            f'Too many errors [{parsing_errors_ratio * 100} %] occurred during parsing logfile {logfile_path}'
        )
    for url, info in urls_info.items():
        urls_info[url]['url'] = url
        urls_info[url]['count_perc'] = round(urls_info[url]['count'] / total_lines_counter * 100)
        urls_info[url]['time_perc'] = round(urls_info[url]['time_sum'] / total_urls_time * 100)
        urls_info[url]['time_sum'] = round(urls_info[url]['time_sum'], 3)
        urls_info[url]['time_max'] = max(urls_info[url]['timings'])
        urls_info[url]['time_avg'] = round(mean(urls_info[url]['timings']), 3)
        urls_info[url]['time_med'] = round(median(urls_info[url]['timings']), 3)
        del urls_info[url]['timings']
    urls_table_data = []
    for v in sorted(urls_info.values(), key=lambda item: item['time_sum'], reverse=True):
        if len(urls_table_data) == report_size:
            break
        urls_table_data.append(v)
    return urls_table_data


def save_report(stats: list, reports_dir: str, date: datetime):
    with open('report.html', encoding='utf-8') as template_file:
        template = Template(template_file.read())
        output_str = template.safe_substitute(table_json=stats)
        with open(f'{reports_dir}/report-{date.strftime("%Y.%m.%d")}.html', 'w', encoding='utf-8') as report_file:
            report_file.write(output_str)


def get_config(default_config: dict) -> dict:
    parser = argparse.ArgumentParser('LogParser')
    parser.add_argument('--config')
    args = parser.parse_args()
    config_path = args.config
    if config_path:
        if os.path.exists(config_path):
            config = ConfigParser()
            config.read(config_path)
            if config.has_option('DEFAULT', 'REPORT_SIZE'):
                default_config['REPORT_SIZE'] = config.getint('DEFAULT', 'REPORT_SIZE')
            for option in ['REPORT_DIR', 'LOG_DIR']:
                if config.has_option('DEFAULT', option):
                    default_config[option] = config.get('DEFAULT', option)
        else:
            raise FileNotFoundError
    return default_config


def main():
    try:
        config = get_config(DEFAULT_CONFIG)
        if not os.path.exists(config['REPORT_DIR']):
            os.mkdir(config['REPORT_DIR'])
        logfile_path, date = get_last_logfile_info(config['LOG_DIR'])
        if not logfile_path:
            logger.info('No logs was found to process.')
            return
        logger.info(f'Processing [{logfile_path}] file.')
        if os.path.exists(f'{config["REPORT_DIR"]}/report-{date.strftime("%Y.%m.%d")}.html'):
            logger.info(f'Report for [{logfile_path}] already exists.')
            return
        stats = process_logfile(logfile_path, config['REPORT_SIZE'], config['ERRORS_THRESHOLD'])
        save_report(stats, config['REPORT_DIR'], date)
        logger.info(f'Log {logfile_path} successfully processed.')

    except (SystemError, FileNotFoundError) as e:
        logger.error(e)
    except (KeyboardInterrupt, Exception) as e:
        logger.exception(e)


if __name__ == "__main__":
    main()
