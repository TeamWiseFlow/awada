import { Room, Contact } from '@juzi/wechaty'
import { types } from '@juzi/wechaty'

/** 消息类型 */
export const PUPPET_TYPE_MESSAGE = types.Message;

export const MESSAGE_TYPE = {
    '文本': PUPPET_TYPE_MESSAGE.Text,
    '图片': PUPPET_TYPE_MESSAGE.Image,
    '语音': PUPPET_TYPE_MESSAGE.Audio,
    '视频': PUPPET_TYPE_MESSAGE.Video,
    '文件': PUPPET_TYPE_MESSAGE.Attachment,
    '表情符号': PUPPET_TYPE_MESSAGE.Emoticon,
    '聊天历史记录': PUPPET_TYPE_MESSAGE.ChatHistory,
    '地方': PUPPET_TYPE_MESSAGE.Location,
    '小程序': PUPPET_TYPE_MESSAGE.MiniProgram,
    '未知': PUPPET_TYPE_MESSAGE.Unknown,
    '添加用户成功消息': 18,
    "链接": PUPPET_TYPE_MESSAGE.Url,
    "撤回消息": PUPPET_TYPE_MESSAGE.Recalled
}

export type AliasType = Room['alias']

/** 权限群数据类型 */
export type RoomUsersType = {
    room: Room['payload'],
    users: Contact[] & { roomAlias?: string },
}[]

/** 全局配置 config.json 数据类型 */
export type StaticConfigType = {
    /* 变量提前配置，方便后续配置引用 */
    "variable_config": {
        /* 群欢迎语 */
        "welcome": "欢迎大家参与社区情景培训课程的语料采集工作！\n这项工作很重要， 我将从您的每一句回复中学习到正确的答案特征， 以便在未来社工的培训中充当一名合格的裁判。\n另外我还能帮助大家进行业务知识查询， 目前支持的领域包括： 防疫政策和加梯政策。\n请大家这就添加我的微信开始吧！[玫瑰]"
    },
    /* 命令超时限制 */
    "timeout": 90,
    /* 群聊问答模式是否开启 close or open */
    "room_question": "close" | "open",
    /* 管理员列表*/
    "directors": string[],
    /* 普通命令 */
    "common_order": {
        "confirm": "确认",
        "abort": "取消"
    },
    /* 管理员命令 */
    "directors_order": {
        /* 查询列表 */
        "list": "list",
        /* 帮助命令 */
        "help": "help",
        "ding": "ding"
    },
    /* 群命令 */
    "room_order": {
        /* 开启群权限 */
        "start": "start",
        /* 关闭群权限 */
        "stop": "stop",
        /* 开启、关闭 群问答*/
        "talking": "talking"
        /** 版本更新 */
        "update": "update"
        /** 查询文件列表 */
        "list": "list"
    },
    /* 群对话文案 */
    "room_speech": {
        /* 群欢迎语 */
        "welcome": "${variable_config.welcome}",
        /* 群无权限 */
        "no_permission": "请管理员先开启本群服务权限：@我并输入start",
        /* 新用户加入 */
        "person_join": "欢迎加入数字社区！\n\n${variable_config.welcome}\n\n请新成员完成以下操作：\n1. 按群主要求修改群昵称\n2. 添加我为微信好友，以便正常使用服务。\n谢谢！",
        /* 修改群备注名提示 */
        "modify_remarks": "请您及时按群主要求设定昵称哦，谢谢配合[玫瑰]",
        /* 执行start */
        "start": "${variable_config.welcome}\n\n请大家添加我为微信好友，以便正常使用服务[呲牙]。",
        /* 群关闭提示文案 */
        "stop": "数字社工助理的服务已关闭，再次开通服务请联系管理员",
        "update": "我更新好了，欢迎大家@我进行提问。",
        /* 开启群问答 */
        "open_talking": "群内对话服务已开启，请@我进行提问。",
        /* 关闭群问答*/
        "stop_talking": "对话服务已关闭，如需再次开启请管理员@我并输入taliking",
        /* 当前群未开启问答模式 */
        "no_talking": "群内对话服务未开启，请管理员@我并输入talking开启"
    },
    /* 私聊对话文案 */
    "person_speech": {
        /* 私聊欢迎语 */
        "welcome": "欢迎您为社区情景培训课程贡献训练数据！我们将以对话的方式进行采集，您的个人信息都将被去除，如需开始，请输入：#开始\n业务知识查询， 请直接输入问题喔~[抱抱]",
        /* 无权限 */
        "no_permission": "您暂未开通使用权限，请联系管理员开通，或咨询微信：baohukeji",
        /* 群权限关闭，用于通知管理员*/
        "room_stop": "的服务已关闭，再次开启请在群内@我并输入start"
    },
    /* 通用文案 */
    "common_speech": {
        /* 不当言论 */
        "bad_words": "请勿发表不当言论",
        /* 指令错误 */
        "order_error": "未查询到相关指令，您是否想输入以下指令：\n查询文件库的所有文件，输入：list \n更多请输入：help",
        /* 收到文件资源，图片、长文本、文件 */
        "file_received": "收到新文档，确定添加到文档库中么？确认请回复：确认",
        /* 资源接收失败 */
        "file_received_fail": "文件上传失败，请您再试一次，或联系管理员处理～",
        /* 确定添加文件到中台 */
        "file_saved": "收到！文件库更新中，请稍后～",
        /* 文件添加到中台成功 */
        "file_saved_success": "文件库更新成功",
        /* 执行 #list 未查找到任何文件 */
        "file_list_none": "未查找到任何文件",
        /* 执行 #list 查询文件列表 */
        "file_list": "文件库已有文件如下：",
        /* 删除文件提示 */
        "file_delete": "如需删除某个文件，请回复文件前的数字序号。",
        /* 正在删除 */
        "file_delete_start": "文件正在删除中，请稍后～",
        /* 删除失败 */
        "file_delete_failed": "文件删除失败，请联系管理员处理哦～",
        /* 删除失败 */
        "file_delete_success": "文件删除成功",
        /* 取消操作 */
        "abort": "好的，已取消操作",
        /* help 指令*/
        "help": "数字社工助理导演指令：\n1. 查询文件库的所有文件，输入：list\n2. 查询服务范围，输入：help\n3. 如需新增文件，请直接转发文件或者文本内容给数字社工助理",
        /* ding 指令*/
        "ding": "dong"
    },
    /* 请求相关文案 */
    "request_speech": {
        /* flag=1或flag为0、2但contents为空 */
        "ask_noanswer": "未检索到相关信息，请换个问题或联系管理员查证",
        /* flag 为-3*/
        "audio_failed": "抱歉，没听清呢，好心人不介意再试一次吧[委屈]",
        /* 其他 */
        "error": "数字社工助理开小差了，请联系管理员处理哦～",
        /** 路径错误 */
        "path_error": "文件路径有问题，请重新上传或联系管理员处理~",
        /** 稍后重试 */
        "retry": "抱歉，请稍后重试"
    }
} | undefined
