import { Contact, log } from "@juzi/wechaty";
import { bot } from "@/src/index";
import { WechatyUi } from '@/utils'

/** 登录 */
export const onLogin = async (user: Contact) => {
  console.log('🌰🌰🌰 login 🌰🌰🌰')
  const room_list = WechatyUi.getPermissionRoom().rooms;
  const room = await bot.Room.find({
    id: room_list[0],
  });
  // 1. Send text inside Room
  // await room.say("我上线了");
  return log.info("StarterBot", "%s login", user);
};
