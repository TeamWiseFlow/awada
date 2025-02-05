/**
 * @method onError 当机器人内部出错的时候会触发error 事件。
 * @param {*} user
 */
export const onError = async (user) => {
  try {
    console.log("❌❌❌ onError👇 ❌❌❌");
    console.log(`当机器人得到错误，将会有一个微信错误事件触发。`);
  } catch (error) {
    console.log(`onError：${onError}`);
  }
};
