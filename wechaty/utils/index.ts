export * as WechatyUi from "./wechaty-ui";
export { default as MessageUtils } from "./message";
export { default as FileUtils } from "./file";
export { default as BotUtils } from "./bot";
export * as FormatUtils from "./format";
export * as NormalchatUtils from "./normalchat";
export * as SensitivesUtils from "./sensitive";
export * as TypeUtils from "./type";

export const isUrl = (text: string) => {
  return text.startsWith("https://") || text.startsWith("http://");
};
