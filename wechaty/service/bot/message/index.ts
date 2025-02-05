import { Message, Wechaty } from "@juzi/wechaty";
import { WechatyUi, FormatUtils } from "@/utils";
import { isUseFulMessage } from "./filter";
import { getMSG } from "./msg";
import { log } from "./log";
import config from "@/config";
import plan from "./plan";

const { directorOrders } = config;

// 消息监听回调
export const onMessage = (bot: Wechaty) => {
  return async (msg: Message) => {
    console.log("🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀 -【新消息】- 🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀");

    /** 读取消息信息 */
    const MSG = await getMSG(msg, bot);

    const { isDirectors, room, text } = MSG;

    /** 日志 */
    log(MSG);

    /* 过滤掉不需要处理的消息 & 无权限消息处理*/
    const isUseFul = await isUseFulMessage(MSG, msg);
    if (!isUseFul) {
      console.log("🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀 -【无用消息】- 🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀");
      return;
    }

    /** 群消息 */
    if (room) {
      console.log("🌰🌰🌰 群聊消息 🌰🌰🌰");

      /** 导演消息 */
      if (isDirectors) {
        const { configFileMap, configMap } = await WechatyUi.loadBotsConfig();

        const commandStr = FormatUtils.checkCommand(text);

        let commands = commandStr.split(" ").map((item) => item.trim());

        console.log("commands", commands);
        const command = commands[0];
        /** 消息指令处理 */

        /** 查看bot列表 */
        if (command === directorOrders.bot_list) {
          const botList = Object.keys(configFileMap)
            .map((botId) => `Bot ID: ${botId}`)
            .join("\n");
          await room.say(botList);
          return;
        }

        /** 把房间里的所有人提升为导演角色 */
        if (command === directorOrders.co_director) {
          await WechatyUi.promoteRoomDirectors(room);
          return;
        }

        /** start 初始化群、生成json 配置文件 */
        if (command === directorOrders.start) {
          await WechatyUi.initRoomBot(room);
          return;
        }

        /** 刷新群成员 */
        if (command === directorOrders.refresh) {
          await WechatyUi.refreshRoom(room);
          return;
        }

        /** 停止群bot服务 */
        if (command === directorOrders.stop) {
          await WechatyUi.stopRoomBot(room);
          return;
        }

        /** 为智能体添加新的 学习来源 */
        if (command === directorOrders.add_source_to) {
          if (commands.length < 2) {
            await room.say(
              `为智能体添加新的资源对象群 - 在要资源群中发送： ${directorOrders.add_source_to} <bot_id>`
            );
          } else {
            const answer = await WechatyUi.addSourceTo(room, commands[1]);
            await room.say(answer);
            return;
          }
        }

        /** 为智能体添加新的 服务者 */
        if (command == directorOrders.add_service_to) {
          if (commands.length < 2) {
            room.say(
              `为智能体添加新的服务对象群 - 在要被服务的群中发送： ${directorOrders.add_service_to} <bot_id>`
            );
            return;
          } else {
            const answer = await WechatyUi.addServiceTo(room, commands[1]);
            await room.say(answer);
            return;
          }
        }

        console.log("该群是学习源");
        plan(MSG, msg);
        return;
      }

      /** 群内问答 */
      plan(MSG, msg);
    } else {
      /** 私发消息 */
      plan(MSG, msg);
    }
  };
};
