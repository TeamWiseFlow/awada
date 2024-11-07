import { MSGType } from "./msg";
import { Message } from "@juzi/wechaty";
import { MessageUtils } from "@/utils";
import { requestQuestion } from "@/service/algorithm";
import { MESSAGE_TYPE } from "@/utils/type";
import { QueryReturnType } from "@/service/algorithm/type";

/** smartQa 智能问答模块 */
export const replyMessage = async (res: QueryReturnType["contents"], msg) => {
  if (typeof res === "string") {
    msg.say(res);
  } else {
    for await (const m of res) {
      await msg.say(m.text);
    }
  }
};

export default async (MSG: MSGType, msg: Message) => {
  const { staticConfig } = MSG;
  const { room_question } = staticConfig;

  /** 判断是否开启群问答 */
  if (room_question === "close" && MSG.room)
    return msg.say(staticConfig.room_speech.welcome);

  /** 判断是否有权限 */
  if (!MSG?.talker?.permision)
    return msg.say(staticConfig.person_speech.no_permission);

  if (MSG.type === MESSAGE_TYPE.文本 || MSG.type === MESSAGE_TYPE.语音) {
    const text = MessageUtils.formatTextMsg(MSG.text);
    // 请求机器人接口回复
    let { contents } = await requestQuestion({
      user_id: MSG.talker.id,
      type: "text",
      content: text,
    });
    await replyMessage(contents, msg);
  }
};
