let dotenv = require("dotenv");
let Koa = require("koa");
// Import necessary modules
import { WechatyBuilder, log } from "@juzi/wechaty";
import fs from "fs";
import path from "path";
import CONFIG, { init } from "../config";

dotenv.config("./env");

// Initialize Wechaty bot
/** 机器人初始化 */
export const bot = WechatyBuilder.build({
  name: CONFIG.name,
  puppet: CONFIG.juziPuppetName,
  puppetOptions: {
    tls: {
      disable: true,
    },
    token: process.env?.TOKEN,
    timeoutSeconds: 4 * 60, // 默认1分钟
  },
});
// Global variables
let directors = [];
const configFolderPath = process.env.CONFIGS || "avatars";
const configFileMap = {};
const learnSourcesMap = {};
const serviceListMap = {};

// Load directors from file
function loadDirectors() {
  if (fs.existsSync("directors.json")) {
    directors = JSON.parse(fs.readFileSync("directors.json", "utf-8"));
  }
}

// Load bot configurations
function loadConfigs() {
  const configFiles = fs
    .readdirSync(configFolderPath)
    .filter((file) => file.endsWith(".json"));
  configFiles.forEach((file) => {
    const configFile = path.join(configFolderPath, file);
    const config = JSON.parse(fs.readFileSync(configFile, "utf-8"));
    const botId = config.bot_id || "default";
    configFileMap[botId] = configFile;
    config.learn_sources.forEach((source) => (learnSourcesMap[source] = botId));
    config.service_list.forEach((service) => (serviceListMap[service] = botId));
  });
}

// Define the handleRoomMessage function
async function handleRoomMessage(roomId: string, content: string) {
  // Find the room by ID
  const room = await bot.Room.find({ id: roomId });
  if (!room) {
    console.error(`Room with ID ${roomId} not found`);
    return;
  }

  // Process the message content
  // For example, you could log the message or perform some action based on its content
  console.log(`Message received in room ${roomId}: ${content}`);

  // Example: Respond to a specific command
  if (content === "hello") {
    await room.say("Hello! How can I assist you today?");
  }
}

// Handle incoming messages
bot.on("message", async (message) => {
  const room = message.room();
  const sender = message.from();
  const content = message.text();

  if (room) {
    const roomId = room.id;
    if (content.startsWith("/")) {
      await handleDirectorCommand(roomId, content);
    } else if (content.includes(`@${bot.name()}`)) {
      const cleanContent = content.replace(`@${bot.name()}`, "").trim();
      await handleRoomMessage(roomId, cleanContent);
    }
  } else if (directors.includes(sender.id) && content.startsWith("/")) {
    await handleDirectorCommand(sender.id, content);
  }
});

// Handle director commands
async function handleDirectorCommand(id, command) {
  const [cmd, ...args] = command.split(" ");
  switch (cmd) {
    case "/start":
      await startBot(id);
      break;
    case "/add_source":
      await addSourceTo(id, args[0]);
      break;
    case "/add_service":
      await addServiceTo(id, args[0]);
      break;
    case "/stop":
      await stopAny(id);
      break;
    case "/promotion":
      await promoteCoDirector(id);
      break;
    case "/refresh":
      await refreshAny(id);
      break;
    case "/list":
      await listBots(id);
      break;
    default:
      log.info("Unknown command");
  }
}

// Start a new bot
async function startBot(roomId) {
  if (configFileMap[roomId]) {
    log.info(`Bot already exists for room ${roomId}`);
    return;
  }
  const config = {
    bot_id: roomId,
    learn_sources: [roomId],
    service_list: [roomId],
  };
  configFileMap[roomId] = path.join(configFolderPath, `${roomId}.json`);
  fs.writeFileSync(configFileMap[roomId], JSON.stringify(config, null, 2));
  log.info(`Created bot for room ${roomId}`);
}

// Add a learning source
async function addSourceTo(roomId, botId) {
  if (!configFileMap[botId]) {
    log.info(`Bot ${botId} does not exist`);
    return;
  }
  const config = JSON.parse(fs.readFileSync(configFileMap[botId], "utf-8"));
  if (!config.learn_sources.includes(roomId)) {
    config.learn_sources.push(roomId);
    fs.writeFileSync(configFileMap[botId], JSON.stringify(config, null, 2));
    log.info(`Added ${roomId} as learning source to bot ${botId}`);
  }
}

// Add a service target
async function addServiceTo(roomId, botId) {
  if (!configFileMap[botId]) {
    log.info(`Bot ${botId} does not exist`);
    return;
  }
  const config = JSON.parse(fs.readFileSync(configFileMap[botId], "utf-8"));
  if (!config.service_list.includes(roomId)) {
    config.service_list.push(roomId);
    fs.writeFileSync(configFileMap[botId], JSON.stringify(config, null, 2));
    log.info(`Added ${roomId} as service target to bot ${botId}`);
  }
}

// Stop a bot
async function stopAny(roomId) {
  if (configFileMap[roomId]) {
    delete configFileMap[roomId];
    log.info(`Stopped bot for room ${roomId}`);
  }
}

// Promote co-director
async function promoteCoDirector(roomId) {
  const members = await getRoomMemberIds(roomId);
  directors = Array.from(new Set([...directors, ...members]));
  fs.writeFileSync("directors.json", JSON.stringify(directors, null, 2));
  log.info(`Promoted members of ${roomId} to co-directors`);
}

// Refresh room members
async function refreshAny(roomId) {
  const members = await getRoomMemberIds(roomId);
  const botId = serviceListMap[roomId];
  if (botId) {
    const config = JSON.parse(fs.readFileSync(configFileMap[botId], "utf-8"));
    config.service_list = Array.from(new Set([...config.service_list, ...members]));
    fs.writeFileSync(configFileMap[botId], JSON.stringify(config, null, 2));
    log.info(`Refreshed members of ${roomId} for bot ${botId}`);
  }
}

// List all bots
async function listBots(userId) {
  const botList = Object.keys(configFileMap)
    .map((botId) => `Bot ID: ${botId}`)
    .join("\n");
  await bot.say(botList);
}

// Get room member IDs
async function getRoomMemberIds(roomId) {
  const room = await bot.Room.find({ id: roomId });
  if (room) {
    const members = await room.memberAll();
    return members.map((member) => member.id);
  }
  return [];
}

// Start the bot
bot
  .start()
  .then(() => {
    log.info("Bot started");
    loadDirectors();
    loadConfigs();
  })
  .catch((err) => log.error("Bot start failed:", err));
