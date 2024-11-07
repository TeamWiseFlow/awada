const request = require("request")
import fs from "fs";
import responseHandler from './response'
import { QueryReturnType, Type, ParamsType } from './type'
import PB from '@/utils/pb'
import { FileBox, FileBoxInterface } from "file-box";

/* 添加文件 */
export const requestFileAdd = async (info: { content: string, filename: string }): Promise<QueryReturnType> => {
    const { content, filename } = info
    const res = await PB.uploadFile(content, filename)
    return res as any
}