const request = require("request")
import responseHandler from './response'
import { QueryReturnType, ParamsType } from './type'
import CONFIG, { staticConfig } from '@/config'

const CONTENTMOCKS = [
    {
        text: `【活动主题】 六一儿童节快乐！

        【一、服务背景】
        为了让孩子们度过一个愉快的节日，同时增强社区的凝聚力，我们计划在社区开展一系列的活动，其中包括庆祝六一儿童节。
        
        【二、服务目标】
        1. 通过此次活动，增进社区居民之间的友谊和互动。
        2. 给孩子们提供一个展示自己才艺的机会，让他们感受到自己的价值和重要性。
        3. 通过活动，让社区居民了解儿童节的重要性和意义。
        
        【三、参与对象】
        社区内所有孩子和家长均可参与活动。
        
        【四、服务时间及地点】
        活动时间：2021年6月1日（周六）上午10点至下午4点。
        活动地点：社区广场。
        
        【五、服务具体内容】
        1. 活动分为儿童才艺表演环节和游戏互动环节两个部分。
        2. 儿童才艺表演环节包括歌舞、朗诵、小品等形式，孩子们可以自愿报名参加。家长可以在现场观看孩子们的表演并提供鼓励和支持。
        3. 游戏互动环节包括猜谜语、跳绳、踢毽子等游戏，孩子们和家长可以一起参与。
        4. 活动结束后，我们将评选出最佳才艺表演家庭和最佳表现家庭。
        5. 活动结束后，我们将为参与者提供一些小礼品作为纪念。`
    }
]
/* 方案策划请求 */
export const requestPlan = (info: ParamsType): Promise<QueryReturnType> => {
    if (process.env.mode === 'local') {
        return new Promise((resolve, reject) => {
            resolve({ success: true, flag: 999, contents: CONTENTMOCKS || [{ text: '等一下，主人没连服务器' }] })
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