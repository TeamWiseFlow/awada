import { MSGType } from './msg'

/** 控制台log信息 */
export const log = (msg: MSGType) => {
    console.log("from", msg?.talker);
    console.log('isDirectors', msg?.isDirectors);
    console.log('roomPermission', msg?.roomPermission);
    // console.log('mentionList', msg?.mention?.acountList?.map((a) => a.name()));
    // console.log("mentionSelf", msg?.mention?.self);
    console.log('text', msg?.text);
    console.log("msgType", msg?.type);
    console.log('roomId', msg?.room?.id)
    console.log('roomName', msg?.roomName)
    console.log('msg.mentionText()', msg?.mention?.text);
}