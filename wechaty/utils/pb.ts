let dotenv = require('dotenv');
const PocketBase = require("pocketbase/cjs");
import fs from "fs";
import FormData from 'form-data';
import 'cross-fetch/polyfill';

dotenv.config('./env')

export const pb = new PocketBase(process.env?.POCKETBASE);

export const ERROR_HTTP = {
    0: "无法连接服务器或连接中断",
    400: "无权限的操作",
    validation_not_unique: "记录已存在，操作取消",
};

type ReturnType = { success: boolean, flag: number, contents: string }


const credentials = {
    username: process.env?.POCKETBASE_USERNAME,
    password: process.env?.POCKETBASE_PASSWORD
}

/** 登录 */
const login = async () => {
    try {
        //const userData = await pb.collection('users').authWithPassword(credentials.username, credentials.password)
        const userData = await pb.admins.authWithPassword(credentials.username, credentials.password);
        // set({ token: userData.token });
        console.log('🚀🚀🚀 pb login success 🚀🚀🚀')
        return userData;
    } catch (err) {
        console.log('⚠️ pocketbase login error', err);
        return { error: true, status: err.status, ...err.response };
    }
}

/** 查询文件列表 */
const getFiles = async (keyword?: string, filters?: any): Promise<{ success: boolean, flag: number, contents: { id: string, filename: string }[] }> => {
    const _exts = (filters && filters.ext && filters.ext.length > 0 && filters.ext) || ["%"];
    const _filename = keyword && keyword != "*" ? `%${keyword}%` : "%";
    const _filter = _exts.map((ext) => `filename ~ "${_filename}.${ext}"`).join(" || ");

    try {
        const data = await pb.collection("documents").getFullList({
            filter: _filter,
            sort: "-updated",
        });
        const files = data.map(f => ({ id: f.id, filename: f.filename }))
        console.log('file-list', { data, files, length: data.length });
        return {
            flag: 0,
            success: true,
            contents: files
        }
    } catch (err) {
        if (err.isAbort) return;
        console.log(err.status, err.response, err.isAbort);
        // get().setErrorMessage(ERROR_HTTP[err.status] || ERROR_HTTP[0]);
        // return { error: true, status: err.status, ...err.response };
        return {
            flag: -1,
            success: false,
            contents: []
        }
    }
}

/** 添加文件 */
const uploadFile = async (dir, name): Promise<ReturnType> => {
    const formData = new FormData();
    formData.append("file", fs.createReadStream(dir));
    formData.append("filename", name);
    try {
        // 如果依赖数据库index unique约束filename，会正常报错，不会新建记录，但文件仍然会传到storage目录，污染目录下文件。
        // 因此手动检查同名文件是否已存在，如果存在直接报错。
        const res = await pb.collection("documents").getFullList({
            filter: `filename = "${name}"`,
        });
        let exists = res.find((f) => f.filename == name);
        if (exists) {
            console.log("file exists");
            return { success: false, flag: -1, contents: '已有同名文件，请修改名字重新上传' };
        }
        const createdRecord = await pb.collection("documents").create(formData);
        // console.log('createdRecord', createdRecord)
        return { success: true, flag: 0, contents: '' }
        // return createdRecord;
    } catch (err) {
        if (err.isAbort) return;
        let ErrorMessage = ''
        if (err.response.data && err.response.data.file && err.response.data.file.code == "validation_not_unique") {
            ErrorMessage = (ERROR_HTTP[err.response.data.file.code] || err.response.data.file.message);
        } else {
            ErrorMessage = (ERROR_HTTP[err.status] || ERROR_HTTP[0]);
        }
        return { success: false, flag: -1, contents: ErrorMessage };
    }
}

/** 删除文件 */
const deleteFile = async (id): Promise<ReturnType> => {
    try {
        await pb.collection("documents").delete(id);
        return {
            success: true,
            flag: 0,
            contents: ''
        }
    } catch (err) {
        if (err.isAbort) return;
        let ErrorMessage = ''
        if (err.response.data && err.response.data.file && err.response.data.file.code) {
            ErrorMessage = ERROR_HTTP[err.response.data.file.code] || err.response.data.file.message;
        } else {
            ErrorMessage = ERROR_HTTP[err.status] || ERROR_HTTP[0];
        }
        return { success: false, flag: -1, contents: ErrorMessage as string };
    }
}

export default {
    login,
    getFiles,
    uploadFile,
    deleteFile
}



