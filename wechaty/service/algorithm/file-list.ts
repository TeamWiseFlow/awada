const request = require("request")
import responseHandler from './response'
import { QueryReturnType, ParamsType } from './type'
import CONFIG, { staticConfig } from '@/config'
import PB from '@/utils/pb'

type ReturnType = {
    success: boolean,
    flag: number,
    // contents: string | { type: "text" | "file", answer: string }[]
    contents: { id: string, filename: string }[]
}
/* 查询文件列表 */
export const requestFileList = async (info: ParamsType): Promise<ReturnType> => {

    const res = await PB.getFiles()
    return res

}