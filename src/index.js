import "dotenv/config";
import fs from "node:fs";
import path from "node:path";
import { Client, GatewayIntentBits, Partials, Collection } from "discord.js";
import { loadConfig } from "./config.js";
import { setupLavalink } from "./lavalink.js";

const config = loadConfig();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildVoiceStates,
  ],
  partials: [Partials.Channel, Partials.Message],
});

client.commands = new Collection();
client.commandModules = [];

const commandsPath = path.join(process.cwd(), "src", "commands");
if (fs.existsSync(commandsPath)) {
  const files = fs.readdirSync(commandsPath).filter((f) => f.endsWith(".js"));
  for (const file of files) {
    const mod = await import(path.join(commandsPath, file));
    client.commandModules.push(mod);
    if (mod?.command?.name) {
      client.commands.set(mod.command.name, mod.command);
      if (mod.command.aliases) {
        for (const alias of mod.command.aliases) {
          client.commands.set(alias, mod.command);
        }
      }
    }
  }
}

client.once("clientReady", async () => {
  console.log(`✅ Logged in as ${client.user.tag}`);
  await setupLavalink(client, config);
  for (const mod of client.commandModules) {
    if (typeof mod.register === "function") {
      await mod.register(client, config);
    }
  }
});

client.on("messageCreate", async (message) => {
  if (!message.guild || message.author.bot) return;
  if (!message.content.startsWith(config.prefix)) return;

  // Role Restriction: Only users with the following role ID can use commands
  const REQUIRED_ROLE_ID = "1260193783484514434";
  if (!message.member.roles.cache.has(REQUIRED_ROLE_ID)) {
    return;
  }

  const args = message.content.slice(config.prefix.length).trim().split(/\s+/);
  const name = args.shift()?.toLowerCase();
  if (!name) return;

  const command = client.commands.get(name);
  if (!command) return;

  try {
    await command.execute({ client, message, args, config });
  } catch (err) {
    console.error(err);
    await message.channel.send("```\n❌ Command failed. Check logs.\n```");
  }
});

client.on("interactionCreate", async (interaction) => {
  if (!interaction.guild) return;

  const REQUIRED_ROLE_ID = "1260193783484514434";
  if (!interaction.member?.roles.cache.has(REQUIRED_ROLE_ID)) {
    if (interaction.isRepliable()) {
      await interaction.reply({ content: "❌ You do not have the required role to use this bot.", flags: 64 });
    }
    return;
  }

  for (const mod of client.commandModules) {
    if (typeof mod.handleInteraction === "function") {
      const handled = await mod.handleInteraction({ client, interaction, config });
      if (handled) {
        return;
      }
    }
  }
});

const token = process.env.DISCORD_TOKEN;
if (!token) {
  throw new Error("DISCORD_TOKEN is not set.");
}

process.on("unhandledRejection", (error) => {
  console.error("Unhandled promise rejection:", error);
});

process.on("uncaughtException", (error) => {
  console.error("Uncaught exception:", error);
});

async function shutdown(signal) {
  console.warn(`Received ${signal}, shutting down bot gracefully...`);
  try {
    await client.destroy();
  } catch (error) {
    console.error("Error while destroying client:", error);
  } finally {
    process.exit(0);
  }
}

process.on("SIGTERM", () => {
  shutdown("SIGTERM");
});

process.on("SIGINT", () => {
  shutdown("SIGINT");
});

client.login(token);
