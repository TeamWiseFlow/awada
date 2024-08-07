from .openai_wrapper import openai_llm
# import re


system_prompt = '''你是一名家长，你很关注自己孩子的升学问题。你将被给到一个字典格式的新闻列表，每一个元素代表一条新闻，key是该条新闻的id，value是该条新闻的内容。
请从给到的新闻列表中精选出最值得你关注的一条，并给出它的id。

请仅输出id，不要输出其他信息。'''

# 实测yi:9b-chat-v1.5-fp16 可以很好的支持40条（关注点分布均匀）
batch_size = 39
mini_batch_size = 7
model = '01-ai/Yi-1.5-9B-Chat-16K'
# pattern = re.compile(r'\"\"\"(.*?)\"\"\"', re.DOTALL)


def pipeline(data: list, logger=None) -> dict:
    if not data:
        logger.info('empty data')
        return {}

    if len(data) <= mini_batch_size:
        logger.info(f'datas less than mini_batch_size: {mini_batch_size}, will return all')
        return {d['content']: d['articles'] for d in data}

    results = {}
    articles = {}
    maps = {}
    for d in data:
        articles[d['id']] = d['content']
        maps[d['id']] = d['articles']
        if len(articles) > batch_size:
            result = openai_llm(
                [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': str(articles)}],
                model, logger)
            try:
                # parsed = pattern.findall(result)[0]
                parsed = result.strip()
                logger.debug(f'parsed: {parsed}')
                if parsed in articles:
                    results[articles[parsed]] = maps[parsed]
                else:
                    logger.warning(f'bad result: {result}')
            except Exception as e:
                logger.warning(f'bad request: {e}')
            articles = {}
            maps = {}

    if articles:
        result = openai_llm(
            [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': str(articles)}], model, logger)
        try:
            # parsed = pattern.findall(result)[0]
            parsed = result.strip()
            logger.debug(f'parsed: {parsed}')
            if parsed in articles:
                results[articles[parsed]] = maps[parsed]
            else:
                logger.warning(f'bad result: {result}')
        except Exception as e:
            logger.warning(f'bad request: {e}')

    return results
