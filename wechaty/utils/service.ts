import { type Wechaty } from "@juzi/wechaty";

export const getContact = async (bot: Wechaty, wxid: string) => {
  const isRoom = wxid.startsWith("R");

  const contact = isRoom
    ? await bot.Room.find({ id: wxid })
    : await bot.Contact.find({ id: wxid });
  return contact;
};
