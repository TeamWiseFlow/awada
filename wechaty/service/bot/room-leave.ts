import { types, Contact, Room } from '@juzi/wechaty'
import { WechatyUi } from '@/utils'
/**
 * 当机器人把群里某个用户移出群聊的时候会触发这个时间。用户主动退群是无法检测到的。
 */

export const onRoomLeave = async (room: Room, leaverList: Contact[], remover?: Contact, date?: Date) => {
    console.log('🌰🌰🌰 onRoomleave👇 🌰🌰🌰')
    // 1、更新room_user
    WechatyUi.refreshRoom(room)

    console.log('成员离开')
    return ;
}
