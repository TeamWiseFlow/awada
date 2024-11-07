
import officegen from "officegen";
import { FilesPath } from '@/config'
const fs = require("fs");

/** 格式转换 */
export const formatContents = (content: string) => {
    const headers = content.match(/\【(.*?)\】(.*?)\n/g);

    const wordContent = [];

    headers.map((t, index) => {
        const currentTitle = t;
        const nextTitle = headers?.[index + 1] || "";
        const stepOne = content.split(currentTitle)[1];
        const stepTwo = nextTitle ? stepOne.split(nextTitle)[0] : stepOne;
        console.log("stepTwo", stepTwo);
        wordContent.push({
            title: t,
            content: stepTwo,
        });
    });
    return wordContent
}


export default async (text: string, title: string, callback: () => void) => {

    const wordContent = formatContents(text)
    // Create an empty Word object:
    let docx = officegen("docx");

    // Officegen calling this function after finishing to generate the docx document:
    docx.on("finalize", function (written) {
        console.log("Finish to create a Microsoft Word document.");
    });

    // Officegen calling this function to report errors:
    docx.on("error", function (err) {
        console.log(err);
    });
    let pObj = docx.createP();

    wordContent?.map((item, index) => {
        // Create a new paragraph:
        if (index === 0) {
            pObj = docx.createP({ align: "center" });
            pObj.addText(item.title, {
                bold: true,
                font_size: 18,
                align: "center",
            });
        } else {
            pObj = docx.createP({ align: "left" });
            pObj.addText(item.title, {
                bold: true,
                font_size: 16,
            });
            pObj.addText(item.content);
        }
    });


    let out = await fs.createWriteStream(`${FilesPath}/${title}.docx`);

    out.on("error", function (err) {
        console.log(err);
    });

    docx.generate(out)

    out.on('close', function () {
        console.log('Finished to create the PPTX file!');      // 回调执行接下步骤达到同步操作
        callback()
    });
}
