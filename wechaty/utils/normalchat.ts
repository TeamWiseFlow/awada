const path = require('path')
const fs = require('fs')

const normalChatPath = '/' + path.join(__dirname, '../config/normal_chat.txt')

let map: string[] = []

const init = () => {
    const normalChat: string = fs.readFileSync(
        normalChatPath,
        "utf-8"
    );
    map = normalChat.split('\n')
}

/** 闲聊信息检测 */
const find = (text: string) => {
    //1、全量匹配 normal_chat.txt中的语句
    if (map.includes(text)) {
        console.log('闲聊信息', text)
        return true
    }

    /** 2、格式为[***]或[**][**] */
    if (text.length <= 6 && text.startsWith('[') && text.endsWith(']')) {
        console.log('闲聊信息', text)
        return true
    }

    if (text.length === 0) return true

    /** 长度为1的非数字字符串 */
    if (text.length === 1 && Number.isNaN(Number(text))) return true

    return false
}

init()

export {
    find
}