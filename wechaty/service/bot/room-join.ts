import { Room, Contact } from '@juzi/wechaty'
import { staticConfig } from "@/config";
import { WechatyUi } from "@/utils";

// 进入房间监听回调 room-群聊 inviteeList-受邀者名单 inviter-邀请者
export const onRoomJoin = async (room: Room, inviteeList: Contact[], inviter: Contact) => {
  console.log('🌰🌰🌰 onRoomJoin👇 🌰🌰🌰')
  console.log('有人加群', { room: room.id, inviteeList: inviteeList.map(i => i.payload), inviter, })
  const permission = WechatyUi.getPermissionRoom(room.id).permission;
  const { room_speech: { person_join, modify_remarks } } = staticConfig

  // 无权限群
  if (!permission) {
    console.log('无权限群加入用户:', inviteeList.map(c => c.name()).join(' + '))
    return
  }

  // 1、发送消息并@
  await room.say(person_join, ...inviteeList.filter(i=>!i.self()));

  // 权限群
  // 2、更新room_user
  WechatyUi.updateRoomUsers(room, 'update')

  // 3、检查用户是否都设置了群昵称
  const noAliasUser = await WechatyUi.getNoAliasUserId(room, inviteeList)

  // 4、针对未设昵称进行提醒
  if (noAliasUser && noAliasUser.length > 0) {
    await room.say(modify_remarks, ...noAliasUser)
  }
  return
};
