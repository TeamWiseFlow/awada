import fs from "fs";
import { FileBox, FileBoxInterface } from "file-box";
import { Message, Wechaty, types, Room } from "@juzi/wechaty";
import { FileUtils } from "@/utils";
import { FilesPath, ConfigPath, CachePath } from "@/config";

/** 处理文本消息格式 */
export const formatTextMsg = (text: string) => {
  /**
   * 换行替换为中文逗号
   * 去掉两头的空字符
   * 处理引用信息
   */
  let textPro = text;
  const textArr = textPro.trim().split("\n- - - - - - - - - - - - - - -\n");
  if (textArr.length === 1) {
    textPro = textArr[0]?.replaceAll("\n", "，").trim();
  } else {
    const quoteText = textArr[0]
      ?.replaceAll('"', "")
      .split(":")?.[1]
      ?.replaceAll("\n", "，")
      ?.trim();
    const msgText = textArr[textArr.length - 1]?.replaceAll("\n", "，").trim();
    textPro = quoteText + "，" + msgText;
  }
  return textPro;
};

/** 保存图片到本地 */
const saveImage = async (
  data: FileBoxInterface,
  type?: "cache" | "files"
): Promise<string> => {
  const base64Data = (await data.toBase64()).replace(
    /^data:image\/png;base64,/,
    ""
  );
  const binaryData = Buffer.from(base64Data, "base64").toString("binary");

  const filePath = `${type === "cache" ? CachePath : FilesPath}/${data.name}`;
  console.log("filePath", filePath);
  fs.writeFile(filePath, binaryData, "binary", (err) => {
    if (err) {
      console.log(err); // writes out file without error, but it's not a valid image
    }
    console.log("文件保存成功！");
  });
  return filePath;
};

/** 保存文件到本地 */
const saveFile = async (
  data: FileBoxInterface,
  type?: "cache"
): Promise<string> => {
  const base64Data = await data.toBase64();
  const binaryData = Buffer.from(base64Data, "base64").toString("binary");

  const filePath = `${type === "cache" ? CachePath : FilesPath}/${data.name}`;
  fs.writeFile(filePath, binaryData, "binary", (err) => {
    if (err) {
      console.log(err); // writes out file without error, but it's not a valid image
    }
    console.log("文件保存成功！");
  });
  return filePath;
};

/** 保存文本消息为txt文件到本地 */
const saveTxt = (data: string, title: string): string => {
  const filePath = `${FilesPath}/${title}.txt`;
  fs.writeFile(`${FilesPath}/${title}.txt`, data, function (err) {
    if (err) {
      return console.error(err);
    }
    console.log("数据写入成功！");
  });
  return filePath;
};

/** 保存语音到本地 */
const saveAudio = async (file: FileBoxInterface) => {
  const filePath = `${FilesPath}/${file.name}`;
  await file.toFile(filePath);
  return filePath;
};

/** 发送语音消息 */
const sendAudio = async (path: string, msg: Message) => {
  const fileList = FileUtils.getFileList("audio");

  const fileBox = FileBox.fromFile(`${FilesPath}/${path}`);
  fileBox.metadata = {
    voiceLength: 3000,
  };
  await msg.say(fileBox);
};

/** 发送文件消息 */
const sendFile = async (path: string, msg: Message | Room) => {
  console.log("send file path", path);
  const fileBox = FileBox.fromFile(path);

  await msg.say(fileBox);
};

export default {
  formatTextMsg,
  saveImage,
  saveFile,
  saveAudio,
  sendAudio,
  saveTxt,
  sendFile,
};
