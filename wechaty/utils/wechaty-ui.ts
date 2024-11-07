import fs from "fs";
import JSON5 from 'json5'
import { Room, Contact } from '@juzi/wechaty'
import { RoomUsersType } from './type'
import { WechatyuiPath, ConfigPath, staticConfig } from '@/config'
import { getRoomUserJSON } from './file'

/** 获取权限用户列表 */
export const getPermissionUsers = (id?: number | string) => {
  const { directors } = staticConfig
  const roomUserConfig: RoomUsersType = getRoomUserJSON() || []
  const allUsers = roomUserConfig?.reduce((pre, cur) => {
    if (cur?.room?.memberIdList)
      return [...pre, ...cur?.room?.memberIdList]
    return pre
  }, [])

  const userInfo = { users: allUsers || [], permission: id ? allUsers.includes(id) || directors.includes(id as string) : false }
  return userInfo
}

/** 获取权限群 */
export const getPermissionRoom = (id?: number | string) => {
  const roomUserConfig: RoomUsersType = getRoomUserJSON() || []
  const allRooms = roomUserConfig?.reduce((pre, cur) => {
    if (cur?.room?.id)
      return [...pre, cur?.room?.id]
    return pre
  }, [])

  const userInfo = { rooms: allRooms || [], permission: id ? allRooms.includes(id) : false }
  return userInfo
}

/** 判断是否为管理员 */
const isDirectors = async (id: string): Promise<boolean> => {
  const { directors } = staticConfig
  return directors.includes(id);
};

/** 获取群内的导演列表 */
const roomDirectors = async (room: Room) => {

  const { directors } = staticConfig
  const allAlias = await room.memberAll()
  const roomDir = []
  allAlias.map(alia => {
    if (directors.includes(alia.id)) {
      roomDir.push(alia.id)
    }
  })
  return roomDir
}

/** 更新room_users */
const updateRoomUsers = async (room: Room, type: 'update' | 'clear' | 'add' | 'delete') => {
  let alias = []
  const roomConfig = getRoomUserJSON() || []
  const allAlias = await room.memberAll();

  if (type === 'update') {
    alias = await Promise.all(
      allAlias.map(ali => {
        return (async () => {
          const roomAlias = await room.alias(ali) || ''
          return { ...ali?.payload, roomAlias: roomAlias }
        })();
      }),
    );
  } else if (type === 'clear') {
    alias = []
  }
  const newConfig = { room: room.payload, users: alias };

  let newRoomConfig = []
  if (type === 'delete') {
    newRoomConfig = roomConfig?.filter((r) => r.room.id !== room.id)
  } else {
    let index = -1
    newRoomConfig = roomConfig?.map((r, i) => {
      if (r.room.id === room.id) {
        index = i
        return newConfig
      }
      return r
    })
    if (index === -1) newRoomConfig.push(newConfig)
  }

  fs.writeFileSync(
    `${WechatyuiPath}/room_users.json`,
    JSON.stringify(newRoomConfig, null, "\t")
  );
};

/** 更新全局 config.json 配置 */
export const updateConfig = async (key: string, value: string) => {
  const res = fs.readFileSync(
    `${ConfigPath}/config.json`,
    "utf-8"
  )
  const newConfig = JSON5.parse(res)
  newConfig[key] = value

  fs.writeFileSync(
    `${ConfigPath}/config.json`,
    JSON.stringify(newConfig, null, "\t")
  );
}

/** 获取当前群没有备注的用户列表，默认取群内所有用户 */
export const getNoAliasUserId = async (room: Room, users?: Contact[]): Promise<Contact[]> => {
  const allMember = users ? users : await room.memberAll()
  const noAlias = []
  await Promise.all(allMember.map((m) => {
    return (async () => {
      const roomAlias = await room.alias(m) || ''
      if (!roomAlias && !m.self()) {
        noAlias.push(m)
      }
    })()
  }))
  return noAlias
}

export default {
  getPermissionUsers,
  getPermissionRoom,
  isDirectors,
  roomDirectors,
  updateConfig,
  updateRoomUsers,
  getNoAliasUserId
};
