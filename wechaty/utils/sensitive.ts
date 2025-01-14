const path = require('path')

// const sensitive_ad = '/' + path.join(__dirname, '../sensitive/广告.txt')
const sensitive_salacity = '/' + path.join(__dirname, '../sensitive/色情类.txt')
const sensitive_violence = '/' + path.join(__dirname, '../sensitive/涉枪涉爆违法.txt')
// const sensitive_politics = '/' + path.join(__dirname, '../sensitive/政治类.txt')

const sensitives = [
    // sensitive_ad,
    // sensitive_salacity,
    // sensitive_violence,
    // sensitive_politics
]

/** 敏感词存放空间 */
let map: any = {}

/** 添加敏感词 */
const addWord = (word) => {
    let parent = map

    for (let i = 0; i < word.length; i++) {
        if (!parent[word[i]]) parent[word[i]] = {}
        parent = parent[word[i]]
    }
    parent.isEnd = true
}

/** 初始化敏感词库 */
const init = () => {
    sensitives.map((p) => {
        let lineReader = require('readline').createInterface({
            input: require('fs').createReadStream(p, { encoding: 'UTF-8' })
        });

        lineReader.on('line', function (line) {
            if (!line) return
            addWord(line)
        });
    })
}

/** 替换敏感词为 * */
const filter = (s, cb?: any) => {
    let parent = map
    for (let i = 0; i < s.length; i++) {
        if (s[i] == '*') {
            continue
        }

        let found = false
        let skip = 0
        let sWord = ''

        for (let j = i; j < s.length; j++) {

            if (!parent[s[j]]) {
                found = false
                skip = j - i
                parent = map
                break;
            }

            sWord = sWord + s[j]
            if (parent[s[j]].isEnd) {
                found = true
                skip = j - i
                break
            }
            parent = parent[s[j]]
        }

        if (skip > 1) {
            i += skip - 1
        }

        if (!found) {
            continue
        }

        let stars = '*'
        for (let k = 0; k < skip; k++) {
            stars = stars + '*'
        }

        let reg = new RegExp(sWord, 'g')
        s = s.replace(reg, stars)

    }

    if (typeof cb === 'function') {
        cb(null, s)
    }

    return s
}

/** 查找第一个敏感词 */
const find = (s: string) => {
    let parent = map
    let sensitive_word = ''
    for (let i = 0; i < s.length; i++) {
        if (s[i] == '*') {
            continue
        }

        let found = false
        let skip = 0
        let sWord = ''

        for (let j = i; j < s.length; j++) {

            if (!parent[s[j]]) {
                found = false
                skip = j - i
                parent = map
                break;
            }

            sWord = sWord + s[j]
            if (parent[s[j]].isEnd) {
                found = true
                skip = j - i
                break
            }
            parent = parent[s[j]]
        }

        if (skip > 1) {
            i += skip - 1
        }

        if (found) {
            sensitive_word = sWord
            break
        }
    }
    if (sensitive_word) console.log('发现敏感词', sensitive_word)
    return sensitive_word
}

// init()

export {
    filter,
    find
}