# from llms.dashscope_wrapper import dashscope_llm
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

# model = 'qwen-72b-chat'
model = "deepseek-chat"
# focus_list = ["社区活动", "服务品牌", "社区共建共享经验", "癌症以及肿瘤", "招聘信息"]
focus_list = [tag['name'] for tag in pb.read(collection_name='tags', filter=f'activated=True') if tag['name']]

system_prompt = f'''请仔细阅读用户输入的新闻内容，并根据所提供的类型列表进行分析。类型列表如下：
{focus_list}

如果新闻中包含上述任何类型的信息，请使用以下格式标记信息的类型，并提供简洁的信息摘要：
"""<tag>类型名称</tag>信息摘要"""

如果新闻中包含多个主题内容，请逐一分析并按一条一行的格式输出。如果新闻不涉及任何类型的信息，则直接输出“无”。

最终结果请整体用三引号包裹输出，如下所示：
"""<tag>居民社区活动</tag>信息内容
<tag>招聘消息</tag>信息内容"""

请严格遵守以下规则：
忠于新闻原文，不得提供原文中不包含的信息。
不得加入自己的分析和猜想。
确保输出的信息摘要简洁明了，不包含无关内容。'''

pattern = re.compile(r'\"\"\"(.*?)\"\"\"', re.DOTALL)


def get_info(article_content: str) -> list[dict]:
    # logger.debug(f'receive new article_content:\n{article_content}')
    # result = dashscope_llm([{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': article_content}], model=model, logger=logger)
    result = openai_llm([{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': article_content}], model=model, logger=logger)
    results = pattern.findall(result)
    if not results:
        logger.info(f'can not find info, llm result:\n{result}')
        return []

    texts = results[0].split('<tag>')
    texts = [_.strip() for _ in texts if _.strip()]
    '''
    to_del = []
    to_add = []
    for element in results:
        if "；" in element:
            to_del.append(element)
            to_add.extend(element.split('；'))
    for element in to_del:
        results.remove(element)
    results.extend(to_add)
    results = list(set(results))
    '''
    cache = []
    for text in texts:
        logger.debug(f'prepare parse: {text}')
        if '</tag>' not in text:
            continue
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
        if info.startswith('无相关信息') or info.startswith('该新闻未提及') or info.startswith('未提及'):
            logger.debug(f'no relevant info: {text}')
            continue

        cache.append({'content': info, 'tag': tag})

    return cache
