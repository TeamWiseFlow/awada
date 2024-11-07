const request = require("request")
import responseHandler from './response'
import { QueryReturnType, ParamsType } from './type'
import PB from '@/utils/pb'

/* 删除文件 */
export const requestFileDelete = (info: { id: string }): Promise<QueryReturnType> => {
    return new Promise(async (resolve, reject) => {
        const res = await PB.deleteFile(info.id)
        console.log('requestFileDelete', res)
        resolve(res)
    })
}