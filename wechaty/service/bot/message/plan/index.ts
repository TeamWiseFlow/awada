
import { requestPlan } from '@/service/algorithm'
import { MSGType } from '../msg'
import { Message } from "@juzi/wechaty";
import { MESSAGE_TYPE } from '@/utils/type'
import { MessageUtils, FormatUtils, isUrl } from '@/utils'
import { QueryReturnType } from '@/service/algorithm/type'
import { FilesPath, CachePath } from '@/config'
import fs from 'fs'

/**  */
export const replyMessage = async (res: QueryReturnType['contents'], msg: Message, question?: string) => {
    const files = fs.readdirSync(FilesPath)
    const room = msg.room()

    const msgSay = async (work, type?: 'file' | 'text') => {
        if (type == 'file') {
            await MessageUtils.sendFile(work, room ? room : msg)
        } else {
            room ? await room.say(`${question ? question + '\n\n' : ''}${work}`, msg.talker()) : await msg.say(work)
        }
    }

    if (typeof res === 'string') {
        msgSay(res)
    } else {
        for await (const m of res) {
            const { type, answer } = m
            // const m_text = m.text.trim()
            if (!answer) continue
            if (type === 'file') {
                await msgSay(answer.startsWith('/home/dsw') ? answer : `/home/dsw/midplatform/${answer}`, 'file')
            } else {
                await msgSay(answer)
            }
        }
    }
}

export const xlsxAction = async (MSG: MSGType, msg: Message, fileName: string) => {
    await msg.say('收到，请稍候')
    let { success, contents, flag } = await requestPlan({ user_id: MSG.talker.id, type: 'file', content: `${CachePath}/${fileName}` })
    await replyMessage(contents, msg)
    // MessageUtils.sendFile(program.text, msg)
}

/** 方案策划 */
export default async (MSG: MSGType, msg: Message) => {
    const isPlan = MSG.text.trim().startsWith('#') || MSG.text.trim().startsWith('＃')
    const { staticConfig } = MSG
    const { room_question } = staticConfig

    /** 判断是否开启群问答 */
    if (room_question === 'close' && MSG.room) return msg.say(staticConfig.room_speech.welcome)

    /** 判断是否有权限 */
    if (!MSG?.talker?.permision) return msg.say(staticConfig.person_speech.no_permission)

    if (MSG.type === MESSAGE_TYPE.文本 || MSG.type === MESSAGE_TYPE.语音) {
        if (isPlan) msg.say('收到，请稍候')

        const text = MessageUtils.formatTextMsg(MSG.text)

        console.log('plan text', text)
        // 请求机器人接口回复
        let { flag, success, contents } = await requestPlan({ user_id: MSG.talker.id, type: 'text', content: text });

        if (flag === 21 && Array.isArray(contents)) {
            const [title, program] = contents
            // contents = [title]
            await replyMessage(contents, msg, text)
            // MessageUtils.sendFile(program.text, msg)
        } else {
            await replyMessage(contents, msg, text)
        }
    }
    // else if (MSG.type === MESSAGE_TYPE.语音) {
    //     const file = await msg.toFileBox();
    //     const fileName = await MessageUtils.saveAudio(file);
    //     // 请求机器人接口回复
    //     let { contents } = await requestPlan({ user_id: MSG.talker.id, type: 'voice', content: fileName });
    //     await replyMessage(contents, msg)
    // } 
    else if (MSG.type === MESSAGE_TYPE.文件) {
        return
    } else {
        return
    }

}