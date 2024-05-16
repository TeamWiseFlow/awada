from scrapers import *
from utils.general_utils import extract_urls
from loguru import logger
import os
import json
from datetime import datetime, timedelta
from lurker.get_info import get_info, pb, project_dir
from urllib.parse import urlparse


expiration_days = 7
existing_urls = [url['url'] for url in pb.read(collection_name='articles', fields=['url']) if url]


def pipeline(_input: dict):
    logger.debug(_input)
    cache = {}
    source = _input['user_id'].split('@')[-1]

    if _input['type'] == 'url':
        try:
            cache = json.loads(_input['content'])
        except Exception as e:
            logger.warning(f'json.loads failed, writing to cache_file - {e}')
            return
        urls = [cache['url']]
        if _input['addition'] and cache['abstract']:
            cache['abstract'] = f"（{_input['addition']} 报道）{cache['abstract']}"
    elif _input['type'] == 'text':
        urls = extract_urls(_input['content'])
        if not urls:
            logger.debug("can not find any url, pass...")
            return
    else:
        return

    global existing_urls

    for url in urls:
        # 0、先检查是否已经爬取过
        if url in existing_urls:
            logger.info(f"{url} has been crawled, skip")
            continue

        logger.debug(f"fetching {url}")
        # 1、选择合适的爬虫fetch article信息
        if url.startswith('https://mp.weixin.qq.com'):
            flag, article = mp_crawler(url, logger)
        else:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            if domain in scraper_map:
                flag, article = scraper_map[domain](url, logger)
            else:
                flag, article = simple_crawler(url, logger)

        if flag != 11:
            logger.info(f"{url} failed with mp_crawler and simple_crawler")
            flag, article = llm_crawler(url, logger)
            if flag != 11:
                logger.info(f"{url} failed with llm_crawler")
                continue

        existing_urls.append(url)
        article['source'] = source

        if cache and cache['title']:
            article['title'] = cache['title']
            if not article['abstract']:
                article['abstract'] = cache['abstract']
        # 2、文章入库（不管是否抽取出来info，所有爬取的文章都入库）
        try:
            article_id = pb.add(collection_name='articles', body=article)
        except Exception as e:
            logger.error(f'add article failed, writing to cache_file - {e}')
            with open(os.path.join(project_dir, 'cache_articles.json'), 'a', encoding='utf-8') as f:
                json.dump(article, f, ensure_ascii=False, indent=4)
            continue

        # 3、判断是否早于 当日- expiration_days ，如果是的话，舍弃
        expiration_date = datetime.now() - timedelta(days=expiration_days)
        expiration_date = expiration_date.strftime('%Y%m%d')
        article_date = int(article['publish_time'])
        if article_date < int(expiration_date):
            logger.info(f"publish date is {article_date}, too old, skip")
            continue

        # 4、使用content从中提炼信息
        insights = get_info(f"标题：{article['title']}\n\n内容：{article['content']}")
        if not insights:
            continue

        # 5、把新的insight入库
        for insight in insights:
            insight['articles'] = [article_id]
            try:
                _insight_id = pb.add(collection_name='insights', body=insight)
            except Exception as e:
                logger.error(f'add insight failed, writing to cache_file - {e}')
                with open(os.path.join(project_dir, 'cache_insights.json'), 'a', encoding='utf-8') as f:
                    json.dump(insight, f, ensure_ascii=False, indent=4)

    # todo insight 比对去重与合并
