
export const StatusEnum = {
    '无对话轮次': 0,
    '是否添加文件': 1,
    '添加文件确认': 11,
    '添加文件取消': 10,
    '查看文件列表': 2,
    '输入修改意见': 12
} as const

export type ConfigStatusType = keyof typeof StatusEnum

export type ConversationUserConfigType = {
    status?: ConfigStatusType
    fileName?: string
    fileList?: { id: string, filename: string }[]
    lastTime?: string
}

export interface ConversationConfigType {
    [user: string]: ConversationUserConfigType
}