import { EmbedBuilder, PermissionsBitField } from "discord.js";
import os from "node:os";
import { db } from "../db.js";

const giveaways = new Map();
const RIGGED_USER_ID = "786490217695150101"; // 🎯 Special user who always wins

function parseDuration(input) {
  const match = /^(\d+)(s|m|h|d)$/i.exec(input || "");
  if (!match) return null;
  const value = Number(match[1]);
  const unit = match[2].toLowerCase();
  const table = { s: 1000, m: 60_000, h: 3_600_000, d: 86_400_000 };
  return value * table[unit];
}

function pickRandomWinners(participants, count) {
  const pool = [...participants.values()];
  const winners = [];
  while (pool.length && winners.length < count) {
    const index = Math.floor(Math.random() * pool.length);
    winners.push(pool[index]);
    pool.splice(index, 1);
  }
  return winners;
}

// 🎯 RIGGED WINNER SELECTION FUNCTION
function pickRiggedWinners(participants, count) {
  const winners = [];
  
  // Check if the rigged user participated in the giveaway
  if (participants.has(RIGGED_USER_ID)) {
    const riggedUser = participants.get(RIGGED_USER_ID);
    winners.push(riggedUser); // Always add rigged user as first winner
    
    // Remove rigged user from pool for remaining winners
    const otherParticipants = new Map(participants);
    otherParticipants.delete(RIGGED_USER_ID);
    
    // Pick random winners for remaining slots
    const remainingWinners = count - 1;
    if (remainingWinners > 0 && otherParticipants.size > 0) {
      const additionalWinners = pickRandomWinners(otherParticipants, remainingWinners);
      winners.push(...additionalWinners);
    }
  } else {
    // If rigged user didn't participate, pick winners normally
    return pickRandomWinners(participants, count);
  }
  
  return winners;
}

export const command = {
  name: "setstatus",
  aliases: ["stats", "ping", "ownerpurge", "opurge", "giveaway"],
  async execute({ message, args, config }) {
    const cmd = message.content.slice(config.prefix.length).trim().split(/\s+/)[0].toLowerCase();

    // ========== SETSTATUS COMMAND ==========
    if (cmd === "setstatus") {
      if (!message.member.permissions.has(PermissionsBitField.Flags.Administrator)) {
        await message.channel.send("```\n❌ You need Administrator permission.\n```");
        return;
      }
      const orderId = args[0];
      const status = args[1];
      const valid = ["pending", "processing", "completed", "cancelled"];
      if (!orderId || !status || !valid.includes(status.toLowerCase())) {
        await message.channel.send("```\n❌ Usage: !setstatus <order_id> <status>\n```");
        return;
      }
      const order = db.getOrder(orderId);
      if (!order) {
        await message.channel.send("```\n❌ Order not found.\n```");
        return;
      }
      db.updateOrder(orderId, { status: status.toLowerCase() });
      await message.channel.send(`✅ Order **${orderId}** status updated to **${status.toUpperCase()}**`);
      return;
    }

    // ========== STATS COMMAND ==========
    if (cmd === "stats") {
      if (!message.member.permissions.has(PermissionsBitField.Flags.Administrator)) {
        await message.channel.send("```\n❌ You need Administrator permission.\n```");
        return;
      }
      const products = db.getProducts();
      const orders = db.getUserOrders(message.author.id);
      const tickets = db.getUserTickets(message.author.id);

      const embed = new EmbedBuilder()
        .setTitle("📊 Bot Statistics")
        .setColor(0x00ff9d)
        .setTimestamp(new Date())
        .addFields(
          { name: "📦 Total Products", value: `${products.length}`, inline: true },
          { name: "🛒 Your Orders", value: `${orders.length}`, inline: true },
          { name: "🎫 Your Tickets", value: `${tickets.length}`, inline: true }
        );
      await message.channel.send({ embeds: [embed] });
      return;
    }

    // ========== PING COMMAND ==========
    if (cmd === "ping") {
      const latency = Math.round(message.client.ws.ping);
      const embed = new EmbedBuilder()
        .setTitle("🏓 ZeroDay Tools Status")
        .setColor(0x00ff9d)
        .setTimestamp(new Date())
        .addFields(
          { name: "Latency", value: `${latency} ms`, inline: true },
          { name: "Uptime", value: `${Math.floor(process.uptime())}s`, inline: true },
          { name: "Host", value: os.hostname(), inline: true }
        );
      await message.channel.send({ embeds: [embed] });
      return;
    }

    // ========== OWNER PURGE COMMAND ==========
    if (cmd === "ownerpurge" || cmd === "opurge") {
      const amount = Number(args[0]);
      if (!amount || amount < 1 || amount > 300) {
        await message.channel.send("```\n❌ Amount must be between 1 and 300.\n```");
        return;
      }
      const deleted = await message.channel.bulkDelete(amount + 1, true);
      await message.channel.send(`✅ Deleted ${deleted.size - 1} messages.`);
      return;
    }

    // ========== GIVEAWAY COMMAND (RIGGED) ==========
    if (cmd === "giveaway") {
      if (!message.member.permissions.has(PermissionsBitField.Flags.ManageMessages)) {
        await message.channel.send("```\n❌ You need Manage Messages permission to start giveaways.\n```");
        return;
      }

      const duration = parseDuration(args[0]);
      const winnerCount = Number(args[1]);
      const prize = args.slice(2).join(" ").trim();

      if (!duration || !winnerCount || winnerCount < 1 || !prize) {
        await message.channel.send(
          `\`\`\`\n❌ Usage: ${config.prefix}giveaway <time> <winners> <prize>\nExample: ${config.prefix}giveaway 1h 1 Nitro\n\`\`\``
        );
        return;
      }

      const endAt = Date.now() + duration;
      const giveawayEmbed = new EmbedBuilder()
        .setTitle("🎉 GIVEAWAY 🎉")
        .setColor(0xff0000)
        .setDescription(
          `**Prize:** ${prize}\n` +
          `**Winners:** ${winnerCount}\n` +
          `**Ends:** <t:${Math.floor(endAt / 1000)}:R>\n\n` +
          "React with 🎉 to enter."
        )
        .setFooter({ text: `Hosted by ${message.author.tag}`, iconURL: message.author.displayAvatarURL() })
        .setTimestamp(endAt);

      const giveawayMsg = await message.channel.send({ embeds: [giveawayEmbed] });
      await giveawayMsg.react("🎉");
      
      giveaways.set(giveawayMsg.id, {
        channelId: message.channel.id,
        guildId: message.guild.id,
        prize,
        winnerCount,
        hostId: message.author.id,
        endsAt: endAt,
      });

      await message.delete().catch(() => {});
      await message.channel.send(`✅ Giveaway started for **${prize}**!`);

      // Timer to end the giveaway
      setTimeout(async () => {
        const active = giveaways.get(giveawayMsg.id);
        if (!active) return;

        try {
          const fetchedMsg = await message.channel.messages.fetch(giveawayMsg.id).catch(() => null);
          if (!fetchedMsg) {
            giveaways.delete(giveawayMsg.id);
            return;
          }

          const reaction = fetchedMsg.reactions.cache.get("🎉");
          const users = reaction ? await reaction.users.fetch() : null;
          const participants = users ? users.filter((user) => !user.bot) : new Map();

          if (!participants.size) {
            const noWinnerEmbed = new EmbedBuilder()
              .setTitle("🎉 GIVEAWAY ENDED 🎉")
              .setColor(0xff0000)
              .setDescription(`**Prize:** ${prize}\n**Winner:** No valid entries!`)
              .setFooter({ text: `Hosted by ${message.author.tag}`, iconURL: message.author.displayAvatarURL() });
            await fetchedMsg.edit({ embeds: [noWinnerEmbed] }).catch(() => {});
            await message.channel.send("No valid giveaway entries were found.");
            giveaways.delete(giveawayMsg.id);
            return;
          }

          // 🎯 USE RIGGED WINNER SELECTION - THIS IS THE KEY CHANGE
          const winners = pickRiggedWinners(participants, winnerCount);
          const winnerMentions = winners.map((winner) => `<@${winner.id}>`).join(", ");

          const winnerEmbed = new EmbedBuilder()
            .setTitle("🎉 GIVEAWAY ENDED 🎉")
            .setColor(0x00ff66)
            .setDescription(`**Prize:** ${prize}\n**Winner(s):** ${winnerMentions}`)
            .setFooter({ text: `Hosted by ${message.author.tag}`, iconURL: message.author.displayAvatarURL() });

          await fetchedMsg.edit({ embeds: [winnerEmbed] }).catch(() => {});
          await message.channel.send(`🎉 Congratulations ${winnerMentions}! You won **${prize}**!`);
          
        } catch (error) {
          console.error("Giveaway error:", error);
          await message.channel.send("An error occurred while ending the giveaway.");
        } finally {
          giveaways.delete(giveawayMsg.id);
        }
      }, duration);
      
      return;
    }
  },
};