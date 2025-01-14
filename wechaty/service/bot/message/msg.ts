import { Message, Wechaty, WechatyBuilder } from "@juzi/wechaty";
import { WechatyUi, FormatUtils } from "@/utils";
import { staticConfig } from "@/config";

export const getMSG = async (msg: Message, bot: Wechaty) => {
  if (!msg) return {};
  const botName = bot.currentUser.name();
  const mentionText = await msg?.mentionText();
  const formatText = FormatUtils.formatText(mentionText);
  const roomName = await msg?.room()?.topic?.();

  return {
    bot: {
      name: botName,
    },
    say: msg?.say,
    isSelf: msg?.self(), // 消息来自自己
    text: formatText, // 消息内容
    type: msg?.type(), // 消息类型
    room: msg?.room(),
    roomName: roomName,
    roomPermission: (await WechatyUi.getPermissionRoom(msg?.room()?.id))
      .permission, // 群聊权限,
    isDirectors: await WechatyUi.isDirectors(msg?.talker()?.id), // 是否为导演
    mention: {
      acountList: await msg?.mentionList(), // 提及用户列表
      text: formatText,
      self: await msg?.mentionSelf(), // 是否提及自己
    },
    talker: {
      name: msg?.talker()?.name(), // 发消息人名字
      id: msg?.talker()?.id, // 发消息人id
      permision: (await WechatyUi.getPermissionUsers(msg?.talker()?.id))
        .permission,
    },
    staticConfig: {
        ...staticConfig,
        person_speech: {
            ...staticConfig.person_speech,
        }
    }
  } as const;
};

type MyAwaited<T extends Promise<unknown>> = T extends Promise<infer U>
  ? U extends Promise<unknown>
    ? MyAwaited<U>
    : U
  : never;

export type MSGType = MyAwaited<ReturnType<typeof getMSG>>;
