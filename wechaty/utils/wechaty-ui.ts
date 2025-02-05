import fs from "fs";
import JSON5 from "json5";
import { Room, Contact, log } from "@juzi/wechaty";
import {
  ConfigPath,
  config_template,
  AvatarsPath,
  DirectorsPath,
} from "@/config";
import path from "path";

/** 获取导演列表 */
export const loadDirectors = async () => {
  let directors = [];
  if (fs.existsSync(DirectorsPath)) {
    directors = JSON.parse(fs.readFileSync(DirectorsPath, "utf-8"));
  }
  console.log("directors", directors);
  return directors;
};

/** 获取所有bot 配置文件 */
export const loadBotsConfig = async () => {
  const botsList = [];
  const serviceUserList = [];
  const configFileMap = {};
  const configMap = {};
  const learnSourcesMap = {};
  const serviceListMap = {};
  const configFiles = fs
    .readdirSync(AvatarsPath)
    .filter((file) => file.endsWith(".json"));
  configFiles.forEach((file) => {
    const configFile = path.join(AvatarsPath, file);
    const config = JSON.parse(fs.readFileSync(configFile, "utf-8"));
    const botId = config.bot_id || "default";
    botsList.push(botId);
    configFileMap[botId] = configFile;
    configMap[botId] = config;
    config.learn_sources.forEach((source) => (learnSourcesMap[source] = botId));
    serviceUserList.push(...config.service_list);
    config.service_list.forEach((service) => (serviceListMap[service] = botId));
  });
  return {
    botsList,
    serviceUserList,
    configFileMap,
    configMap,
    learnSourcesMap,
    serviceListMap,
  };
};

/** 判断是否为管理员 */
export const isDirectors = async (id: string): Promise<boolean> => {
  const directors = await loadDirectors();
  return directors.includes(id);
};

/** 把房间里的所有人提升为导演角色 */
export const promoteRoomDirectors = async (room: Room) => {
  const members = await room.memberAll();
  const directors = await loadDirectors();
  const newDirectors = [...directors, ...members.map((m) => m.id)];
  const uniqueDirectors = new Set(newDirectors);
  fs.writeFileSync(
    DirectorsPath,
    JSON.stringify(Array.from(uniqueDirectors), null, 2)
  );
  room.say("已将群内所有人提升为导演");
};

/** 初始化一个群，将该群保存为一个agent，生成配置文件 */
export const initRoomBot = async (room: Room) => {
  const { configMap } = await loadBotsConfig();
  const roomId = room.id;
  if (configMap[roomId]) {
    log.info(`Bot already exists for room ${roomId}`);
    room.say("该群已存在机器人");
    return;
  }

  const allMembers = await room.memberAll();
  const config = {
    ...config_template,
    bot_id: roomId,
    learn_sources: [roomId],
    service_list: [roomId, ...allMembers.map((m) => m.id)],
  };

  const newBotConfigPath = path.join(AvatarsPath, `${roomId}.json`);
  fs.writeFileSync(newBotConfigPath, JSON.stringify(config, null, 2));
  log.info(`Created bot for room ${roomId}`);
  room.say("已为该群创建机器人");
};

/** 更新当前 bot 群的群成员 Refresh room members */
export async function refreshRoom(room: Room) {
  console.log("🌰🌰🌰 refreshRoom👇 🌰🌰🌰");
  const { serviceListMap, configFileMap } = await loadBotsConfig();
  const roomId = room.id;
  let members = await room.memberAll();

  const membersIds = members.map((member) => member.id);
  const botId = serviceListMap[roomId];
  console.log("botId", botId);

  if (botId) {
    const config = JSON.parse(fs.readFileSync(configFileMap[botId], "utf-8"));
    config.service_list = Array.from(new Set([...membersIds]));
    fs.writeFileSync(configFileMap[botId], JSON.stringify(config, null, 2));
    room.say("已刷新群成员");
    log.info(`Refreshed members of ${roomId} for bot ${botId}`);
  }
}

/** 停用 群bot */
export async function stopRoomBot(room: Room) {
  const roomId = room.id;
  /** 如果该文件存在 */
  if (fs.existsSync(path.join(AvatarsPath, `${roomId}.json`))) {
    fs.unlinkSync(path.join(AvatarsPath, `${roomId}.json`));
    room.say(
      "已将该群从所有学习源中取消，同时该群以及所有成员从服务清单中移除，对应的 bot 也已解除关联"
    );
  } else {
    log.info(`Bot for room ${roomId} does not exist`);
    room.say("该群不存在机器人");
  }
}

/** 获取权限用户列表 */
export const getPermissionUsers = async (id?: number | string) => {
  const directors = await loadDirectors();
  const { serviceUserList } = await loadBotsConfig();

  const userInfo = {
    users: serviceUserList || [],
    permission: id
      ? serviceUserList.includes(id) || directors.includes(id as string)
      : false,
  };
  return userInfo;
};

/** 获取权限群 */
export const getPermissionRoom = async (id?: number | string) => {
  const { botsList } = await loadBotsConfig();

  const userInfo = {
    rooms: botsList || [],
    permission: id ? botsList.includes(id) : false,
  };
  return userInfo;
};

/** 为群添加学习源 */
export async function addSourceTo(room: Room, bot_id: string): Promise<string> {
  const { configFileMap, learnSourcesMap } = await loadBotsConfig();

  const room_id = room.id;
  // 检查机器人配置文件是否存在
  if (!(bot_id in configFileMap)) {
    return `未找到对应 ${bot_id} 的机器人配置文件，请先创建该机器人配置文件，再添加学习源`;
  }

  // 检查聊天室是否已被其他机器人添加为学习源
  if (room_id in learnSourcesMap && learnSourcesMap[room_id] !== bot_id) {
    return `${room_id} 已经被 ${learnSourcesMap[room_id]} 添加为学习源，无法再次添加`;
  }

  // 检查聊天室是否已被当前机器人添加为学习源
  if (room_id in learnSourcesMap && learnSourcesMap[room_id] === bot_id) {
    return `${room_id} 已经被 ${bot_id} 添加为学习源，无需重复添加`;
  }

  // 加载机器人配置
  const config = configFileMap[bot_id];
  if (!config || !config.learn_sources) {
    return `智能体 ${bot_id} 配置文件异常，请检查后再操作`;
  }

  // 更新配置
  config.learn_sources.push(room_id);

  if (configFileMap[bot_id] && configFileMap[bot_id].endsWith(".json")) {
    fs.writeFileSync(configFileMap[bot_id], JSON.stringify(config, null, 2));
  } else {
    return;
  }

  return `已为 ${room_id} 添加到 ${bot_id} 的学习源，${bot_id} 将会主动学习该群聊信息`;
}

export async function addServiceTo(
  room: Room,
  bot_id: string
): Promise<string> {
  const { configFileMap, serviceListMap } = await loadBotsConfig();

  const room_id = room.id;
  // 检查机器人配置文件是否存在
  if (!(bot_id in configFileMap)) {
    return `未找到对应 ${bot_id} 的机器人配置文件，请先创建该机器人配置文件，再添加服务对象`;
  }

  // 检查聊天室是否已被其他机器人添加为服务对象
  if (room_id in serviceListMap && serviceListMap[room_id] !== bot_id) {
    return `${room_id} 已经被 ${serviceListMap[room_id]} 添加为服务对象，无法再次添加`;
  }

  // 检查聊天室是否已被当前机器人添加为服务对象
  if (room_id in serviceListMap && serviceListMap[room_id] === bot_id) {
    return `${room_id} 已经被 ${bot_id} 添加为服务对象，无需重复添加`;
  }

  // 加载机器人配置
  const config = configFileMap[bot_id];

  if (!config) {
    return `智能体 ${bot_id} 配置文件异常，请检查后再操作`;
  }

  // 更新配置
  if (!config.service_list) {
    config.service_list = [];
  }

  // 如果是群聊，添加所有成员
  if (room_id.endsWith("@chatroom")) {
    if (room) {
      const members = await room.memberAll();
      const memberIds = members.map((member) => member.id);
      config.service_list.push(...memberIds, room_id);
    }
  } else {
    config.service_list.push(room_id);
  }

  // 去重
  config.service_list = Array.from(new Set(config.service_list));

  // 保存配置
  if (configFileMap[bot_id] && configFileMap[bot_id].endsWith(".json")) {
    fs.writeFileSync(configFileMap[bot_id], JSON.stringify(config, null, 2));
  } else {
    return;
  }

  return `已将贵群内所有成员添加到 ${bot_id} 的服务清单。`;
}

/** 更新全局 config.json 配置 */
export const updateConfig = async (key: string, value: string) => {
  const res = fs.readFileSync(`${ConfigPath}/config.json`, "utf-8");
  const newConfig = JSON5.parse(res);
  newConfig[key] = value;

  fs.writeFileSync(
    `${ConfigPath}/config.json`,
    JSON.stringify(newConfig, null, "\t")
  );
};
