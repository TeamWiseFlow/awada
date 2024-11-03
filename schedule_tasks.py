"""
目前定义两个定时任务：
1、每日发布昨日简报（如果 对应的config 里面有配置的话；
2、每日凌晨自动进行指定站点学习，如果config 里面有配置的话
3、每日晚进行Qanything daily status check并清理数据库（被清理的文件在 Qanything 后台也看不到）
"""
import schedule
import time
from workflows.topnews import general_top_news
from utils.general_utils import get_logger
import os, json
import httpx
import asyncio
from llms.qanything import purge_kb, daily_status


logger = get_logger(logger_name='schedule_tasks', logger_file_path='projects_data')
service_url = os.environ.get('AWADA_ENDPOINT', 'http://127.0.0.1:8077/')
WX_BOT_ENDPOINT = os.environ.get('WX_BOT_ENDPOINT', '127.0.0.1:8066')
wx_url = f"http://{WX_BOT_ENDPOINT}/api/"

if os.path.exists('directors.json'):
    logger.info("directors.json exists, loading...")
    with open('directors.json', 'r', encoding='utf-8') as f:
        directors = json.load(f)
else:
    directors = []


def send_msg(user_id: str, content: str):
    endpoint = f"{wx_url}sendtxtmsg"
    body = {"wxid": user_id, "content": content}
    with httpx.Client() as client:
        response = client.post(endpoint, json=body)
        if response.status_code != 200:
            logger.error(f"send message failed: {response.text}")


# 企微简报发送函数，如果不用企微这个函数无作用
def send_qw_msg(room_id: str, msg: str):
    msg_send_api_base = "http://localhost:8088/api/sendtxtmsg"
    data = {
        "wxid": room_id,
        "content": msg
    }
    try:
        with httpx.Client() as client:
            response = client.post(msg_send_api_base, json=data)
            if response.status_code == 200:
                logger.info("send message to wechat success")
            else:
                logger.error(f"send message to wechat failed: {response.text}")
                for director in directors:
                    send_msg(director, f"企微 {room_id} 群消息发送失败，赶紧起床去排查吧！[擦汗]")
    except Exception as e:
        logger.error(f"send message to wechat failed: {e}")
        for director in directors:
            send_msg(director, f"企微 {room_id} 群消息发送失败，赶紧起床去排查吧！[擦汗]")


# 配置读取函数
def scan_configs() -> dict:
    result = {"topnews":[], "wiseflow_sites":[]}
    config_folder_path = os.environ.get("CONFIGS", "avatars")
    config_files = [file for file in os.listdir(config_folder_path) if file.endswith('.json')]
    logger.info(f"total {len(config_files)} config files from {config_folder_path}")
    for file in config_files:
        config_file = os.path.join(config_folder_path, file)
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if config.get("wiseflow_sites", []):
            result["wiseflow_sites"].append({"bot_id":config["bot_id"], "sites":config["wiseflow_sites"]})
        if config.get("top_news_items", {}) and config.get("topnews_scriber", []):
            try:
                bot_id = config['bot_id'] if config['bot_id'] else "default"
                kbs = config["kbs"]
                model = config["chat_model"]
                top_news_item = config["top_news_items"]
                welcome_message = config.get("topnews_shout", "")
                max_items = config.get("topnews_max", 5)
                scriber = config.get("topnews_scriber", [])
                result["topnews"].append({"bot_id":bot_id, "welcome_message":welcome_message, "kbs":kbs, "model":model,
                                          "top_news_item":top_news_item, "max_items":max_items, "scriber":scriber})
            except Exception as e:
                logger.warning(f"config file {config_file} has error: {e}, cannot excute topnews task")
    logger.info(f"topnews tasks: {len(result['topnews'])}, wiseflow scan tasks: {len(result['wiseflow_sites'])}")
    return result

def topnews_task():
    configs = scan_configs()
    if not configs["topnews"]:
        logger.info("no topnews tasks")
        return

    configs = configs["topnews"]
    sending_list = {}
    for config in configs:
        scriber = config.pop("scriber")
        sending_list[config["bot_id"]] = scriber

    async def process_single_config(config: dict, results: dict, logger):
        logger.debug(f"start topnews task for {config['bot_id']}")
        bot_id = config.pop("bot_id")
        project_dir = os.path.join("projects_data", bot_id)
        config["cache_file"] = os.path.join(project_dir, "reported_urls.pkl")
        config["wf_dir"] = os.path.join(project_dir, 'wiseflow')
        config["logger"] = logger
        result = await general_top_news(**config)
        results[bot_id] = result

    async def process_configs(configs, logger):
        tasks = []
        final_results = {}
        # 为每个 config 创建任务
        for config in configs:
            tasks.append(asyncio.create_task(process_single_config(config, final_results, logger)))
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        return final_results

    news = asyncio.run(process_configs(configs, logger))
    for bot_id, top_news in news.items():
        if not top_news:
            logger.info(f'no top news today for {bot_id}')
            continue
        # 企微发送
        for room_id in sending_list[bot_id]:
            logger.debug(f"send top news to {room_id}")
            send_qw_msg(room_id=room_id, msg=top_news)
            logger.debug("done")
        """
        # 个微发送
        for room_id in sending_list[bot_id]:
            logger.debug(f"send top news to {room_id}")
            send_msg(room_id, top_news)
            logger.debug("done")
        """

def wiseflow_task():
    configs = scan_configs()
    if not configs["wiseflow_sites"]:
        logger.info("no wiseflow_sites tasks")
        return
    configs = configs["wiseflow_sites"]
    for config in configs:
        bot = config["bot_id"]
        logger.info(f"start wiseflow scanning task for {bot}")
        for site_url in config["sites"]:
            post_body = {"user_id": "everyday task", "type": "url", "content": site_url, "addition": "", "bot_id": bot}
            with httpx.AsyncClient() as client:
                response = client.post(f"{service_url}feed", json=post_body)
            if response.status_code != 200:
                logger.warning(f"failed to post to service, 响应内容: {response.text}")
                for director in directors:
                    send_msg(director, "后端服务feed 接口异常，请去排查[擦汗]")

def qanything_daily_maintance():
    logger.info("start daily qanything maintenance")
    flag, result = daily_status()
    if flag != 200:
        logger.warning(f"qanything daily status check failed: {result}")
        for director in directors:
            send_msg(director, "[惊恐]别睡了！qanything daily status check failed！")
        return
    if not result:
        logger.info("no kb to clean")
        return
    logger.info(f"qanything daily check: {result}")
    flag, msg = purge_kb(logger=logger)
    if flag != 200:
        logger.warning(f"qanything daily status check failed: {msg}")
    else:
        logger.info(f"kb cleaned: {msg}")


schedule.every().day.at("00:38").do(wiseflow_task)
schedule.every().day.at("07:38").do(topnews_task)
schedule.every().day.at("22:38").do(qanything_daily_maintance)

# topnews_task()
logger.info("Schedule started")
while True:
    try:
        schedule.run_pending()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    time.sleep(60)
