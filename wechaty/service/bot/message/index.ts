import { Message, Wechaty } from "@juzi/wechaty";
import { WechatyUi, BotUtils, FormatUtils } from "@/utils";
import { isUseFulMessage } from './filter'
import { getMSG } from './msg'
import { log } from './log'
import personMessage from './person'
import wechatyUi from "@/utils/wechaty-ui";
import Plan from './plan'

// 消息监听回调
export const onMessage = (bot: Wechaty) => {
  return async (msg: Message) => {
    console.log("🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀 -【新消息】- 🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀");
    /** 读取消息信息 */
    const MSG = await getMSG(msg, bot)

    const { talker, isDirectors, room, text, staticConfig } = MSG
    const { room_question } = staticConfig

    /** 日志 */
    log(MSG)

    /* 过滤掉不需要处理的消息 & 无权限消息处理*/
    const isUseFul = await isUseFulMessage(MSG, msg)
    if (!isUseFul) return

    /** 群消息 */
    if (room) {
      console.log('🌰🌰🌰 群聊消息 🌰🌰🌰')

      /** 导演消息 */
      if (isDirectors) {
        const command = FormatUtils.checkCommand(text)
        const { start, stop, talking, update, list } = MSG.command

        /** 消息指令处理 */
        if (command === list) {
          return;
          // commandList(msg)
        } else if (command === update) {
          await WechatyUi.updateRoomUsers(room, 'update');
          // 返回欢迎语
          await room.say(staticConfig.room_speech.update)
        } else if (command === start) {
          await WechatyUi.updateRoomUsers(room, 'update');
          // 返回欢迎语
          await room.say(staticConfig.room_speech.start);
          const noAliasUser = await WechatyUi.getNoAliasUserId(room)
          //3、检查是否群成员都设定群昵称
          if (noAliasUser && noAliasUser.length > 0) {
            //   没设定的要在群聊里面@提醒
            await room.say(staticConfig.room_speech.modify_remarks, ...noAliasUser)
          }
        } else if (command === stop) {
          await WechatyUi.updateRoomUsers(room, 'delete');
          // 返回消息，并@来自人
          room.say(staticConfig.room_speech.stop)
          BotUtils.sendMessage(staticConfig.person_speech.room_stop, {
            type: "user",
            id: talker.id,
          });
          await wechatyUi.updateConfig('room_question', 'close')
        } else if (command === talking) {
          console.log('room_question', room_question)
          const newMode = room_question === 'open' ? 'close' : 'open'
          const returnMsg = newMode === 'close' ? staticConfig.room_speech.stop_talking : staticConfig.room_speech.open_talking
          room.say(returnMsg)
          await wechatyUi.updateConfig('room_question', newMode)
        } else {
          /** 群内问答 */
          if (room_question === 'open') {
            Plan(MSG, msg)
            // SmartQa(MSG, msg)
            return
          } else {
            room.say(staticConfig.room_speech.no_talking)
          }
        }
      } else {
        /** 群内问答 */
        if (room_question === 'open') {
          Plan(MSG, msg)
          // SmartQa(MSG, msg)
          return
        } else {
          room.say(staticConfig.room_speech.no_talking)
        }
      }
    } else {
      /** 私发消息 */
      personMessage(MSG, msg)
    }
  }
};
