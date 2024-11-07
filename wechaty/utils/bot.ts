import { bot } from "@/src/index";
import { FileBox, FileBoxInterface } from "file-box";

type SendMessageProps = (
  text: string,
  config: { type: "user" | "room"; id: string },
  messageType?: 'text' | 'file'
) => {};

/** 机器人主动发送消息 */
const sendMessage: SendMessageProps = async (text: string, { type, id }, messageType) => {
  if (type === "room") {
    const room = await bot.Room.find({
      id: id,
    });
    // 1. Send text inside Room
    if (!messageType || messageType === 'text')
      await room.say(text);
  } else if (type === "user") {
    const user = await bot.Contact.find({
      id: id,
    });
    // 1. Send text to User
    if (!messageType || messageType === 'text') {
      await user.say(text);
    }else if(messageType === 'file') {
      const fileBox = FileBox.fromFile(text);
      await user.say(fileBox)
    } 

  }
};

export default {
  sendMessage,
};
