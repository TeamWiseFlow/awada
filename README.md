# awada

虽然基于LLM的Agent概念已经很统一，业内也不断涌现优秀的框架和开源项目，但是目前这些Agent还局限在Assistant的范畴，也就是“它们”被设计为只能执行人类给出的任务，且人设定位为人类的辅助（表现为对话逻辑很容易被人类带走）。

我们并不否认这类Assistant的价值，事实上Assistant的应用范围确实很广，但是依然有很多场景我们是需要Agent具有类似人脑那样的较为“感性”的“说不清道理“的决策机制，且需要Agent能够“坚持己见”，甚至反过来说服人类。

这些典型的场景可以举例如下：
- 数字演员，尤其是互动类体验的演员，如“剧本杀”；
- 售前机器人，帮助客户快速了解产品，并能够基于客户对话有目的的说服客户购买；
- 社交网络博主，可以自主使用各类AIGC工具，在各类社交平台（如小红书、微博、知乎等）进行创作与发布，并与粉丝互动

……

总而言之，我们要打造的是一个具有自主意识、自主决策能力的Agent“灵魂系统”，我们相信这套灵魂系统也可以嫁接到目前各类流行的Assistant类Agent上，这可能会产生更大的价值。

<img alt="scope" src="asset/what&#39;sawada.png" width="960"/>

## 发布平台

目前我们在repo中提供了一个简单的web对话界面示例，参考 DialogWeb目录

对于有需求接入微信公众号的项目，推荐参考 [微信SDK](https://weixin-python.readthedocs.io/zh/latest/ '微信SDK docs')

对于有需求接入微信（个微或企微），推荐参考 [wechaty](https://github.com/wechaty/wechaty 'wechaty github')

## 欢迎贡献

Awada项目目前处于起步阶段，WiseFlow（首席情报官） Team 会在社交网络行业情报获取、角色扮演对话机器人等类型项目的开发工作中不断提炼相关技术，整理贡献至Awada项目，也希望大家可以一起参与贡献。（项目开源许可证为Apache2.0，所有贡献者需要签署CLA）。

# Citation

如果您在相关工作中参考或引用了本项目的部分或全部，请注明如下信息：

```
Author：Project Awada
https://openi.pcl.ac.cn/wiseflow/awada
Licensed under Apache2.0
```