import { staticConfig } from "@/config"

/** 接口返回flag */
export const FLAG_ENUM = {
    '-5': '入参格式错误',
    '-4': 'scholar文件提取失败',
    '-3': '语音asr失败',
    '-2': '（部分）tts转化失败',
    '-1': 'playlist生成失败',
    '0': '正常返回',
    '1': 'scholar没有找到答案',
    '2': 'scholar给出的是参考答案',
    '11': 'Journalist/Coacher流程正常结束'
}

/** 处理接口返回信息 */
export default async (error, response, body): Promise<{ success: boolean, flag, contents: any }> => {
    console.log('response', {
        error: error,
        statusCode: response?.statusCode,
        body: body
    })

    if (!error && response?.statusCode == 200 && body) {
        let res = JSON.parse(body)

        const { flag, result: contents, play_list } = res

        if (flag === 0 || flag === 2) {
            return { flag, success: true, contents }
        }

        if (flag === 1) {
            return {
                flag,
                success: true,
                contents: contents || staticConfig?.request_speech.ask_noanswer
            }
        }

        /** flag为21 返回 策划标题 和 word文件路径 */
        if (flag === 21) {
            return {
                flag,
                success: true,
                contents: contents
            }
        }

        if (flag === -3) {
            return {
                flag,
                success: false,
                contents: contents || staticConfig.request_speech.audio_failed
            }
        }

        if (flag === -4) {
            return {
                flag,
                success: false,
                contents: contents || staticConfig?.request_speech.error
            }
        }

        /** 文件路径错误 */
        if (flag === -5) {
            return {
                flag,
                success: false,
                contents: contents || staticConfig?.request_speech.path_error
            }
        }

        /** 大模型错误，稍后重试 */
        if (flag === -11) {
            return {
                flag,
                success: false,
                contents: contents || staticConfig?.request_speech.retry
            }
        }

        return {
            flag,
            success: false,
            contents: contents || staticConfig?.request_speech.error
        }
    } else {
        return {
            flag: 999,
            success: false,
            contents: staticConfig?.request_speech.error
        }
    }
}