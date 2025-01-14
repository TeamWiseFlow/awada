const path = require("path");
const fs = require("fs");
import { FileUtils, TypeUtils } from "@/utils";

export const WechatyuiPath =
  "/" + path.join(__dirname, "../database/wechatyui");
export const AvatarsPath = "/" + path.join(__dirname, "../../avatars");
export const FilesPath = "/" + path.join(__dirname, "../database/files");
export const CachePath = "/" + path.join(__dirname, "../database/cache");
export const ConfigPath = "/" + path.join(__dirname, "./");

export const DirectorsPath = "/" + path.join(__dirname, "../../directors.json");

export let MAIN_SERVICE_ENDPOINT = "http://127.0.0.1:8077";

export let staticConfig: TypeUtils.StaticConfigType = null;

/**
 * 全局配置 config.json
 */
export const init = async () => {
  console.log("🌰🌰🌰 static config init 🌰🌰🌰");
  /** 初始化全局配置信息，不用多次调取 */
  staticConfig = await FileUtils?.getStaticConfig?.();
};

const ConfigJson = "/" + path.join(__dirname, "./config.json");

console.log(`Watching for file changes on ${ConfigJson}`);

fs.watch(ConfigJson, (event, filename) => {
  if (event === "change") {
    console.log(`${filename} file Changed`);
    init();
  }
});

export const config_template = {
  bot_id: "",
  bot_org: "",
  bot_name: "",
  learn_sources: [],
  service_list: [],
  chat_model: "",
  kbs: [],
  working_kb: "",
  greeting: "",
  wiseflow_working_kb: "",
  wiseflow_focus: [],
  wiseflow_model: "",
  wiseflow_sites: [],
  topnews_shout: "",
  top_news_items: {},
  topnews_max: 5,
  topnews_scriber: [],
};
/**
 * 常量信息
 */
export default {
  /** 机器人名称 */
  name: "awada-bot",

  puppetName: "wechaty-puppet-service" as const,

  juziPuppetName: "@juzi/wechaty-puppet-service" as const,

  Apis: {
    feed: `${MAIN_SERVICE_ENDPOINT}/feed`,
    dm: `${MAIN_SERVICE_ENDPOINT}/dm`,
  } as const,

  directorOrders: {
    add_source_to: "/add_source",
    start: "/start",
    add_service_to: "/add_service",
    stop: "/stop",
    co_director: "/promotion",
    refresh: "/refresh",
    bot_list: "/list",
  },
};
