from llms.dashscope_wrapper import dashscope_llm
from llms.openai_wrapper import openai_llm
import re
from utils.general_utils import get_logger_level
from loguru import logger
from utils.pb_api import PbTalker
import os


project_dir = os.environ.get("PROJECT_DIR", "")
if project_dir:
    os.makedirs(project_dir, exist_ok=True)
logger_file = os.path.join(project_dir, 'lurker.log')
dsw_log = get_logger_level()
logger.add(
    logger_file,
    level=dsw_log,
    backtrace=True,
    diagnose=True,
    rotation="50 MB"
)

pb = PbTalker(logger)

# model = 'qwen1.5-32b-chat'
model = "deepseek-chat"
focus_data = pb.read(collection_name='tags', filter=f'activated=True')
focus_list = [item["name"] for item in focus_data if item["name"]]
focus_dict = {item["name"]: item["id"] for item in focus_data if item["name"]}

system_prompt = f'''请仔细阅读用户输入的新闻内容，并根据所提供的类型列表进行分析。类型列表如下：
{focus_list}

如果新闻中包含上述任何类型的信息，请使用以下格式标记信息的类型，并提供信息摘要：
"""<tag>类型名称</tag>信息摘要"""

如果新闻中包含多个主题内容，请逐一分析并按一条一行的格式输出。如果新闻不涉及任何类型的信息，则直接输出“无”。
如下是输出结果格式示例：
"""<tag>居民社区活动</tag>信息摘要
<tag>招聘消息</tag>信息摘要"""

请严格忠于新闻原文，不得提供原文中不包含的信息。'''

# pattern = re.compile(r'\"\"\"(.*?)\"\"\"', re.DOTALL)


def get_info(article_content: str) -> list[dict]:
    # logger.debug(f'receive new article_content:\n{article_content}')
    result = openai_llm([{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': article_content}], model=model, logger=logger)
    # for test only
    compared = dashscope_llm(
        [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': article_content}], model='qwen1.5-32b-chat',
        logger=logger)
    # results = pattern.findall(result)

    texts = result.split('<tag>')
    texts = [_.strip() for _ in texts if '</tag>' in _.strip()]
    if not texts:
        logger.info(f'can not find info, llm result:\n{result}')
        return []

    cache = []
    for text in texts:
        # qwen-72b-chat 特例
        # potential_insight = re.sub(r'编号[^：]*：', '', text)
        try:
            strings = text.split('</tag>')
            tag = strings[0]
            tag = tag.strip()
            if tag not in focus_list:
                logger.info(f'tag not in focus_list: {tag}, aborting')
                continue
            info = ''.join(strings[1:])
            info = info.strip()
        except Exception as e:
            logger.debug(f'parse error: {e}\ntry another solution')
            tag = ''
            info = ''
            for focus in focus_list:
                if focus in text:
                    tag = focus
                    info = text.replace(focus, '')
                    info.strip()
                    break
        if not info or not tag:
            logger.warning(f'parse failed-{text}')
            continue

        if len(info) < 10:
            logger.warning(f'info too short, possible invalid: {info}')
            continue

        if info.startswith('无相关信息') or info.startswith('该新闻未提及') or info.startswith('未提及'):
            logger.debug(f'no relevant info: {text}')
            continue

        while info.endswith('"'):
            # for test only
            print(info)
            info = info[:-1]
        # for test only
        print(info)

        # 拼接下来源信息
        sources = re.findall(r'内容：\((.*?) 文章\)', article_content)
        if sources and sources[0]:
            info = f"【{sources[0]} 公众号】 {info}"

        cache.append({'content': info, 'tag': focus_dict[tag]})

    return cache
