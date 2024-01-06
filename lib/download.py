# 用于发起网络请求
import signal

# 用于多线程操作
import multitasking
import requests
# 导入 retry 库以方便进行下载出错重试
from retry import retry

signal.signal(signal.SIGINT, multitasking.killall)
# 导入math库方便计算
import math

proxy = {'http': 'localhost:7890'}
# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 '
                  'Safari/537.36 QIHU 360SE'
}
# 定义 1 MB 多少为 B
MB = 1024 ** 2


def split(start: int, end: int, step: int) -> list[tuple[int, int]]:
    # 分多块
    parts = [(start, min(start + step, end))
             for start in range(0, end, step)]
    return parts


def get_file_size(url: str) -> int:
    """
    获取文件大小
    Parameters
    ----------
    - url : 文件直链
    - raise_error : 如果无法获取文件大小，是否引发错误
    ------
    文件大小（B为单位）
    如果不支持则会raise异常
    :param url:
    """
    try:
        request = requests.get(url, proxies=proxy)
        file_size_str = request.headers['Content-Length']
    except:
        raise ValueError("Unable to get file size from this URL")
    else:
        return math.ceil(round(int(file_size_str) / MB))


def download(
        down_url: str, down_name: str,
        *,
        retry_times: int = 3,
        each_size: int = MB
):
    """
    根据文件直链和文件名下载文件
    Parameters
    ----------
    - down_url : 文件直链
    - down_name : 文件名
    - retry_times: 可选的，每次连接失败重试次数
    - each_size: 分块大小
    ------
    """
    f = open(down_name, 'wb')
    file_size = get_file_size(down_url)
    print(file_size)

    @retry(tries=retry_times)
    @multitasking.task
    def start_download(start: int, end: int) -> None:
        """
        根据文件起止位置下载文件
        Parameters
        ----------
        start : 开始位置
        end : 结束位置
        """
        _headers = headers.copy()
        # 分段下载的核心
        _headers['Range'] = f'bytes={start}-{end}'
        # 发起请求并获取响应（流式）
        response = session.get(down_url, headers=_headers, stream=True)
        # 每次读取的流式响应大小
        chunk_size = 128
        # 暂存已获取的响应，后续循环写入
        chunks = []
        for chunk in response.iter_content(chunk_size=chunk_size):
            # 暂存获取的响应
            chunks.append(chunk)
        f.seek(start)
        for chunk in chunks:
            f.write(chunk)
        # 释放已写入的资源
        del chunks

    session = requests.Session()
    # 分块文件如果比文件大，就取文件大小为分块大小
    each_size = min(each_size, file_size)
    # 分块
    print(file_size, each_size)
    parts = split(0, file_size, each_size)
    # 创建进度条
    for part in parts:
        start, end = part
        start_download(start, end)
    # 等待全部线程结束
    multitasking.wait_for_tasks()
    f.close()
