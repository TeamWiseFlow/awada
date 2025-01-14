import { Friendship, Wechaty, types } from "@juzi/wechaty";
import { getPermissionUsers } from '@/utils/wechaty-ui'
import { staticConfig } from '@/config'

// 打招呼消息
const HelloMap: { [key: number | string]: string } = {}
// 维护打招呼消息对象
export const Hello = () => {
  return {
    get: (id?: number | string) => {
      if (id)
        return HelloMap?.[id] || ''
      return HelloMap
    },
    add: (id: number | string, text) => {
      HelloMap[id] = text
    },
    remove: (id: number | string) => {
      delete HelloMap[id]
      console.log('清除成功')
    }
  }
}

// 好友添加监听回调
// export const onFriendShip = (bot: Wechaty) => {
export const onFriendShip = async (friendship: Friendship) => {
  console.log('🌰🌰🌰 friendship 🌰🌰🌰')
  let logMsg;
  console.log('friendship.content', friendship.contact().name)
  try {
    const permisesion = (await getPermissionUsers(friendship.contact().id)).permission

    switch (friendship.type() || 5) {
      case types.Friendship.Receive:
        // 判断用户是否在权限群组中
        if (permisesion) {
          const hello = friendship.hello()
          Hello().add(friendship.contact().id, hello)
          console.log('用户是权限用户，加好友请求通过', HelloMap)
          // 通过验证
          await friendship.accept();
        } else {
          console.log('用户不是权限用户，加好友请求不通过')
        }
        break
      case 5:
        console.log('有人删除好友')
        break
      /**
      * 2. 友谊确认
      */
      case types.Friendship.Confirm:
        console.log(`添加好友通过: ${friendship.type()} ${friendship.contact().name()} ${friendship.contact().id}`)
        logMsg = "friend ship confirmed with " + friendship.contact().name()
        // 判断用户是否在权限群组中
        console.log('用户是权限用户，发送欢迎语')
        // 通过验证，发送欢迎语
        friendship.contact().say(staticConfig.person_speech.welcome)
        break
      default: console.log('未处理', friendship.type())
    }
    return
  } catch (e) {
    logMsg = e.message;
  }
  console.log(logMsg);
}

