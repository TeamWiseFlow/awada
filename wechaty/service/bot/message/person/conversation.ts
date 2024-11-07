import dayjs from 'dayjs'
import { ConversationConfigType, ConversationUserConfigType } from './const'

let ConversationConfig: ConversationConfigType = {}

// 重置对话轮次
export const resetConfig = () => {
    ConversationConfig = {}
}

// 重置用户对话轮次
export const resetTalkerConfig = (id: string, config?: ConversationUserConfigType) => {
    ConversationConfig[id] = {
        status: '无对话轮次',
        fileName: null,
        lastTime: dayjs().toString(),
        ...config || {}
    }
}

export default {
    config: ConversationConfig,
    resetConfig,
    resetTalkerConfig,
}
