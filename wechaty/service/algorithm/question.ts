const request = require("request")
import responseHandler from './response'
import { QueryReturnType, ParamsType } from './type'
import CONFIG, { staticConfig } from '@/config'

/* 机器人请求算法接口 处理函数 */
export const requestQuestion = (info: ParamsType): Promise<QueryReturnType> => {
    if (process.env.mode === 'local') {
        return new Promise((resolve, reject) => {
            resolve({ success: false, flag: 999, contents: [{ text: '等一下，主人没连服务器' }] })
        })
    }
    return new Promise((resolve, reject) => {
        let url = CONFIG.Apis.callAgent
        request({ url, method: 'POST', body: JSON.stringify(info) }, async (...params: [any, any, any]) => {
            const res = await responseHandler(...params)
            resolve({
                flag: res.flag,
                success: true,
                contents: res.contents.length > 0 ? res.contents : staticConfig?.request_speech.ask_noanswer
            })
        })
    })
}