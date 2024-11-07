import { MSGType } from '../msg'
import { Message } from "@juzi/wechaty";
import { staticConfig } from '@/config'
import { FormatUtils } from '@/utils'
import { requestFileList } from '@/service/algorithm'
import Conversation from './conversation'
import { replyMessage } from '../smartqa'

/** 导演指令【#list】文件列表查询 */
export const commandList = async (msg: Message) => {
    const room = msg.room()
    const { success, contents } = await requestFileList({ user_id: msg.id, type: 'text', content: '#list' })
    if (!success) {
        await replyMessage(contents, msg)
        return []
    }

    /** 未查找到任何文件 */
    if (typeof contents === 'object' && contents.length === 0) {
        await msg.say(staticConfig.common_speech.file_list_none)
        return []
    }

    let replayContent = staticConfig.common_speech.file_list

    const fileList = contents?.map((item, index) => `${index + 1}、${item.filename}`).join('\n')
    replayContent += `\n\n${fileList}`
    if (!room)
        replayContent += `\n\n${staticConfig.common_speech.file_delete}`
    if (room) {
        await room.say(replayContent, msg.talker())
    } else {
        await msg.say(replayContent)
    }
    return contents
}

/** 导演指令 */
export default async (MSG: MSGType, msg: Message) => {
    const { directors_order } = staticConfig
    console.log('🌰🌰🌰 导演指令 🌰🌰🌰')
    const command = FormatUtils.checkCommand(MSG.text)
    return;
}