import { MSGType } from "./msg";
import { staticConfig } from "../../../config";
import { Message } from "@juzi/wechaty";
import { FormatUtils, TypeUtils, SensitivesUtils } from "@/utils";
import { Hello } from "../friendship";
const MESSAGE_TYPE = TypeUtils.MESSAGE_TYPE;

/** 判断消息是否处理 */
export const isUseFulMessage = async (MSG: MSGType, msg: Message) => {
  const userHello = Hello().get(msg.talker().id);

  console.log("userHello - filter", userHello);
  // 判断是否为打招呼信息
  if (MSG.type === MESSAGE_TYPE.文本 && MSG?.text === userHello) {
    Hello().remove(msg.talker().id);
    return false;
  }

  if (MSG?.text === "我通过了你的联系人验证请求，现在我们可以开始聊天了")
    return false;

  // 其他类型消息：新用户进群
  if (MSG?.type === MESSAGE_TYPE.未知) return false;

  // 表情包
  if (MSG?.type === MESSAGE_TYPE.表情符号) return false;

  // 微信官方发送的消息
  if (msg?.talker()?.id === "weixin") return false;

  // 加好友之后好友发送的通知
  if (MSG?.type === MESSAGE_TYPE.添加用户成功消息) return false;

  // 判断消息来自自己，直接return
  if (MSG?.isSelf) return false;

  // 不当言论检测
  if (MSG.type === MESSAGE_TYPE.文本 && SensitivesUtils.find(MSG.text)) {
    msg.say(staticConfig.common_speech.bad_words);
    return false;
  }

  // 聊天群没有权限
  if (MSG?.room) {
    // 未授权群
    if (!MSG?.roomPermission) {
      const command = FormatUtils.checkCommand(MSG.text);
      if (command === MSG.command.start) return true;
      if (command === MSG.command.update) return true;
      if (command === MSG.command.stop || command === MSG.command.talking) {
        if (MSG.isDirectors) {
          msg.say(staticConfig.room_speech.no_permission);
        } else {
          msg.say(staticConfig.room_speech.stop);
        }
      }

      return false;
    }
    /** 群内无导演 */
    if (!(MSG?.roomDirectors.length > 0)) return false;

    // 授权群内未 AT 消息
    if (!MSG?.mention.self) return false;

    // 授权群内 AT 多人消息
    if (MSG?.mention.acountList.length > 1) return false;
  }

  // 个人消息没有权限
  if (!MSG?.room && !MSG?.talker?.permision) {
    msg.say(staticConfig.person_speech.no_permission);
    return false;
  }

  return true;
};
