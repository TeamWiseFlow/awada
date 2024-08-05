"""
通过编辑这个脚本，可以自定义需要的后台任务
"""
import schedule
import time
from topnews import pipeline
from loguru import logger
from pb_api import PbTalker
import os
from general_utils import get_logger_level
from datetime import datetime, timedelta
import pytz
import requests


talking_list = ['wxid_tnv0hd5hj3rs11']

project_dir = os.environ.get("PROJECT_DIR", "")
if project_dir:
    os.makedirs(project_dir, exist_ok=True)
logger_file = os.path.join(project_dir, 'awada_tasks.log')

logger.add(
    logger_file,
    level=get_logger_level(),
    backtrace=True,
    diagnose=True,
    rotation="50 MB"
)

pb = PbTalker(logger)
utc_now = datetime.now(pytz.utc)
# 减去一天得到前一天的UTC时间
utc_yesterday = utc_now - timedelta(days=1)
utc_last = utc_yesterday.strftime("%Y-%m-%d %H:%M:%S")
reported_urls = set()


def task():
    global utc_last
    global reported_urls
    logger.debug(f'last_collect_time: {utc_last}')
    datas = pb.read(collection_name='insights', filter=f'updated>="{utc_last}"', fields=['id', 'content', 'tag', 'articles'])
    logger.debug(f"got {len(datas)} items")
    utc_last = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    logger.debug(f'now_utc_time: {utc_last}')

    tags = pb.read(collection_name='tags', filter=f'activated=True')
    tags_dict = {item["id"]: item["name"] for item in tags if item["name"]}
    top_news = {}
    for _id, name in tags_dict.items():
        logger.debug(f'tag: {name}')
        data = [item for item in datas if item["tag"] == _id]
        logger.debug(f"got {len(data)} items")
        topnew = pipeline(data, logger)
        if not topnew:
            logger.debug(f'no top news for {name}')
            continue

        top_news[name] = {}
        for content, articles in topnew.items():
            content_urls = [pb.read('articles', filter=f'id="{a}"', fields=['url'])[0]['url'] for a in articles]
            # 存在报道过的url则跳过
            if not set(content_urls).isdisjoint(reported_urls):
                logger.debug(f'{content} has reported urls')
                continue
            # 去除重叠内容
            # 如果发现重叠内容，哪个标签长就把对应的从哪个标签删除
            to_skip = False
            for k, v in top_news.items():
                to_del_key = None
                for c, u in v.items():
                    if not set(content_urls).isdisjoint(set(u)):
                        if len(topnew) > len(v):
                            to_skip = True
                        else:
                            to_del_key = c
                        break
                if to_del_key:
                    del top_news[k][to_del_key]
                if to_skip:
                    break
            if not to_skip:
                top_news[name][content] = content_urls
                reported_urls.update(content_urls)

        if not top_news[name]:
            del top_news[name]

    if not top_news:
        logger.info("no top news today")
        return

    for name, v in top_news.items():
        if not v:
            continue
        top_news[name] = {content: '\n\n'.join(urls) for content, urls in v.items()}
        top_news[name] = "\n".join(f"{content}\n{urls}" for content, urls in top_news[name].items())

    top_news_text = "\n\n".join(f"{k}\n{v}" for k, v in top_news.items())
    logger.info(top_news_text)

    for wxid in talking_list:
        data = {
            "wxid": wxid,
            "content": top_news_text
        }
        try:
            response = requests.post("http://127.0.0.1:8066/api/sendtxtmsg", json=data)
            if response.status_code == 200:
                logger.info("send message to wechat success")
            else:
                logger.error(f"send message to wechat failed: {response.text}")
        except Exception as e:
            logger.error(f"send message to wechat failed: {e}")
        time.sleep(1)


task()
schedule.every().day.at("07:38").do(task)
while True:
    schedule.run_pending()
    time.sleep(60)
