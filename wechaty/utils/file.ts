import fs from "fs";
import JSON5 from 'json5'
import { RoomUsersType, StaticConfigType } from './type'
import { WechatyuiPath, FilesPath, ConfigPath } from '@/config'

// 遍历读取文件
export const readFile = (path: string, fileList: any[]) => {
  var files = fs.readdirSync(path);
  var work = function (file) {
    var states = fs.statSync(path + "/" + file);
    if (states.isDirectory()) {
      readFile(path + "/" + file, fileList);
    } else {
      // 创建一个对象保存信息
      let obj: any = {};
      obj.size = states.size;
      obj.name = file;
      obj.path = path + "/" + file;
      fileList.push(obj);
    }
  };
  files.forEach(work);
};

// 获取文件夹下所有文件
export const getFileList = (
  type: 'file' | 'config' | 'audio' | 'custom',
  path?: string,
): { size: number; name: string; path: string }[] => {
  const pathConfig = {
    file: FilesPath,
    config: WechatyuiPath,
    audio: FilesPath,
    custom: path || ''
  }
  var fileList = [];
  readFile(pathConfig[type], fileList);
  return fileList;
};

/** 获取项目全局配置 config.json */
export const getStaticConfig = async (): Promise<StaticConfigType> => {
  const res = await fs.readFileSync(
    `${ConfigPath}/config.json`,
    "utf-8"
  )

  let configValues = {}
  /** 对 ${} 进行匹配替换，只能匹配 ${a.b} 类型 */
  const result = JSON5.parse(res, (key, value) => {
    let newValue = value
    configValues[key] = value

    if (typeof value === 'string') {
      const match = newValue.match(/\$\{.*?\}/g)
      if (!match || match.length === 0) return newValue

      match.map((m: string) => {
        const fields = m.match(/\$\{(\S*)\}/)[1]?.trim().split('.')
        if (!fields || fields.length === 0) return

        const fieldValue = fields.reduce((pre, next) => {
          return pre[next]
        }, configValues)

        newValue = newValue.replace(m, fieldValue)
      })
    }
    return newValue
  })

  return result
}


/** 删除文件 */
export const removeFile = (fileName: string, type: 'file' | 'config') => {
  const prePath = type === 'config' ? WechatyuiPath : FilesPath
  fs.unlink(`${prePath}/${fileName}`, (err) => {
    if (err) {
      return console.error(err);
    }
    console.log(`【${fileName}】该文件删除成功`)
  })
}

/** 清空 database/files下的所有文件 */
export const removeAllDatabaseFiles = () => {
  fs.unlinkSync(`${FilesPath}`)
  fs.mkdirSync(FilesPath)
}

export default {
  readFile,
  getFileList,
  removeFile,
  getStaticConfig,
};
