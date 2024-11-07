const path = require('path')
const fs = require('fs')
import { FileUtils, TypeUtils } from '@/utils'

export const WechatyuiPath = '/' + path.join(__dirname, "../database/wechatyui");
export const FilesPath = '/' + path.join(__dirname, "../database/files");
export const CachePath = '/' + path.join(__dirname,"../database/cache")
export const ConfigPath = '/' + path.join(__dirname, "./");

export let staticConfig: TypeUtils.StaticConfigType = null

/**
 * 全局配置 config.json
 */
export const init = async () => {
  console.log('🌰🌰🌰 static config init 🌰🌰🌰')
  /** 初始化全局配置信息，不用多次调取 */
  staticConfig = await FileUtils?.getStaticConfig?.()
}

const ConfigJson = '/' + path.join(__dirname, "./config.json");

console.log(`Watching for file changes on ${ConfigJson}`);

fs.watch(ConfigJson, (event, filename) => {
  if (event === 'change') {
    console.log(`${filename} file Changed`);
    init()
  }
});


/**
 * 常量信息
 */
export default {
  /** 机器人名称 */
  name: "wechaty-ts-bot",

  puppetName: "wechaty-puppet-service" as const,

  juziPuppetName: "@juzi/wechaty-puppet-service" as const,

  /** 默认导演 */  
  defaultDirectorId : "7881301783996424" ,

  Apis: {
    fileList: 'http://127.0.0.1:8000/api/ai/v1/scholar/list',
    fileAdd: "http://127.0.0.1:8000/api/ai/v1/scholar/add",
    fileDelete: "http://127.0.0.1:8000/api/ai/v1/scholar/delete",
    smartQa: "http://127.0.0.1:8000/api/ai/v1/scholar/ask",
    callAgent: "http://127.0.0.1:7777/dm",
  } as const
};