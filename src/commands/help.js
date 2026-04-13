import {
  EmbedBuilder,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
} from "discord.js";

const MUSIC_ICON = "https://cdn.discordapp.com/emojis/1041113066373152828.gif";

function helpMusic() {
  const embed = new EmbedBuilder()
    .setColor(0x00ff9d)
    .setTimestamp(new Date())
    .setAuthor({ name: "🎵 MUSIC COMMANDS", iconURL: MUSIC_ICON })
    .setDescription(
      "```ansi\n" +
        "\u001b[1;36m╔═══════════════════════════════════════════════════╗\n" +
        "\u001b[1;36m║             ADVANCED MUSIC SYSTEM                 ║\n" +
        "\u001b[1;36m╚═══════════════════════════════════════════════════╝\n" +
        "```\n" +
        "**Music commands for the best audio experience!**\n" +
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    .addFields(
      {
        name: "🎶 **Playback**",
        value:
          "> `!play <song>` - Play a song or URL\n" +
          "> `!pause` - Pause current track\n" +
          "> `!resume` - Resume current track\n" +
          "> `!stop` - Stop and clear queue\n" +
          "> `!skip` - Skip current track\n" +
          "> `!join` - Join your voice channel\n" +
          "> `!leave` - Disconnect from voice",
        inline: false,
      },
      {
        name: "📜 **Queue & Info**",
        value:
          "> `!queue` - View current queue\n" +
          "> `!nowplaying` - View current track\n" +
          "> `!shuffle` - Shuffle the queue\n" +
          "> `!loop` - Toggle loop modes\n" +
          "> `!volume <0-150>` - Change volume",
        inline: false,
      },
      {
        name: "🤖 **Advanced Features**",
        value:
          "> `!autoplay` - Toggle automatic play\n" +
          "> `!aimode` - Toggle AI suggestions\n" +
          "> `!vibe <style>` - Set AI vibe\n" +
          "> `!suggest` - Get AI song suggestions",
        inline: false,
      }
    )
    .setFooter({
      text: "Music Bot • Enjoy the rhythm",
      iconURL: MUSIC_ICON,
    })
    .setThumbnail(MUSIC_ICON);
  return embed;
}

export const command = {
  name: "help",
  aliases: ["h", "commands"],
  async execute({ message }) {
    await message.channel.send({ embeds: [helpMusic()] });
  },
};

export async function handleInteraction({ interaction }) {
  return false;
}
