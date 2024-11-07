import { Contact, log } from "@juzi/wechaty";
import { bot } from "@/src/index";
import { WechatyUi } from '@/utils'

/** 登出 */
export const onLogout = async (user: Contact) => {
  console.log('🌰🌰🌰 logout 🌰🌰🌰')
  // const room_list = WechatyUi.getPermissionRoom().rooms;
  // const room = await bot.Room.find({
  //   id: room_list[0],
  // });
  // // 1. Send text inside Room
  // await room.say("拜拜👋🏻👋🏻，我下线了");
  console.log("🌰🌰🌰 StarterBot", "%s logout 🌰🌰🌰", user);
};
