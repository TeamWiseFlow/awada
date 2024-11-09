# -*- coding: utf-8 -*- #
from llms.openai_wrapper import openai_llm as llm
from llms.qanything import *
from workflows.penholder import Penholder
import time, pickle, json
import uuid
from utils.general_utils import *
from datetime import datetime
from typing import Dict
from scrapers.general_crawler import general_crawler
import asyncio
from typing import Union, List, Optional


bot_system = """来自{org}的知识助理，帮助维护团队的知识库，基于知识库辅助团队成员的问答、资料查找功能。名字是“{name}”。
回答风格要尽量简洁，当无需查询知识库资料或请求用户提供更多信息时，仅使用诸如“好的”“再见”“你好”这样的短语回复用户。
当你判断需要进行知识库查询后才能回复用户时，请输出：#search"""

user_rag_prompt_prefix = "请基于如下的参考资料简洁的回答我的问题。\n\n参考资料：\n"
user_rag_prompt_suffix = """\n\n我的问题:
{user_input}

务必坚持如下回答原则：
1、忠于参考资料。请不要添加任何参考资料中未提及的信息，也不要进行个人猜测或推测；
2、仅做简短的总结式回答即可，我主要还是会根据你的回答查看对应的资料原始文档。
"""

wiseflow_system = """你是一名来自{org}的网络信息编辑，你和你的团队仅关注这些方面的信息：{focus}。
你将被给到一篇网络报道的文字部分，请判断该报道是否值得关注。
请注意文字是通过程序从网页中提取出来的，所以可能会混入一些干扰信息。请仔细思考，因为你的判断会十分影响团队接下来的工作。
请一步一步思考，先给出推断依据，最终再给出结论（是或否，是代表值得关注，否代表不值得关注）。"""

wiseflow_prompt = """\n请按如下顺序和格式进行输出：
Thought:你的推断
Final conclusion:你的最终结论（仅为“是”或“否”）"""

speech_dict = {
    "failed": "[破涕为笑]出错啦，已经通知管理员查看服务器状态，请等待管理员通知，勿重复尝试！",
    "asr_failed": "抱歉，没听清呢，好心人不介意再试一次吧~",
    "others": "{bot_name}开小差了，请联系管理员处理哦～",
    "dissatisfied": "抱歉，我没有在资料库中找到相关信息，为避免误导，我不能回答您的这个问题。",
    "meaningless": "嗯，我在。",
    "wrong_input": "文件库资料仅支持word、pdf、图片和文本信息哦~请您提交正确的文件格式",
    "duple_file": "文件库已经有同名文件啦，请联系管理员操作",
    "no_answer": "未检索到相关信息，请换个问题或联系管理员查证",
    "greeting": "您好，我是来自 {org} 的知识助理 {name}。我可以帮助维护团队的知识库，并基于知识库提供问答、资料查找等服务。\n好助理，不闲聊，图灵测试很无聊[吃瓜]"
}

extensions = ('.pdf', '.docx', '.xlsx', '.doc', '.ppt', '.pptx', '.xls', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.bmp',
              '.tiff', '.mp4', '.avi', '.wmv', '.mkv', '.flv', '.wav', '.mp3', '.avi', '.mov', '.wmv', '.mpeg', '.mpg',
              '.3gp', '.ogg', '.webm', '.m4a', '.aac', '.flac', '.wma', '.amr', '.ogg', '.m4v', '.m3u8', '.m3u', '.ts',
              '.mts')
support_exts = ('.md', '.txt', '.pdf', '.jpg', '.png', '.jpeg', '.docx', '.xlsx', '.pptx', '.eml', '.csv')
time_out_dict = {"qa": 38, "normal": 24, "coacher": 38, "rewrite": 38, "penholder": 38, "recording": 300}


class DialogManager:
    def __init__(self, config: dict, config_file: str, logger):
        # 0. initial bot config file
        try:
            self.name = config['bot_name']
            org = config['bot_org']
            self.llm_model = config["chat_model"]
            focus = config["wiseflow_focus"]
            project_dir = os.path.join("projects_data", config['bot_id'] if config['bot_id'] else "default")
        except Exception as e:
            raise Exception(f"{e}, cannot process initial, pls check {config_file}")

        self.wf_model = config.get("wiseflow_model", "") if config.get("wiseflow_model", "") else self.llm_model
        # 1. base initialization
        self.config_file = config_file
        self.cache_url = os.path.join(project_dir, "cache")
        os.makedirs(self.cache_url, exist_ok=True)
        self.wf_cache = os.path.join(project_dir, 'wiseflow')
        os.makedirs(self.wf_cache, exist_ok=True)
        self.wf_temp = os.path.join(project_dir, 'wiseflow_temp')
        os.makedirs(self.wf_temp, exist_ok=True)
        self.logger = logger

        # 2. bot setting
        self.greeting = config.get('greeting', '')
        if not self.greeting:
            self.greeting = speech_dict['greeting'].format(name=self.name, org=org)
        self.bot_system = bot_system.format(org=org, name=self.name)
        self.wf_system = wiseflow_system.format(org=org, focus=", ".join(focus))
        self.kbs = config.get("kbs", [])
        self.working_kb = config.get("working_kb", "")
        self.wf_kb = config.get("wiseflow_working_kb", "")

        # 3. 检查working_kb是否存在，不存在创建一个
        if not self.working_kb:
            self.logger.info("no working kb set, create new kb")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            flag, new_kb_id = create_kb(f"{self.name}_{timestamp}", logger=self.logger)
            if flag == 200:
                self.logger.info(f"create new kb success: {new_kb_id}")
                self.kbs.append(new_kb_id)
                self.working_kb = new_kb_id

                config['working_kb'] = new_kb_id
                if "kbs" in config:
                    config['kbs'].append(new_kb_id)
                    config['kbs'] = list(set(config['kbs']))
                else: config['kbs'] = [new_kb_id]

                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            else:
                self.logger.error(f"create new kb failed: {flag} {new_kb_id}")
                self.logger.warning(f"{self.name} 未配置知识库，无法上传文件，请手动创建，或稍后再试")

        # 4. 读取历史 url
        self.existing_urls_file = os.path.join(project_dir, "existing_urls.pkl")
        if not os.path.exists(self.existing_urls_file):
            self.existing_urls = set()
        else:
            self.logger.debug("existing_urls.pkl found, loading")
            with open(self.existing_urls_file, 'rb') as f:
                self.existing_urls = pickle.load(f)

        # 5. 预设常用词
        self.replace_dict = {}
        hot_words_txt = os.path.join(project_dir, "replace_word.txt")
        if os.path.exists(hot_words_txt):
            with open(hot_words_txt, "r", encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if "：" in line:
                        value, keys = line.split("：")
                    elif ":" in line:
                        value, keys = line.split(":")
                    else:
                        continue
                    value = value.strip()
                    keys = keys.split("、")
                    for key in keys:
                        self.replace_dict[key.strip()] = value
            self.logger.debug(f"totally {len(self.replace_dict)} words added to replace dict")

        # 6. 其他模块加载以及流程建立
        self.loop = {}
        self.lock = asyncio.Lock()
        self.penholder = Penholder(org, self.llm_model, self.wf_cache, self.logger)
        self.logger.info(f'DialogManager {self.name} init success.')

    async def update_config_file(self, updates: dict):
        self.logger.info(f"updating config file - {updates}")
        config = await aio_config_load(self.config_file)
        config.update(updates)
        await aio_save_config(config, self.config_file)
        self.logger.info("config file updated")

    async def _run_penholder(self, query: str, user_id: str, file_path: str = None) -> dict:
        docx_name = os.path.join(self.cache_url, f"{str(uuid.uuid4())[:8]}.docx")
        if file_path:
            self.logger.debug(f"{user_id} will step into a whole new penholder loop from a docx file, input file:{file_path}")
            flag, result = await self.penholder.writing(opinion=query, out_file=docx_name, kbs=self.kbs, file_path=file_path)
        else:
            if self.loop[user_id]["temp"]:
                self.logger.debug(f"{user_id} has a temp writing and wants to modify it")
                flag, result = await self.penholder.modify(opinion=query, out_file=docx_name, history=self.loop[user_id]["temp"])
            else:
                self.logger.debug(f"{user_id} will step into a whole new penholder loop and I will check which template to use")
                flag, result = await self.penholder.writing(opinion=query, out_file=docx_name, kbs=self.kbs)

        if flag == 21:
            replies = {"flag": flag, "result": [{"type": "file", "answer": docx_name},
                                                {"type": "text", "answer": "已为您生成文件，有什么需要修改或者补充的，可以直接跟我说哦[愉快]"}]}
            self.loop[user_id]["temp"] = result
        elif flag == 0:
            replies = self.build_out(flag, result)
            self.loop[user_id]["temp"] = result
        else:
            replies = self.build_out(flag, result)

        return replies

    # 统一由主程序管理memory，
    # 产品目前定位主要是协助用户从资料库寻找资料以及根据资料库资料进行简单问答，因此不采用复杂的 memory 机制，诸如建立长期记忆库，进行记忆检索召回等……
    # 同时为了避免上轮对话对下轮对话的干扰，采用最保守的策略保存记忆，仅处理可能的追问和澄清场景。【对于小型 llm更如此，比如 qwen2.5-7b int8实测在前轮有答案和无答案的情况下，历史消息都会对本轮对话有一定干扰】
    async def __call__(self, input: dict) -> dict:
        self.logger.debug(f"new input:\n{input}")
        if input['type'] == 'text':
            query = input['content'].strip()
        elif input['type'] == 'voice':
            return self.build_out(-4, "this version does not support voice message, use wechaty work-pro api")
        elif input['type'] == 'file':
            query = input['content'].strip()
            if query.endswith(".docx"):
                # 增加“记一下”功能后可以增加判断逻辑：如果是  user_id 在 sourcing 中，那么问询下
                # 记一下应该是先接受文件（兼顾群聊 和管理员转发两种情况），之后77s 内收到“#记一下”则 add files
                self.loop[input['user_id']] = {"status": "penholder", "memory": [], "temp": None, "last_update": time.time()}
                return await self._run_penholder(query=input['addition'], user_id=input['user_id'], file_path=query)
            else:
                self.logger.debug("wrong_input")
                return self.build_out(-1, "wrong_input")
        else:
            self.logger.debug("wrong_input")
            return self.build_out(-1, "wrong_input")

        # 预处理
        if not query:
            return self.build_out(0, speech_dict["meaningless"])
        if query == "#ding" or query == "#help":
            return self.build_out(0, self.greeting)

        user_id = input['user_id']

        if query.startswith("?") or query.startswith("？"):
            self.logger.debug(f"query start with ？, will reset {user_id}")
            if user_id in self.loop:
                del self.loop[user_id]
            query = query[1:]
            query = clean_query(query, self.name)
            if len(query) <= 1:
                return self.build_out(0, self.greeting)
            status = "qa"
        elif query.startswith("#") or query.startswith("＃"):
            if user_id in self.loop:
                del self.loop[user_id]
            query = query[1:]
            query = clean_query(query, self.name)
            if len(query) <= 1:
                return self.build_out(0, self.greeting)
            status = "penholder"
        else:
            status = self.loop[user_id]["status"] if user_id in self.loop else "normal"

        # 对话超时依然清除所有状态
        if user_id in self.loop and "last_update" in self.loop[user_id]:
            time_out = time_out_dict[status]
            if time.time() - self.loop[user_id]["last_update"] > time_out:
                # 只考虑追问情景，这样是最保险、最安全的，也是问答流程处理最省事的
                self.logger.debug(f"{status} timeout setting: {time_out}s. memory timeout, will reset {user_id}")
                del self.loop[user_id]
                status = "normal"
            else:
                self.loop[user_id]["last_update"] = time.time()

        self.logger.debug(f"user id:{user_id}, status:{status}")

        # 热词替换
        for word, replace_word in self.replace_dict.items():
            if word in query and replace_word not in query:
                self.logger.debug(f"替换：{word} -> {replace_word}")
                query = query.replace(word, replace_word)
                break

        # 写作技能
        if status == "penholder":
            if user_id not in self.loop:
                self.loop[user_id] = {"status": status, "memory": [], "temp": None, "last_update": time.time()}
            return await self._run_penholder(query=query, user_id=user_id)

        # 检索流程
        if status == "qa":
            if not self.kbs:
                self.logger.debug("no knowledge base, so no answer")
                self.logger.debug(speech_dict['no_answer'])
                return self.build_out(0, speech_dict["no_answer"])

            flag, msg, search_result = await search(query, model=self.llm_model, kb_ids=self.kbs, wf_dir=self.wf_cache, logger=self.logger)
            if flag == -4:
                self.logger.error(f"Qanything out of service, code:{flag}, msg:{msg}")
                return self.build_out(flag, speech_dict["failed"])
            if flag > 200:
                self.logger.warning(f"Qanything search failed, code:{flag}, msg:{msg}")
                if check_health():
                    self.logger.info("health check ok, try again")
                    flag, msg, search_result = await search(query, model=self.llm_model, kb_ids=self.kbs, wf_dir=self.wf_cache, logger=self.logger)
                    self.logger.info(f"retry result:{flag}, {msg}")
                else:
                    self.logger.error("health check failed")
                    return self.build_out(1, speech_dict["failed"])
            # formate the reply
            if not search_result:
                self.logger.debug("search result is empty")
                self.logger.debug(speech_dict['no_answer'])
                return self.build_out(0, speech_dict["no_answer"])
            faq_answer = set()
            ws_answer = set()
            to_send_files = set()

            # 没有必要做澄清机制了，？功能本来就是捞资料，另外要0.88以上的 faq才能判定直接回答
            for result in search_result:
                if result['type'] == 'faq':
                    if len(search_result) == 1:
                        reply = f"为您找到如下参考：\n\n{result['content']}"
                        self.loop[user_id] = {"status": "normal", "memory": [[query, reply]], "temp": None,
                                              "last_update": time.time()}
                        self.logger.debug(reply)
                        return self.build_out(0, reply)
                    faq_answer.add(result['content'])
                if result['type'] == 'wiseflow':
                    if result['title'] or result['source']:
                        ws_answer.add(f"{result['title']}\n{result['source']}")
                elif result['type'] == 'file':
                    faq_answer.add(result['title'])
                    if result['attachment']:
                        to_send_files.add(result['attachment'])

            # 拼接回复文本
            reply = ""
            if faq_answer:
                reply = "为您找到如下参考：\n\n"
                for i, answer in enumerate(faq_answer):
                    reply = f"{reply}{i+1}. {answer}\n\n"
            if ws_answer:
                reply = f"{reply}同时如下网络报道中存在可能的提及：\n\n" if reply else "针对您的提问，如下网络报道中存在可能的提及：\n\n"
                for i, answer in enumerate(ws_answer):
                    reply = f"{reply}{i+1}. {answer}\n\n"
            if not reply:
                self.logger.debug("no search result is valid")
                return self.build_out(0, speech_dict["no_answer"])
            self.loop[user_id] = {"status": "normal", "memory": [[query, reply]], "temp": None, "last_update": time.time()}
            self.logger.debug(reply)
            self.logger.debug(f"with files:{to_send_files}")
            to_send_files = list(to_send_files)
            return self.build_out(0, reply, to_send_files)

        # normal process
        messages = [{"role": "system", "content": self.bot_system}]
        lens = len(self.bot_system) + 64 + len(query)
        if user_id in self.loop and self.loop[user_id]["memory"] and lens < 4096: # 暂时先写死 max_token = 4096，考虑字符数和 token 其实还不同，这是比较保守的数字
            for i in range(-1, -len(self.loop[user_id]["memory"])-1, -1):
                chat = self.loop[user_id]["memory"][i]
                if lens + len(chat[0]) + len(chat[1]) + 64 > 4096:
                    break
                messages.insert(1,{"role": "user", "content": chat[0]})
                messages.insert(2,{"role": "assistant", "content": chat[1]})
        messages.append({"role": "user", "content": query})
        reply = await llm(messages, model=self.llm_model)
        if not reply:
            return self.build_out(-11, speech_dict["failed"])
        flag = 0
        to_send_files = set()
        # 判断是否需要查询
        if '#search' in reply:
            self.logger.debug("need search")
            if not self.kbs:
                self.logger.debug("no knowledge base, so no search result")
                self.logger.debug(speech_dict["dissatisfied"])
                return self.build_out(0, speech_dict["dissatisfied"])

            query = clean_query(query, self.name)
            if user_id in self.loop and self.loop[user_id]["memory"]:
                flag, msg, search_result = await search(query, kb_ids=self.kbs, model=self.llm_model, wf_dir=self.wf_cache,
                                                        history=self.loop[user_id]["memory"], logger=self.logger)
            else:
                flag, msg, search_result = await search(query, kb_ids=self.kbs, model=self.llm_model, wf_dir=self.wf_cache, logger=self.logger)
            if flag == -4:
                self.logger.error(f"Qanything out of service, code:{flag}, msg:{msg}")
                return self.build_out(flag, speech_dict["failed"])
            if flag > 200:
                self.logger.warning(f"Qanything search failed, code:{flag}, msg:{msg}")
                if check_health():
                    self.logger.info("health check ok, try again")
                    flag, msg, search_result = await search(query, kb_ids=self.kbs, model=self.llm_model, wf_dir=self.wf_cache, logger=self.logger)
                    self.logger.info(f"retry result:{flag}, {msg}")
                else:
                    self.logger.error("health check failed")
                    return self.build_out(1, speech_dict["failed"])

            if not search_result:
                self.logger.debug("search but no result...")
                self.logger.debug(speech_dict["dissatisfied"])
                return self.build_out(0, speech_dict["dissatisfied"])

            documents = []
            references = set()
            for doc in search_result:
                if doc['type'] == 'faq':
                    if len(search_result) == 1:
                        reply = f"为您找到如下参考：\n\n{doc['content']}"
                        if user_id not in self.loop:
                            self.loop[user_id] = {"status": "normal", "memory": [[query, reply]], "temp": None, "last_update": time.time()}
                        else:
                            self.loop[user_id]["memory"].append([query, reply])
                        self.logger.debug(reply)
                        return self.build_out(0, reply)
                    else:
                        documents.append(f"<document>{doc['content']}</document>")
                        references.add(f"FAQ_{doc['title']}")
                elif doc['type'] == 'wiseflow':
                    documents.append(f"<document>{doc['content']}</document>")
                    if doc['title'] or doc['source']:
                        references.add(f"{doc['title']}\n{doc['source']}")
                elif doc['type'] == 'file':
                    documents.append(f"<document>{doc['content']}</document>")
                    references.add(doc['title'])
                    if doc['attachment']:
                        to_send_files.add(doc['attachment'])

            # 据说模型对首尾信息更敏感，所以要把得分高的放两端，姑且信之
            n = len(documents)
            doc_list = [None] * n
            for i in range(n):
                if i % 2 == 0:
                    doc_list[i // 2] = documents[i]
                else:
                    doc_list[-(i // 2 + 1)] = documents[i]

            rag_text = "\n\n".join(doc_list)
            self.logger.debug(rag_text)
            messages = [{"role": "system", "content": self.bot_system},
                        {"role": "user", "content": f"{user_rag_prompt_prefix}{rag_text}{user_rag_prompt_suffix.format(user_input=query)}"}]
            reply = await llm(messages, model=self.llm_model)
            if not reply:
                return self.build_out(-11, speech_dict["failed"])
            if user_id in self.loop:
                self.loop[user_id]["memory"] = []
            if references:
                refer = "参考资料：\n"
                for i, ref in enumerate(references):
                    refer = f"{refer}{i+1}. {ref}\n"
                reply = f"{reply}\n\n{refer}"

        self.logger.debug(reply)
        self.logger.debug(f"with files:{to_send_files}")
        if user_id not in self.loop:
            self.loop[user_id] = {"status": "normal", "memory": [[query, reply]], "temp": None, "last_update": time.time()}
        else:
            self.loop[user_id]["memory"].append([query, reply])

        to_send_files = list(to_send_files)
        return self.build_out(flag, reply, to_send_files)

    def build_out(self, flag: int, answer: Union[str, List[str]] = "", files: Optional[list] = None) -> dict:
        # 未来这里如果要集成更多功能，要看如果是 cPU 密集型任务那么还是维持同步函数较好，不然可以考虑改为异步
        # 如果 answer 是 str，则将其转换为单元素列表
        if isinstance(answer, str):
            answer = [answer]
        # 构建结果字典
        result = [{"type": "text", "answer": ans} for ans in answer]
        if files:
            for file in files:
                result.append({"type": "file", "answer": file})
        return {"flag": flag, "result": result}

    async def _create_new_kb(self, new_kb_name: str, for_wf: bool = False) -> bool:
        flag, new_kb_id = await create_new_kb(new_kb_name, logger=self.logger)
        if flag == 200:
            self.logger.info(f"create new kb success: {new_kb_id}")
            async with self.lock:
                self.kbs.append(new_kb_id)
                if for_wf:
                    self.wf_kb = new_kb_id
                    await self.update_config_file({"kbs": self.kbs, "wiseflow_working_kb": new_kb_id})
                else:
                    self.working_kb = new_kb_id
                    await self.update_config_file({"kbs": self.kbs, "working_kb": new_kb_id})
            return True
        return False

    async def add_file(self, input: dict) -> dict:
        if input['type'] != 'file':
            return self.build_out(-1, "wrong_input")
        user_id = input['user_id']
        query = input['content'].strip()
        self.logger.info(f"user: {user_id} apply to add file to kb:\n{query}")
        # 先检查 file 是否存在
        if not (os.path.exists(query) and os.path.isfile(query)):
            self.logger.info('文件不存在')
            return self.build_out(-1, f"{query} 文件不存在")
        if not any(query.endswith(ext) for ext in support_exts):
            self.logger.info('文件类型不支持')
            return self.build_out(2, f'{query} 文件类型不支持')

        if not self.working_kb:
            self.logger.info("no working kb set, create new kb")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            if not await self._create_new_kb(f"{self.name}_{timestamp}"):
                self.logger.error("create new kb failed")
                return self.build_out(1, f"Qanything服务异常：无法创建新数据库，请检查。\n"
                                         f"bot_id:{input['bot_id']}\n当前工作 kb_id:{self.working_kb}\n"
                                         f"未成功上传文件：{query}\n时间{timestamp}")

        code, msg = await upload_files_to_kb(self.working_kb, [query], logger=self.logger)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        if code == 200:
            if msg.startswith('warning'):
                self.logger.warning(f"upload failed, {msg}")
                return self.build_out(1, f"提醒：收到新文件，但因为文件过大，或者库中已有重名文件，导致无法存贮。\n"
                                         f"bot_id:{input['bot_id']}\n当前工作 kb_id:{self.working_kb}\n"
                                         f"未成功上传文件：{query}\n时间{timestamp}")
            return self.build_out(0, f"文件上传成功，时间{timestamp}")
        elif code == 2001 or code == 2002:
            # kb不合法或者文件数量已经超出，新建 kb 并切换 kb_id
            self.logger.warning("kb is invalid or is full, create new kb")
            if await self._create_new_kb(f"{self.name}_{timestamp}"):
                self.logger.debug(f"retry to upload {query}")
                code, msg = await upload_files_to_kb(self.working_kb, [query], logger=self.logger)
                if code != 200:
                    self.logger.error(f"upload failed, error: {msg}\n abort")
                    return self.build_out(1, f"Qanything服务异常：无法上传文件，请检查。\n"
                                             f"bot_id:{input['bot_id']}\n当前工作 kb_id:{self.working_kb}\n"
                                             f"未成功上传文件：{query}\n 时间{timestamp}")
            else:
                self.logger.error("upload failed, then try to create new kb but failed")
                return self.build_out(1, f"Qanything服务异常：无法创建新数据库导致无法上传文件，请检查。\n"
                                         f"bot_id:{input['bot_id']}\n当前工作 kb_id:{self.working_kb}\n"
                                         f"未成功上传文件：{query}\n时间{timestamp}")
        else:
            self.logger.error(f"upload failed, error: {msg}")
            return self.build_out(1, f"Qanything服务异常：无法上传文件，请检查。\n"
                                     f"bot_id:{input['bot_id']}\n当前工作 kb_id:{self.working_kb}\n"
                                     f"未成功上传文件：{query}\n 时间{timestamp}")

    async def wiseflow(self, url: str, cache: Optional[Dict[str, str]] = None):
        # 未预设 kb，则创建新的
        if not self.wf_kb:
            self.logger.info("no working kb set for workflow, create new kb")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            if not await self._create_new_kb(f"wiseflow-{self.name}_{timestamp}", for_wf=True):
                self.logger.error(f"Qanything服务异常：无法创建新数据库，请检查。\n{self.name}\n时间{timestamp}")
                return

        working_list = {url}
        est_length = len(self.existing_urls)
        while working_list:
            url = working_list.pop()
            holding = True if url in self.existing_urls else False
            async with self.lock:
                self.existing_urls.add(url)
            if any(url.endswith(ext) for ext in extensions):
                self.logger.info(f"{url} is a file, skip")
                continue
            self.logger.debug(f"start processing {url}")

            # get article process
            flag, result = await general_crawler(url, self.logger)
            if flag == 1:
                self.logger.info('get new url list, add to work list')
                new_urls = result - self.existing_urls
                working_list.update(new_urls)
                continue
            elif flag <= 0:
                self.logger.error("got article failed, pipeline abort")
                continue

            if holding:
                self.logger.debug(f"got {url} again and not site url, skip")
                continue
            if cache:
                for k, v in cache.items():
                    if v: result[k] = v

            # filter process
            # formate the title and content
            try:
                title = f"{result['author']} {result['publish_time']}\n{result['title']}"
            except KeyError:
                title = result['title']

            content = f"{title}\n\n{result['content']}"
            self.logger.debug(content)
            # use llm to filter out the useless information
            prompt = [{"role": "system", "content": self.wf_system},
                      {"role": "user", "content": f"<context>{content}</context>{wiseflow_prompt}"}]
            conclusion = await llm(prompt, model=self.wf_model)
            self.logger.debug(conclusion)
            if not conclusion:
                self.logger.error("llm failed, pipeline abort")
                continue

            to_save = False
            for i in range(min(7, len(conclusion))):
                char = conclusion[-1 - i]
                if char == '是':
                    self.logger.debug("keep this file")
                    to_save = True
                    break
                elif char == '否':
                    self.logger.debug("skip this file")
                    break
            if not to_save:
                continue

            # write to a markdown file so that it can be uploaded to the knowledge base
            files = await write_md_file(result, self.wf_cache)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            if not files:
                self.logger.error('add article failed, writing to cache_file')
                await aio_save_config(result, os.path.join(self.wf_temp, f'{title}.json'))
                self.logger.error(f"wiseflow md文件写入失败\n失败内容：{title}\n{self.name}\n时间{timestamp}")
                continue

            # upload to the knowledge base
            code, msg = await upload_files_to_kb(self.wf_kb, files, logger=self.logger)
            if code == 200:
                if msg.startswith('warning'):
                    self.logger.warning(f"upload failed, {msg}")
            elif code == 2001 or code == 2002:
                # kb不合法或者文件数量已经超出，新建 kb 并切换 kb_id
                self.logger.warning("kb is invalid or is full, create new kb")
                if await self._create_new_kb(f"wiseflow-{self.name}_{timestamp}", for_wf=True):
                    self.logger.debug(f"retry to upload {title}")
                    code, msg = await upload_files_to_kb(self.wf_kb, files, logger=self.logger)
                    if code != 200:
                        self.logger.error(f"upload failed, error: {msg}\n abort")
                        await aio_save_config(result, os.path.join(self.wf_temp, f'{title}.json'))
                else:
                    self.logger.error(f"upload failed, then try to create new kb but failed")
                    await aio_save_config(result, os.path.join(self.wf_temp, f'{title}.json'))
            else:
                self.logger.error(f"upload failed, error: {msg}, writing to cache_file")
                await aio_save_config(result, os.path.join(self.wf_temp, f'{title}.json'))

        # 将existing_urls 写入文件
        if est_length != len(self.existing_urls):
            config_bytes = pickle.dumps(self.existing_urls)
            async with self.lock:
                async with aio_open(self.existing_urls_file, 'wb') as f:
                    await f.write(config_bytes)
