wxbot 虽然可以通过wine+docker方案运行于macOS或者linux上，但稳定性效果不如直接在windows系统上运行

_（在win上运行也更简单，直接下载exe文件，一键启动了）_

### 运行命令 

`docker run -itd --name wxbot -e WXBOT_ARGS="-q http://127.0.0.1:8080/qr_callback" -p 8066:8080 registry.cn-shanghai.aliyuncs.com/jwping/wxbot:v1.10.1-9-3.9.8.25`

【2024-07-07】亲测正常下载就行，无需特殊操作

以上命令参数不要改，尤其是端口映射，awada dm部分是写死的。

### 首次登录

首次运行需要用使用的微信号扫码登录下

`docker logs -f wxbot`

注意，如果你使用OrbStack，直接用软件界面打开container的日志，可能看不到二维码链接，所以要用系统自带的终端使用上述命令。

等待终端输出，直到看到 类似  “http://weixin.qq.com/x/QfOfkbfe_P5wdeKNjR7S”  这样的登录二维码链接信息，复制（**注意不要直接打开，那没用！**）

使用二维码生成器，比如草料 https://cli.im/url

生成一个二维码，用需要的微信扫码登录（仅限个微）

直到logs出现  `Http Server Listen 0.0.0.0:8080` 那就好了，终端里面出现的任何报错信息都可以忽略，不影响正常使用。

好了 `ctrl+C` 退出 终端logs界面，之后终端直接关闭都行。

用作助理的个微小号建议把支付还有服务等都关闭，不要暴露敏感信息，**使用者请风险自担**！

### 再次登录

在macOS或者linux上运行wxbot最适合成功后常开，不要频繁关闭打开，就放在那里就好，反正默认是静默运行，终端正常也不会输出什么信息的。

理论上，关掉container（包括电脑重启），再次启动会自动登录，此时只需要在微信手机端上点同意就行。

如果失败的话， 先运行 `docker logs -f wxbot` 看看是不是要重新登录。

如果看不到让你重新登录的二维码链接信息，尝试

`docker restart wxbot`

如果还不行，运行，

`docker rm -f wxbot`

然后用最开始那个运行命令再次创建container，放心image已经在本地，不会再次下载。

### 问题排查

首先logs界面里面出现的任何报错信息都可以忽略，只要有 `Http Server Listen 0.0.0.0:8080`  那就是正常的

每次启动（包括重启），最长需要5min才能出现 Http Server Listen 0.0.0.0:8080  或者二维码链接，期间任何报错信息都没所谓

如果在 Http Server Listen 0.0.0.0:8080  或者 二维码链接 之前长时间（大于等于5min）不出任何信息，那可能是出问题了。参考再次登录方案。

`Http Server Listen 0.0.0.0:8080` 之后基本终端界面就不会出新的消息了，这是正常的，这个时候其实可以退出logs，甚至关闭终端。

更多，请参考：https://github.com/jwping/wxbot?tab=readme-ov-file#linux%E4%B8%8Bdocker%E9%83%A8%E7%BD%B2
