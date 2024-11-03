from urllib.parse import urlparse
import os
import re
import hashlib
import json
from loguru import logger
from aiofiles import open as aio_open
import asyncio
import base64


async def read_file_as_base64(file_location):
    async with aio_open(file_location, "rb") as f:
        file_content = await f.read()
        file_base64 = base64.b64encode(file_content).decode()
    return file_base64


def isURL(string):
    if string.startswith("www."):
        string = f"https://{string}"
    result = urlparse(string)
    return result.scheme != '' and result.netloc != ''


def is_file_exists(file_path):
    # 检查文件路径是否存在
    if os.path.exists(file_path):
        # 进一步检查是否是一个文件
        if os.path.isfile(file_path):
            return True
        else:
            return False
    else:
        return False


def extract_urls(text):
    # Regular expression to match http, https, and www URLs
    url_pattern = re.compile(r'((?:https?://|www\.)[-A-Za-z0-9+&@#/%?=~_|!:,.;]*[-A-Za-z0-9+&@#/%=~_|])')
    urls = re.findall(url_pattern, text)
    # urls = {quote(url.rstrip('/'), safe='/:?=&') for url in urls}
    cleaned_urls = set()
    for url in urls:
        if url.startswith("www."):
            url = f"https://{url}"
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            continue
        # remove hash fragment
        if not parsed_url.scheme:
            # just try https
            cleaned_urls.add(f"https://{parsed_url.netloc}{parsed_url.path}{parsed_url.params}{parsed_url.query}")
        else:
            cleaned_urls.add(
                f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}{parsed_url.params}{parsed_url.query}")
    return cleaned_urls


def isChinesePunctuation(char):
    # Define the Unicode encoding range for Chinese punctuation marks
    chinese_punctuations = set(range(0x3000, 0x303F)) | set(range(0xFF00, 0xFFEF))
    # Check if the character is within the above range
    return ord(char) in chinese_punctuations


def is_chinese(string):
    """
    :param string: {str} The string to be detected
    :return: {bool} Returns True if most are Chinese, False otherwise
    """
    pattern = re.compile(r'[^\u4e00-\u9fa5]')
    non_chinese_count = len(pattern.findall(string))
    # It is easy to misjudge strictly according to the number of bytes less than half.
    # English words account for a large number of bytes, and there are punctuation marks, etc
    return (non_chinese_count/len(string)) < 0.68


def extract_and_convert_dates(input_string):
    # 定义匹配不同日期格式的正则表达式
    if not isinstance(input_string, str):
        return None

    patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{4})/(\d{2})/(\d{2})',  # YYYY/MM/DD
        r'(\d{4})\.(\d{2})\.(\d{2})',  # YYYY.MM.DD
        r'(\d{4})\\(\d{2})\\(\d{2})',  # YYYY\MM\DD
        r'(\d{4})(\d{2})(\d{2})'  # YYYYMMDD
    ]

    matches = []
    for pattern in patterns:
        matches = re.findall(pattern, input_string)
        if matches:
            break
    if matches:
        return ''.join(matches[0])
    return None


def get_logger(logger_name: str, logger_file_path: str):
    level = 'DEBUG' if os.environ.get("VERBOSE", "").lower() in ["true", "1"] else 'INFO'
    logger_file = os.path.join(logger_file_path, f"{logger_name}.log")
    if not os.path.exists(logger_file_path):
        os.makedirs(logger_file_path)
    logger.add(logger_file, level=level, backtrace=True, diagnose=True, rotation="50 MB")
    return logger


async def aio_write_file(file_path, text):
    try:
        async with aio_open(file_path, 'w', encoding='utf-8') as file:
            await file.write(text)
        return file_path
    except Exception as e:
        print(f"Failed to write file {file_path}: {e}")
        return None


async def write_md_file(result: dict, file_path: str) -> list[str]:
    MAX_CHARS = 1000000  # 要与 Qanything （qanything_kernel/configs/model_config.py）里的值保持一致
    title = result.get('title', '')
    content = result.get('content', '')
    imgs = result.get('images', [])
    url = result.get('url', '')
    author = result.get('author', '')
    publish_time = result.get('publish_time', '')
    if not title or not content or not imgs or not url:
        return []
    if not os.path.exists(file_path):
        os.makedirs(file_path, exist_ok=True)
    elif not os.path.isdir(file_path):
        return []
    img_links = '\n'.join(imgs)
    if author or publish_time:
        title = f"//{author} {publish_time}// {title}"

    max_chars = MAX_CHARS - len(title) - len(img_links) - len(url) - 52
    to_write = []
    while len(content) > max_chars:
        to_write.append(f"# {title}\n\n{content[:max_chars]}\n\n## Images In the Article\n\n{img_links}\n\n## Origin URL\n\n{url}")
        content = content[max_chars:]
    if content:
        to_write.append(f"# {title}\n\n{content}\n\n## Images In the Article\n\n{img_links}\n\n## Origin URL\n\n{url}")
    tasks = []
    for i, texts in enumerate(to_write):
        file_name = f"{hashlib.sha256(title.encode('utf-8')).hexdigest()[-12:]}_{i}.md"
        file_result = os.path.join(file_path, file_name)
        # 将异步函数作为任务添加到任务列表中
        tasks.append(aio_write_file(file_result, texts))
    # 等待所有写操作完成
    results = await asyncio.gather(*tasks)
    return [result for result in results if result is not None]


def clean_query(query: str, addition: str = "") -> str:
    """清除 query 中的所有表情符号、两边的空字符和 addition（大小写匹配）"""
    if addition:
        query = (query.replace(addition, "").replace(addition.lower(), "").
                 replace(addition.upper(), "").replace(addition.capitalize(), "").strip())
    # 去除所有表情符号
    query = re.sub(r'\[[^]]{1,4}]', '', query)
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', query)


async def aio_save_config(config, config_file: str):
    # 检查 config 是否为 dict 或 list
    if not isinstance(config, (dict, list)):
        return
    # 检查 config_file 是否以 .json 结尾
    if not config_file.endswith('.json'):
        return
    config_str = json.dumps(config, ensure_ascii=False, indent=4)
    async with aio_open(config_file, 'w', encoding='utf-8') as f:
        await f.write(config_str)


async def aio_config_load(config_file: str):
    if not config_file.endswith('.json'):
        return None
    async with aio_open(config_file, 'r', encoding='utf-8') as f:
        content = await f.read()
        return json.loads(content)
