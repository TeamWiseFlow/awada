import { MESSAGE_TYPE } from '@/utils/type'
import { ConfigStatusType } from './const'
import { FormatUtils, isUrl } from '@/utils'

/** 拆解消息处理类型【仅包含问答、活动策划、】 */
export const getMessageFunUser = (text: string, type: number ,status: ConfigStatusType, overtime:boolean,modifyOvertime:boolean) => {
    if(status==='输入修改意见'){
        if(!modifyOvertime){
            if(type=== MESSAGE_TYPE.文本 || type=== MESSAGE_TYPE.语音){
                return '修改意见'
            } else {
                return '修改意见输入格式错误'
            }
        }
    }
    if (type === MESSAGE_TYPE.文本) {
        if (isUrl(text)) {
            return '文本链接'
        } else {
            return '文本'
        }
    }
    if (type === MESSAGE_TYPE.图片) return '图片'
    if (type === MESSAGE_TYPE.语音) return '语音'
    if (type === MESSAGE_TYPE.文件) {
        return '文件'
    }
    if (type === MESSAGE_TYPE.链接) return '链接'
    return '未知'
}

// /** 拆解消息处理类型 */
export const getMessageFunDirector = (text: string, type: number, status: ConfigStatusType, overtime: boolean,modifyOvertime?:boolean) => {
    if(status==='输入修改意见'){
        if(!modifyOvertime){
            if(type=== MESSAGE_TYPE.文本 || type=== MESSAGE_TYPE.语音){
                return '修改意见'
            } else {
                return '修改意见输入格式错误'
            }
        }
    }

    if (type === MESSAGE_TYPE.文本) {

        const isUrlLink = isUrl(text)
        const command = FormatUtils.checkCommand(text)
        console.log('command', command)
        if (command === '#list' || command === '#help' || command === '#ding') {
            return '命令'
        }

        if (text.length > 100 && !isUrlLink) return '长文本消息'

        if (status === '是否添加文件') {
            if (text === '取消') {
                if (!overtime) return '添加文件取消'
                return '指令超时'
            }
            if (text === '确认') {
                if (!overtime) return '添加文件确认'
                return '指令超时'
            }
        }

        if (status === '查看文件列表') {
            if (text === '取消') {
                if (!overtime) return '删除文件取消'
                return '指令超时'
            }
            if (!Number.isNaN(Number(text))) {
                if (!overtime) return '删除文件序号'
                return '指令超时'
            }
        }

        if (['确认', '取消'].includes(text)) {
            return '未知'
        }

        if (isUrlLink) return '文本链接'
        return '问题'
    }
    if (type === MESSAGE_TYPE.链接) return '链接'
    if (type === MESSAGE_TYPE.图片) return '图片'
    if (type === MESSAGE_TYPE.语音) return '语音'
    if (type === MESSAGE_TYPE.文件) {
        return '文件'
    }

    return '未知'
}