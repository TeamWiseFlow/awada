## Service 接口

### 端口号： 8088

#### 获取当前账号
GET /api/userinfo 

#### 发送文本消息
POST /api/sendtxtmsg

- wxid string ： 发送消息的微信id或群id
- content string：发送消息内容（如果是群聊组消息并需要发送艾特时，此content字段中需要有对应数量的@[自定义被艾特人的昵称，不得少于2个字符] [每个艾特后都需要一个空格以进行分隔（包括最后一个艾特！）]，这一点很重要！ 如果您不理解，请继续看下面的Tips！）
- atlist array<string>：如果是群聊组消息并需要发送艾特时，此字段是一个被艾特人的数组
 
###### Tips：如果是群聊艾特消息，那么content字段中的@艾特符号数量需要和atlist中的被艾特人数组长度一致，简单来说，就是atlist中有多少个被艾特人的wxid，那么content字段中就需要有多少个艾特组合，位置随意，例如： {"wxid": "xx@chatroom", "content": "这里@11 只是@22 想告诉你@33 每个被艾特人的位置并不重要", "atlist": ["wxid_a", "wxid_b", "wxid_c"]} 每个被艾特人在content中 固定为@[至少两个字符的被艾特人名] + 一个空格！ 如果是发送@所有人消息，那么请在atlist字段中仅传入一个notify@all字符串，content字段中仅包含一个@符号规范（最少两字符+一个空格）， 一般建议是@所有人见名知意


#### 发送图片消息
POST /api/sendimgmsg

- wxid string： 发送消息的微信id或群id
- path string： 发送图片的绝对路径
- atlist array<string>：如果是群聊组消息并需要发送艾特时，此字段是一个被艾特人的数组

#### 发送文件消息

POST /api/sendfilemsg

- wxid string： 发送消息的微信id或群id
- path string： 发送文件的绝对路径
- atlist array<string>：如果是群聊组消息并需要发送艾特时，此字段是一个被艾特人的数组

-------------------------------------------

### 1、环境搭建

##### 安装 node 环境

> https://blog.csdn.net/jason_cuijiahui/article/details/79450232

a、安装 nvm

```
git clone https://github.com/creationix/nvm.git ~/.nvm && cd ~/.nvm && git checkout `git describe --abbrev=0 --tags`
```

b、安转Node

```sh
nvm use 16.10.0
```

##### 配置 pm2 环境

安转 pm2

```sh
npm install -g pm2
```

pm2 日志

```sh
pm2 install pm2-logrotate
```

### 2、启动方式

```sh
npm install
```

#### 本地调试

```sh
pm2 start npm --name wechaty -- run local
```

环境变量【当前环境变量配置在.env文件中，也可添加在命令中】

##### TOKEN=****

购买的句子互动的Puppet

##### WECHATY_PUPPET_SERVICE_AUTHORITY=token-service-discovery-test.juzibot.com：

wechaty官方的token解析不稳定，使用句子提供的服务器

##### mode=local

判断当前是否为本地开发环境

##### WECHATY_LOG=silly

增加Wechaty log信息

#### 服务器启动

```sh
pm2 start npm --name wechaty -- run serve
```

【wechaty】是当前开启进程的名字，自定义

之后执行pm2 log 打开日志

#### 关于pm2服务管理

###### pm2 list

查看当前进程列表

###### pm2 log

打开进程日志

###### pm2 restart wechaty

重新启动 wechaty 进程

### 3、项目结构

```
├── config                   // 全局配置信息   
│   ├── config.json             // 项目可配置参数【修改无需重启】
├── ├── normal_chat.txt         // 闲聊信息词典 
│   └── index.ts                // 项目配置参数 【修改需要重启】 
├── database                 // 文件存放     
│   ├── files                   // 用户上传文件暂存区
│   └── wechatyui               // 用户相关信息暂存
│       └── room_users.json         // 权限群用户暂存
├── sensitive                // 不当言论词库     
├── service                  // 中台服务
│   ├── algorithm               // 中台接口
│   │   ├── file-add.ts             // 添加文件接口
│   │   ├── file-delete.ts          // 删除文件接口
│   │   ├── file-list.ts            // 获取文件列表接口
│   │   ├── index.ts    
│   │   ├── question.ts             // QA接口
│   │   └── response.ts             // 接口返回信息统一处理
│   └── bot                  // Wechaty 服务
│       ├── error.ts            // bot 报错处理
│       ├── friendship.ts       // bot 加、删好友处理
│       ├── index.ts    
│       ├── login.ts            // bot 登录处理
│       ├── logout.ts           // bot 登出处理
│       ├── message             // bot 消息
│       │   ├── filter.ts           // 过滤掉无用消息或对某些不规范消息进行处理
│       │   ├── index.ts            // 处理消息
│       │   ├── log.ts              // 消息日志
│       │   ├── msg.ts              // 将消息信息进行整理，封装成一个信息库，方便其他模块使用
│       │   ├── person              // 处理私聊消息
│       │   │   ├── command.ts          // 导演指令处理
│       │   │   ├── const.ts            // 私聊相关常量值
│       │   │   ├── conversation.ts     // 私聊对话轮次存取
│       │   │   └── index.ts            // 处理私聊信息
│       │   └── smartqa.ts          // smartqa 消息类型处理以及回复处理
│       ├── room-join.ts        // 新用户加群处理
│       ├── room-leave.ts       // 用户离群处理
│       └── scan.ts             // bot 扫码登录
├── src
│   └── index.ts            // bot 初始化、启动
├── utils                   // 工具包
│   ├── bot.ts                  // bot 相关方法
│   ├── file.ts                 // 文件信息处理方法
│   ├── format.ts               // 格式化方法
│   ├── index.ts        
│   ├── message.ts              // 各种类型消息处理方法
│   ├── sensitive.ts            // 不当消息检测
├── ├── normalchat.ts           // 闲聊信息检测
│   ├── type.ts                 // 类型定义集合
│   └── wechaty-ui.ts           // 获取相关信息方法合集
├── tsconfig.json           // typescript 配置文件 
├── package.json            // 项目包管理配置文件 
├── pm2.config.js           // pm2 配置文件
└── .env                    // 存放TOKEN【服务端需要手动添加】

```

### 4、常见问题

#### Q1：文件保存失败【 WARN PuppetService This might because you are using Wechaty v1.x with a Puppet Service v0.x 】

##### 参考

https://github.com/wechaty/puppet-service/issues/179

```
npm install wechaty-puppet-service
```

#### Q2：JSON文件内加注释报【 Comments are not permitted in JSON 】

在vsCode 的 settings.json添加配置

```
"files.associations": {
    "*.json": "jsonc"
}
```

#### Q3：throw new error（'no grpc manager')

这个是workpro服务的一个重连的bug。token对应容器被重启后，链接没有自动恢复。【 具体问题找句子互动 】

Q4：nvm 安装之后可能文件夹带锁，导致之后nvm 安装node版本的时候没有权限，添加 sudo 执行又找不到命令，这个时候可以把.nvm文件的锁去掉，执行

```
sudo chown -R username .nvm
```

这里的username就是你Ubuntu系统安装的时候取得名字
