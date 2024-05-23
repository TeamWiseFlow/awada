from scrapers import *
from utils.general_utils import extract_urls
from lurker.get_info import get_info, pb, project_dir, logger
import os
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse
# from llms.embeddings import embed_model, reranker
# from langchain_community.vectorstores import FAISS
# from langchain_core.documents import Document
# from langchain_community.vectorstores.utils import DistanceStrategy
# from langchain.retrievers import ContextualCompressionRetriever
import re


# 用正则不用xml解析方案是因为公众号消息提取出来的xml代码存在异常字符
item_pattern = re.compile(r'<item>(.*?)</item>', re.DOTALL)
url_pattern = re.compile(r'<url><!\[CDATA\[(.*?)]]></url>')
summary_pattern = re.compile(r'<summary><!\[CDATA\[(.*?)]]></summary>')

expiration_days = 7
existing_urls = [url['url'] for url in pb.read(collection_name='articles', fields=['url']) if url['url']]


def pipeline(_input: dict):
    cache = {}
    source = _input['user_id'].split('@')[-1]
    logger.debug(f"received new task, user: {source}, MsgSvrID: {_input['addition']}")

    if _input['type'] == 'publicMsg':
        items = item_pattern.findall(_input["Content"])
        # 遍历所有<item>内容，提取<url>和<summary>
        for item in items:
            url_match = url_pattern.search(item)
            summary_match = summary_pattern.search(item)
            url = url_match.group(1) if url_match else None
            if not url:
                logger.warning(f"can not find url in \n{item}")
                continue
            if url in cache:
                logger.debug(f"duplict url in \n{item}")
            summary = summary_match.group(1) if summary_match else None
            if not summary:
                logger.warning(f"can not find summary in \n{item}")
            cache[url] = summary
        urls = list(cache.keys())
    elif _input['type'] == 'text':
        urls = extract_urls(_input['content'])
        if not urls:
            logger.debug("can not find any url, pass...")
            return
    elif _input['type'] == 'url':
        urls = []
        pass
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

        # 2、判断是否早于 当日- expiration_days ，如果是的话，舍弃
        expiration_date = datetime.now() - timedelta(days=expiration_days)
        expiration_date = expiration_date.strftime('%Y-%m-%d')
        article_date = int(article['publish_time'])
        if article_date < int(expiration_date.replace('-', '')):
            logger.info(f"publish date is {article_date}, too old, skip")
            continue

        article['source'] = source
        if url in cache and cache[url]:
            article['abstract'] = cache[url]

        # 3、使用content从中提炼信息
        insights = get_info(f"标题：{article['title']}\n\n内容：{article['content']}")
        # 提炼info失败的article不入库，不然在existing里面后面就再也不会处理了，但提炼成功没有insight的article需要入库，后面不再分析。

        # 4、article入库
        try:
            article_id = pb.add(collection_name='articles', body=article)
        except Exception as e:
            logger.error(f'add article failed, writing to cache_file - {e}')
            with open(os.path.join(project_dir, 'cache_articles.json'), 'a', encoding='utf-8') as f:
                json.dump(article, f, ensure_ascii=False, indent=4)
            continue

        existing_urls.append(url)

        if not insights:
            continue
        # insight 比对去重与合并, article打标签，insight入库
        article_tags = set()
        # 从数据库中读取过去expiration_days的insight记录，避免重复
        old_insights = pb.read(collection_name='insights', filter=f"updated>'{expiration_date}'")
        for insight in insights:
            article_tags.add(insight['tag'])
            # 从old_insights 中挑出相同tag的insight，组成 content: id的反查字典
            old_insight_dict = {i['content']: i for i in old_insights if i['tag'] == insight['tag']}
            """
            insight_list = [Document(page_content=key, metadata={}) for key, value in old_insight_dict.items()]
            retriever = FAISS.from_documents(insight_list, embed_model,
                                             distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT).as_retriever(
                search_type="similarity",
                search_kwargs={"score_threshold": 0.92, "k": 1})
            compression = ContextualCompressionRetriever(base_compressor=reranker, base_retriever=retriever)
            rerank_results = compression.get_relevant_documents(insight['content'])
            if rerank_results and rerank_results[0].metadata['relevance_score'] > 0.92:
                old_content = rerank_results[0].page_content
                logger.debug(f"{insight['content']} is too similar to {old_content}, merging")
                insight['articles'] = old_insight_dict[old_content]['articles'] + [article_id]
                # 旧的insight需要从old_insights删除
                old_insights.remove(old_insight_dict[old_content])
                # 对于日期与采集日一样的old_insight，还需要从pb中删除
                old_updated_date = old_insight_dict[old_content]['updated'].date()
                today_utc = datetime.utcnow().date()
                if old_updated_date == today_utc:
                    pb.delete(collection_name='insights', id=old_insight_dict[old_content]['id'])
            else:
                insight['articles'] = [article_id]
            """
            if insight in old_insight_dict:
                insight['articles'] = old_insight_dict[insight]['articles'] + [article_id]
                # 旧的insight需要从old_insights删除
                old_insights.remove(old_insight_dict[insight])
                pb.delete(collection_name='insights', id=old_insight_dict[insight]['id'])
            else:
                insight['articles'] = [article_id]

            old_insights.append(insight)
            try:
                _insight_id = pb.add(collection_name='insights', body=insight)
            except Exception as e:
                logger.error(f'add insight failed, writing to cache_file - {e}')
                with open(os.path.join(project_dir, 'cache_insights.json'), 'a', encoding='utf-8') as f:
                    json.dump(insight, f, ensure_ascii=False, indent=4)

        try:
            pb.update(collection_name='articles', id=article_id, body={'tag': list(article_tags)})
        except Exception as e:
            logger.error(f'update article failed - article_id: {article_id}\n{e}')
            article['tag'] = list(article_tags)
            with open(os.path.join(project_dir, 'cache_articles.json'), 'a', encoding='utf-8') as f:
                json.dump(article, f, ensure_ascii=False, indent=4)
