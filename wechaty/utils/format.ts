/** 检查是否为命令，如果为命令则自动去除前面的 #号 */
export const checkCommand = (text: string): string | boolean => {
    // if (text.trim().startsWith('#') || text.trim().startsWith('＃')) {
    //     /** 处理中文和英文#号 */
    //     const command = text.trim().replace('#', '').replaceAll('＃', '')
    //     return command.length > 0 ? command : false
    // }
    // return false
    return text.trim()
}

/** 
 * 文本过滤
 * 1、过滤emoji表情
 */
export const formatText = (text: string): string => {
    let result = text
    // result = text.replaceAll(/\[.*?\]/g, '')
    result = result.replaceAll(/\uD83C[\uDF00-\uDFFF]|\uD83D[\uDC00-\uDE4F]/g, "")
    return result
}
