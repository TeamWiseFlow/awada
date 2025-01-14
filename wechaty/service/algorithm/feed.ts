const request = require("request")
import responseHandler from './response'
import { QueryReturnType, ParamsType } from './type'
import CONFIG, { staticConfig } from '@/config'

const CONTENTMOCKS = [
    {
        answer: `文件就收到了，主人正在处理中`
    }
]
/* 方案策划请求 */
export const requestFeed = (info: ParamsType): Promise<QueryReturnType> => {
    console.log('----feed',info)

    if (process.env.mode === 'local') {
        return new Promise((resolve, reject) => {
            resolve({ success: true, flag: 999, contents: CONTENTMOCKS || [{ text: '等一下，主人没连服务器' }] })
        })
    }
    return new Promise((resolve, reject) => {
        let url = CONFIG.Apis.feed
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