import subprocess as sp
from typing import Any


class AriaCtl:

    def __init__(self, aria_path: str = "", aria_cmdoptions=None, aria_name: str = "aria2c",
                 enable_log_file: str = "aria2c_log.txt", dry_run: bool = False, max_concurrent_downloads: int = 5,
                 split: int = 8, enable_check: Any = False, enable_http_proxy: bool = False, timeout: int = 60,
                 max_connection_per_server: int = 1, max_try_times: int = 10, retry_wait_sec: int = 2,
                 min_split_size: int = 1, ):
        if aria_cmdoptions is None:
            aria_cmdoptions = ['']
        self.aria_path = aria_path
        self.aria_name = aria_name
        self.aria_cmdoptions = aria_cmdoptions
        self.enable_check = enable_check
        self.aria2c = None
        self.included_options = [
            f"--log={enable_log_file}",
            f"--max-concurrent-downloads={max_concurrent_downloads}",
            f"--split={split}",
            f"--connect-timeout={timeout}",
            f"--dry_run={dry_run}",
            f"--max-connection-per-server={max_connection_per_server}",
            f"--max-tries={max_try_times}",
            f"--min-split-siz={min_split_size}",
            f"--retry-wait={retry_wait_sec}",
            f"--timeout={timeout}",
        ]
        '''
        PROXY Dictionary EXAMPLE
        {
            "host":"127.0.0.1",
            "port":"7890",
            "user":"",
            "passwd":"",
        }
        
        SUMCHECK Dictionary EXAMPLE
        {
            "method":"sha-1",
            "sum":""
        }
        '''
        if enable_http_proxy:
            if isinstance(enable_http_proxy, dict):
                user = enable_http_proxy["user"]
                passwd = enable_http_proxy["passwd"]
                host = enable_http_proxy["host"]
                port = enable_http_proxy["port"]
                proxy = f"--http-proxy={user}:{passwd}@{host}:{port}"
                self.included_options.append(proxy)
            else:
                raise Exception

        if enable_check:
            if isinstance(enable_check, dict):
                pass
            else:
                raise Exception

    def start(self, download_name: str, download_path: str, download_url: str, download_opti: list[str] = ''):
        if not download_opti:
            download_opti = self.aria_cmdoptions
        download_opti += self.included_options
        download_opti.append(f"--out={download_name}")
        download_opti.append(f"--dir={download_path}")
        download_opti.append(download_url)
        download_opti_str = ""
        for item in download_opti:
            download_opti_str += item
        self.aria2c = sp.run(self.aria_path + download_opti_str)

    def check(self):
        if isinstance(self.enable_check, dict):
            check_method = self.enable_check["method"]
            check_sum = self.enable_check["sum"]
            check_opti = f"--checksum={check_method}={check_sum}"
            self.aria2c = sp.run(self.aria_path + check_opti)
