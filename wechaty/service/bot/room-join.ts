import { Room, Contact } from '@juzi/wechaty'
// import { staticConfig } from "@/config";
import { WechatyUi } from "@/utils";

// 进入房间监听回调 room-群聊 inviteeList-受邀者名单 inviter-邀请者
export const onRoomJoin = async (room: Room, inviteeList: Contact[], inviter: Contact) => {
  console.log('🌰🌰🌰 onRoomJoin👇 🌰🌰🌰')
  console.log('有人加群', { room: room.id, inviteeList: inviteeList.map(i => i.payload), inviter })
  const permission = (await WechatyUi.getPermissionRoom(room.id)).permission;
  //   const { room_speech: { person_join, modify_remarks } } = staticConfig
  // 无权限群
  if (!permission) {
    console.log('无权限群加入用户:', inviteeList.map(c => c.name()).join(' + '))
    return
  }

  // 1、发送消息并@
  //   await room.say(person_join, ...inviteeList.filter(i=>!i.self()));

  // 权限群
  // 2、更新room_user
  WechatyUi.refreshRoom(room)

  return
};
