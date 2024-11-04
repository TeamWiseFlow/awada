import httpx
import os, re
from aiofiles import open as aio_open
import asyncio
from typing import Optional


headers = {
    "Content-Type": "application/json"
}
api_base = os.environ.get('LLM_API_BASE', "https://api.openai-proxy.org/v1")
api_key = os.environ.get('LLM_API_KEY', "sk-xxx")
workspace = os.environ.get('QANYTHING_LOCATION', os.path.expanduser("~"))

semaphore = asyncio.Semaphore(5)

async def upload_files_to_kb(kb_id: str, files: list[str], user_id: str = "zzp", mode: str = "soft",
                             chunk_size: int = 800, logger=None) -> (int, str):
    async def send_request(kb_id: str, files: list[str], user_id: str = "zzp", logger=None):
        url = 'http://127.0.0.1:8777/api/local_doc_qa/upload_files'
        data = {
            'user_id': user_id,
            'kb_id': kb_id,
            'mode': mode,
            'chunk_size': chunk_size
        }
        files_data = [('files', open(file, 'rb')) for file in files]

        for attempt in range(2):
            exception_occurred = False  # 标志变量，用于判断是否发生了异常
            try:
                async with semaphore:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(url, data=data, files=files_data)
                response_data = response.json()
                if logger:
                    logger.debug(response_data)
                else:
                    print(response_data)
                code = response_data.get('code', -3)
                msg = response_data.get('msg', 'qanything out of service')
                return code, msg
            except Exception as e:
                exception_occurred = True  # 设置标志变量，表示发生了异常
                if attempt < 1:
                    logger.info('qanything upload service busy, waiting for 1s to retry...')
                    await asyncio.sleep(1)  # 等待一段时间后重试
                else:
                    if logger:
                        logger.error(f'error in uploading files to qanything: {e}')
                    else:
                        print(e)
                    return -3, "qanything out of service"
            finally:
                if attempt == 1 or (attempt < 1 and not exception_occurred):
                    for file in files_data:
                        file[1].close()

    tasks = []
    task = asyncio.create_task(send_request(kb_id=kb_id, files=files, user_id=user_id, logger=logger))
    tasks.append(task)
    results = await asyncio.gather(*tasks)
    # 检查所有任务的结果，如果有 flag 不等于 200 的项目，则返回该项目的 code 和 msg
    for result in results:
        code, msg = result
        if code != 200:
            return code, msg
    # 如果所有项目的 flag 都是 200，则返回第一个项目的 code 和 msg
    return results[0]


async def create_new_kb(kb_name: str, user_id: str = "zzp", quick: bool = False, logger=None) -> (int, str):
    data = {
        "user_id": user_id,
        "kb_name": kb_name,
        "quick": quick
    }
    if logger:
        logger.debug(f'create new kb request: {data}')
    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8777/api/local_doc_qa/new_knowledge_base", headers=headers, json=data)
        if response.status_code != 200:
            return -3, "out of service"
    res = response.json()
    if logger:
        logger.debug(f'response: {res}')
    flag = res.get('code', '-3')
    if flag == 200:
        return flag, res['data']['kb_id']
    return flag, res.get('msg', '')


def create_kb(kb_name: str, user_id: str = "zzp", quick: bool = False, logger=None) -> (int, str):
    data = {
        "user_id": user_id,
        "kb_name": kb_name,
        "quick": quick
    }
    if logger:
        logger.debug(f'create new kb request: {data}')
    with httpx.Client() as client:
        response = client.post("http://127.0.0.1:8777/api/local_doc_qa/new_knowledge_base", headers=headers, json=data)
        if response.status_code != 200:
            return -3, "out of service"
    res = response.json()
    if logger:
        logger.debug(f'response: {res}')
    flag = res.get('code', '-3')
    if flag == 200:
        return flag, res['data']['kb_id']
    return flag, res.get('msg', '')


async def get_file_base64(file_id: str, logger=None):
    url = f"http://127.0.0.1:8777/api/local_doc_qa/get_file_base64"
    data = {
        "file_id": file_id
    }
    if logger:
        logger.debug(f'get file base64 request: {data}')
    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, json=data)
        if response.status_code != 200:
            return -3, "out of service"
    res = response.json()
    flag = res.get('code', '-3')
    msg = res.get('msg', '')
    if flag != 200:
        return flag, msg
    return flag, res['file_base64']


async def rerank_service(query: str, doc_ids: Optional[list] = None, doc_strs: Optional[list] = None, logger=None):
    url = f"http://127.0.0.1:8777/api/local_doc_qa/get_rerank_results"
    data = {
        "query": query,
        "doc_ids": doc_ids if doc_ids else [],
        "doc_strs": doc_strs if doc_strs else []
    }
    if logger:
        logger.debug(f'rerank service request: {data}')
    for attempt in range(2):
        try:
            async with semaphore:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url=url, headers=headers, json=data)
                    res = response.json()
                    break
        except Exception as e:
            if attempt < 2:
                logger.info('qanything rerank service busy, waiting for 3s to retry...')
                await asyncio.sleep(3)  # 等待一段时间后重试
            else:
                if logger:
                    logger.error(f'error in qanything rerank: {e}')
                else:
                    print(e)
                return -3, "qanything out of service"

    if logger:
        logger.debug(f'response: {res}')
    flag = res.get('code', '-3')
    msg = res.get('msg', '')
    if flag != 200:
        return flag, msg
    return flag, res['rerank_results']


async def get_doc(doc_id: str, logger=None):
    url = f"http://127.0.0.1:8777/api/local_doc_qa/get_doc"
    data = {
        "doc_id": doc_id
    }
    if logger:
        logger.debug(f'get doc request: {data}')
    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, json=data)
        if response.status_code != 200:
            return -3, "out of service"
    res = response.json()
    if logger:
        logger.debug(f'response: {res}')
    flag = res.get('code', '-3')
    if flag != 200:
        return flag, res.get('msg', '')
    return flag, res['doc_text']


async def find_origin_file(file_id: str, user_id: str = "zzp") -> (int, str):
    data = {
        "file_id": file_id,
        "user_id": user_id,
        "kb_id": "not_use_yet"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("http://127.0.0.1:8777/api/local_doc_qa/get_doc_completed", headers=headers, json=data)
        if response.status_code != 200:
            return -3, "out of service"
    res = response.json()

    flag = res.get('code', '-3')
    if flag != 200:
        return flag, res.get('msg', '')
    return flag, res['chunks'][0]['metadata']['nos_key'].replace('/workspace', workspace)


def purge_kb(kb_ids: Optional[list] = None, user_id: str = "zzp", logger=None) -> (int, str):
    data = {
        "kb_ids": kb_ids if kb_ids else [],
        "user_id": user_id,
        "status": "red"
    }
    if logger:
        logger.debug(f'purge kb: {data}')
    with httpx.Client() as client:
        response = client.post("http://127.0.0.1:8777/api/local_doc_qa/clean_files_by_status", headers=headers, json=data)
        if response.status_code != 200:
            return -3, "out of service"
    res = response.json()
    if logger:
        logger.debug(f'response: {res}')
    flag = res.get('code', '-3')
    msg = ''
    if flag != 200:
        msg = '入库失败-切分失败文件 清理失败'

    data = {
        "kb_ids": kb_ids,
        "user_id": user_id,
        "status": "yellow"
    }
    if logger:
        logger.debug(f'purge kb: {data}')
    with httpx.Client() as client:
        response = client.post("http://127.0.0.1:8777/api/local_doc_qa/clean_files_by_status", headers=headers, json=data)
        if response.status_code != 200:
            return -3, "out of service"
    res = response.json()
    if logger:
        logger.debug(f'response: {res}')
    flag = res.get('code', '-3')
    if flag != 200:
        msg = f"{msg}\n入库失败-milvus 失败 文件清理失败"
    return flag, msg


async def search(query: str, kb_ids: list[str], model: str, wf_dir:str, top_k: int = 3, user_id: str = "zzp",
                 history: Optional[list] = None, exactly_search: bool = True, network_search: bool = False,
                 web_chunk_size: int = 800, logger=None) -> (int, str, list[dict]):
    """
    QA以及 RAG 场景必须使用exactly_search模式，不然会十分影响问答质量；
    topnews 等粗略召回场景下可以使用非 exactly_search
    """
    url = 'http://127.0.0.1:8777/api/local_doc_qa/local_doc_chat'
    data = {
        "user_id": user_id,
        "kb_ids": kb_ids,
        "history": history if history else [],
        "question": query,
        "only_need_search_results": True,
        "rerank": exactly_search,
        "hybrid_search": True,
        "max_token":512,
        "api_base":api_base,
        "api_key":api_key,
        "model":model,
        "api_context_length":4096,
        "top_k": top_k,
        "networking": network_search,
        "web_chunk_size": web_chunk_size
    }
    for attempt in range(3):
        try:
            async with semaphore:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url=url, headers=headers, json=data)
                    res = response.json()
                    flag = res.get('code', '-4')
                    msg = res.get('msg', '')
        except Exception as e:
            if attempt < 2:
                logger.info('qanything search service busy, waiting for 1s to retry...')
                await asyncio.sleep(1)  # 等待一段时间后重试
            else:
                if logger:
                    logger.error(f'error for qanything searching service: {e}')
                else:
                    print(e)
                return -4, "out of service", []

    if flag != 200:
        return flag, msg, []
    source_documents = res.get("source_documents", [])

    threshold = 0.5 if exactly_search else 0.72 #exactly_search 下分值为 rerank 后分值，最高1分（单召回分值可能大于1）
    result = []
    for doc in source_documents:
        if logger:
            logger.debug(doc["score"])
        # 目前各类型业务均发现低阈值0.5可以较好的保证召回结果相关性且不遗失
        if float(doc["score"]) < threshold:
            if logger:
                logger.debug(f'doc score too low: {doc["score"]}, will abort this and after')
            break
        if not doc['content']:
            continue
        # faq 情况
        if doc["file_name"].endswith(".faq"):
            title_text = doc["file_name"][4:-4]
            if exactly_search and (float(doc["score"]) > 0.88 or title_text == query):
                # 这个时候就不用考虑其他的了……
                # 因为是 rerank 计算，所以完全等于的情况也可能不是0.9
                if logger:
                    logger.debug(f'top1 FAQ score high enough: {doc["score"]} or exact match')
                return flag, msg, [{"type": "faq", "content": doc["content"], "source": "",
                           "title": title_text, "attachment": ""}]

            result.append({"type": "faq", "content": doc["content"], "source": "",
                           "title": title_text, "attachment": ""})
            continue
        # wiseflow存入的 md 文件
        if doc["headers"]["知识库名"].startswith("wiseflow-") or doc["headers"]["知识库名"] == 'linxiaozhu': #后一个条件是历史特例
            file_path = os.path.join(wf_dir, doc["file_name"])
            try:
                async with aio_open(file_path, 'r', encoding='utf-8') as file:
                    md_content = await file.read()
                title_match = re.search(r'# (.+?)\n', md_content)
                title = title_match.group(1) if title_match else ""
                # 使用正则表达式提取 url
                url_match = re.search(r'## Origin URL\n\n(.+)', md_content)
                origin_url = url_match.group(1) if url_match else ""
            except Exception as e:
                if logger:
                    logger.error(f"Error reading wiseflow md file: {e}")
                else:
                    print(f"Error reading wiseflow md file: {e}")
                title = ""
                origin_url = ""
            content = re.sub(r'^#.*?\n\n', '', doc["content"]).strip()
            if not content:
                continue
            result.append({"type": "wiseflow", "source": origin_url, "content": content,
                           "title": title, "attachment": file_path})
        else:
            # 普通文件/普通网页
            if doc["file_url"]:
                result.append({"type": "wiseflow", "source": doc["file_url"], "content": doc["content"],
                               "title": doc["file_name"], "attachment": ""})
            else:
                flag, file_path = await find_origin_file(file_id=doc["file_id"])
                if flag == 200:
                    result.append({"type": "file", "source": "", "content": doc["content"],
                                   "title": doc["file_name"], "attachment": file_path})
                else:
                    logger.error(f"{doc['file_name']} can not find file_path")
                    result.append({"type": "file", "source": "", "content": doc["content"],
                                   "title": doc["file_name"], "attachment": ""})
    return flag, msg, result


def daily_status(user_id: str = "zzp") -> (int, dict):
    data = {
        "user_id": user_id, "by_date": False
    }
    with httpx.Client() as client:
        response = client.post("http://127.0.0.1:8777/api/local_doc_qa/get_total_status", headers=headers, json=data)
        if response.status_code == 200:
            res = response.json()
            flag = res.get('code', '-4')
            result = res.get("status", {})
            return flag, result.get(f'{user_id}__1234', {})
    return -4, {}


async def check_health() -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8777/api/health_check", headers=headers)
    if response.status_code == 200:
        res = response.json()
        flag = res.get('msg', '')
        return flag == 'success'
    return False

"""
new_kb_id = 
print('test for uploading urls')
url = "http://127.0.0.1:8777/api/local_doc_qa/upload_weblink"

urls = ['https://mp.weixin.qq.com/s?__biz=MjM5MjAxNDM4MA==&mid=2666867198&idx=1&sn=840837a920017da2734b639c3e459466',
        'https://mp.weixin.qq.com/s?__biz=MzA4MTEyOTM2Mw==&mid=2652104825&idx=1&sn=68f1fe354b532de0088659d058f2b14f',
        'https://mp.weixin.qq.com/s?__biz=MzIxNDA3NDYxNw==&mid=2651749974&idx=1&sn=ee3769c4b601d9486295aa1a039c37d6']
for u in urls:
    data = {
    "user_id": "zzp",
    "kb_id": new_kb_id,
    "url": u,
}

    response = requests.post(url, headers=headers, json=data)
    print(response.status_code)
    print(response.text)
    docs_id = response.json()['data'][0]['file_id']

print('-' * 24)
print('test for check the docs')
url = "http://127.0.0.1:8777/api/local_doc_qa/get_doc_completed"
data = {
    "user_id": "zzp",
    "kb_id": new_kb_id,
    "file_id": docs_id
}

response = requests.post(url, headers=headers, data=json.dumps(data))

print(response.status_code)
print(response.text)
print('-' * 24)
"""