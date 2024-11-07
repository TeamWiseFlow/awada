export type QueryReturnType = {
    success: boolean,
    flag: number,
    // contents: string | { type: "text" | "file", answer: string }[]
    contents: any
}

export type ParamsType = {
    /** 用户ID */
    user_id: string,
    /**  发送类型 */
    type: Type,
    /** 相应内容 */
    content: string,
    /** 修改意见 */
    addition?: string
}

export type Type = 'text' | 'image' | 'voice' | 'file'
