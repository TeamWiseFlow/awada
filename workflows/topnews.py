from llms.qanything import search
from datetime import datetime
import os
import pickle


async def general_top_news(kbs: list[str], wf_dir: str, model: str, welcome_message: str, top_news_item: dict,
                           max_items: int, cache_file: str, logger=None) -> str:

    if not os.path.exists(cache_file):
        logger.info("cache file not found, creating new one")
        reported_urls = set()
    else:
        logger.debug("cache file found, loading")
        with open(cache_file, 'rb') as f:
            reported_urls = pickle.load(f)

    # given_date = datetime.now() - timedelta(days=7)
    data = {}
    tag_news_count = {}
    news_count = 0
    clean_titles = set()
    for tag, query_list in top_news_item.items():
        logger.debug(f'tag: {tag}')
        for query in query_list:
            logger.debug(f'query: {query}')
            try:
                flag, msg, search_result = await search(query, kb_ids=kbs, wf_dir=wf_dir, top_k=64,
                                                        exactly_search=False, logger=logger, model=model)
            except Exception as e:
                logger.error(f'error occurred: {e}')
                continue
            logger.debug(f'got {len(search_result)} raw items')
            for doc in search_result:
                if doc['type'] != 'wiseflow':
                    logger.debug(f"{doc['type']} type, skipping")
                    continue
                if not doc['title'] or not doc['source']:
                    logger.debug(f"title or source is empty, aborting")
                    continue

                title = doc['title']
                url = doc['source']

                if url in reported_urls:
                    logger.debug(f"{title} has been reported, skipping")
                    continue

                # 判断是否太旧
                modification_time = os.path.getmtime(doc['attachment'])
                modification_datetime = datetime.fromtimestamp(modification_time)
                # if modification_datetime < given_date:
                #     logger.debug(f"最后修改时间早于 {given_date}，舍弃。")
                #    continue
                # 规避多家媒体同一天转发报道的情况
                clean_title = title.split('// ')[-1]
                if clean_title in clean_titles:
                    logger.debug(f"{clean_title} has been reported today, skipping")
                    reported_urls.add(url)
                    continue
                clean_titles.add(clean_title)

                if title not in data:
                    data[title] = {}
                # 保证一个 tag 只包含同新闻的一个 url
                # 这里先仅通过 title 判断新闻是否重复，后续看需要要不要做近似去重，甚至是根据 content 去重
                data[title][tag] = (url, modification_datetime)
                logger.debug(f"{title} added")
        tag_news_count[tag] = len(data) - news_count
        news_count = len(data)

    # 去重过程 去重策略：保留在最少内容的 tag 中。
    results = {}
    for title in data.keys():
        tags = list(data[title].keys())
        if len(tags) == 1:
            tag = tags[0]
            url, news_date = data[title][tag]
        else:
            # 寻找 tag_news_count 值最小的 tag
            temp = {tag_news_count[v]: v for v in tags}
            tag = temp[min(temp.keys())]
            url, news_date = data[title][tag]
            tag_news_count[tag] += 1

        if tag not in results:
            results[tag] = [(title, url, news_date)]
        else:
            results[tag].append((title, url, news_date))
        continue

    top_news = ''
    # 拼接最后的 str
    for tag in top_news_item.keys():
        if tag not in results:
            logger.info(f"no news for {tag}")
            continue
        if len(results[tag]) > max_items:
            logger.debug(f"{tag} has more than {max_items} news, sorting and truncating")
            results[tag].sort(key=lambda x: x[2], reverse=True)
            logger.debug(f"sorted news: {results[tag]}")
            results[tag] = results[tag][:max_items]
        tag_news_list = []
        for title, url, news_date in results[tag]:
            tag_news_list.append(f"{title}\n{url}")
            reported_urls.add(url)
        tag_news = "\n".join(tag_news_list)
        top_news = f"{top_news}\n\n#{tag}\n{tag_news}"
    
    # 将reported_urls 写入文件
    with open(cache_file, 'wb') as f:
        pickle.dump(reported_urls, f)

    if not top_news:
        logger.info("no top news today")
        return ""

    return f"{datetime.now().strftime('%Y-%m-%d')} {welcome_message}:{top_news}"
