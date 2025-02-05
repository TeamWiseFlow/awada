import { Contact, log } from "@juzi/wechaty";

/** 登录 */
export const onLogin = async (user: Contact) => {
  console.log("🌰🌰🌰 login 🌰🌰🌰");

  return log.info("StarterBot", "%s login", user);
};
