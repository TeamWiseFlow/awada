
import { requestDm, requestFeed } from '@/service/algorithm'
import { MSGType } from '../msg'
import { Message } from "@juzi/wechaty";
import { MESSAGE_TYPE } from '@/utils/type'
import { MessageUtils, WechatyUi } from '@/utils'
import { QueryReturnType } from '@/service/algorithm/type'
import { FilesPath} from '@/config'
import fs from 'fs'

/** 回复消息 */
export const replyMessage = async (res: QueryReturnType['contents'], msg: Message, question?: string) => {
    const room = msg.room()

    const msgSay = async (work, type?: 'file' | 'text') => {
        if (type == 'file') {
            await MessageUtils.sendFile(work, room ? room : msg)
        } else {
            console.log('question',{question,work})
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

/** 聊天消息处理 */
export default async (MSG: MSGType, msg: Message) => {
    const isPlan = MSG.text.trim().startsWith('#') || MSG.text.trim().startsWith('＃')
    const {learnSourcesMap } = await WechatyUi.loadBotsConfig()
    console.log('learnSourcesMap', learnSourcesMap)

    console.log('talkerId learn_sources', learnSourcesMap[MSG.talker.id])
    const roomId = MSG.room?.id 
    /** 判断是否开启群问答 */
    if (MSG.type === MESSAGE_TYPE.文本 || MSG.type === MESSAGE_TYPE.语音) {
        if (isPlan) msg.say('收到，请稍候')

        const text = MessageUtils.formatTextMsg(MSG.text)

        console.log('plan text', text)
        // 请求机器人接口回复
        let { flag, success, contents } = await requestDm({ user_id: MSG.talker.id, type: 'text', content: text });

        console.log('contents', contents)
        if (flag === 21 && Array.isArray(contents)) {
            const [title, program] = contents
            // contents = [title]
            await replyMessage(contents, msg, text)
            // MessageUtils.sendFile(program.text, msg)
        } else {
            await replyMessage(contents, msg, text)
        }
    }
    else if (MSG.type === MESSAGE_TYPE.文件 && roomId) {
        let fileName = "";
        let file = null;
        file = await msg.toFileBox();
        fileName = file.name;
        console.log("fileName", fileName);
        await MessageUtils.saveImage(file, "files");
      
        console.log('收到一个文件', fileName)
        requestFeed({ user_id: MSG.talker.id, type: 'file', content: `${FilesPath}/${fileName}`, bot_id: learnSourcesMap[roomId]  })
        return
    } else if (MSG.type === MESSAGE_TYPE.链接 && roomId) {
        const urlLink = await msg.toUrlLink()
        const url = urlLink.url()
        console.log('content', urlLink.url)
        requestFeed({ user_id: MSG.talker.id, type: 'url', content: url, bot_id: learnSourcesMap[roomId] })
        return
    }

}