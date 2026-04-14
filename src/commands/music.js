import {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  EmbedBuilder,
} from "discord.js";

const controlState = new Map();
const autoplayState = new Map();
const aiModeState = new Map();
const vibeState = new Map();
const lastTrackTitle = new Map();
const lastTrackAuthor = new Map();

function isTimeoutError(error) {
  const text = String(error?.message || error || "").toLowerCase();
  return text.includes("timeout") || text.includes("aborted");
}

function isSpotifyUnsupportedError(error) {
  const text = String(error?.message || error || "").toLowerCase();
  return text.includes("spotify") && text.includes("not 'spotify' enabled");
}

function buildSearchQuery(rawQuery) {
  const query = String(rawQuery || "").trim();
  if (!query) return { query };

  const lower = query.toLowerCase();
  if (lower.includes("spotify.com/") || lower.startsWith("spotify:")) {
    return { query, source: "spsearch" };
  }
  if (lower.includes("youtube.com/") || lower.includes("youtu.be/")) {
    return { query, source: "ytsearch" };
  }
  return { query, source: "spsearch" };
}

function formatDuration(ms) {
  if (!Number.isFinite(ms) || ms < 0) return "Unknown";
  const total = Math.floor(ms / 1000);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${m}:${String(s).padStart(2, "0")}`;
}

function clamp(num, min, max) {
  return Math.max(min, Math.min(max, num));
}

function progressBar(positionMs, durationMs, size = 16) {
  if (!Number.isFinite(positionMs) || !Number.isFinite(durationMs) || durationMs <= 0) {
    return "───────────────";
  }
  const ratio = clamp(positionMs / durationMs, 0, 1);
  const filled = Math.round(ratio * size);
  const empty = Math.max(0, size - filled);
  return `${"█".repeat(filled)}${"░".repeat(empty)}`;
}

function shorten(text, max = 48) {
  const value = String(text || "").trim();
  if (!value) return "Unknown";
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}

function sourceLabel(source) {
  const value = normalizeText(source);
  if (value.includes("spotify")) return "Spotify";
  if (value.includes("youtube")) return "YouTube";
  if (value.includes("soundcloud")) return "SoundCloud";
  return source ? shorten(source, 18) : "Unknown";
}

function normalizeText(text) {
  return String(text || "").toLowerCase().replace(/\s+/g, " ").trim();
}

function buildAiQuery(title, author, vibe) {
  const base = [title, author].filter(Boolean).join(" ");
  const vibeTag = vibe ? ` ${vibe} mix` : " mix";
  return `${base}${vibeTag}`.trim();
}

async function ensureAiQueue(player, requester, limit = 3) {
  const currentTrack = player.queue.current;
  const lastTitle = lastTrackTitle.get(player.guildId) || "";
  const lastAuthor = lastTrackAuthor.get(player.guildId) || "";
  
  const title = String(currentTrack?.title || currentTrack?.info?.title || lastTitle || "");
  const author = String(currentTrack?.info?.author || lastAuthor || "");
  const vibe = vibeState.get(player.guildId);
  const query = buildAiQuery(title, author, vibe);
  if (!query) return;

  const result = await player.search({ query }, requester).catch(() => null);
  if (!result?.tracks?.length) return;

  // Build exclusion list including current track, queue, AND previous tracks
  const existing = new Set(
    [
      currentTrack, 
      ...(player.queue.tracks || []),
      ...(player.queue.previous || [])
    ]
      .filter(Boolean)
      .map((track) => normalizeText(track?.title || track?.info?.title))
  );

  // Also exclude the last tracked title manually to be extra safe against loops
  if (lastTitle) existing.add(normalizeText(lastTitle));

  const picks = [];
  for (const track of result.tracks) {
    const key = normalizeText(track?.title || track?.info?.title);
    if (!key || existing.has(key)) continue;
    picks.push(track);
    if (picks.length >= limit) break;
  }
  if (picks.length) {
    await player.queue.add(picks);
  }
}

function buildButtons(player) {
  const autoplayOn = autoplayState.get(player.guildId) === true;
  const loopMode = String(player.repeatMode || "off").toUpperCase();
  const aiOn = aiModeState.get(player.guildId) === true;
  
  return [
    new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId("music_playpause")
        .setLabel(player.paused ? "Resume" : "Pause")
        .setEmoji(player.paused ? "▶️" : "⏸️")
        .setStyle(ButtonStyle.Primary),
      new ButtonBuilder()
        .setCustomId("music_skip")
        .setLabel("Skip")
        .setEmoji("⏭️")
        .setStyle(ButtonStyle.Secondary),
      new ButtonBuilder()
        .setCustomId("music_stop")
        .setLabel("Stop")
        .setEmoji("⏹️")
        .setStyle(ButtonStyle.Danger),
      new ButtonBuilder()
        .setCustomId("music_shuffle")
        .setLabel("Shuffle")
        .setEmoji("🔀")
        .setStyle(ButtonStyle.Secondary),
      new ButtonBuilder()
        .setCustomId("music_loop")
        .setLabel(`Loop: ${loopMode}`)
        .setEmoji("🔁")
        .setStyle(ButtonStyle.Secondary)
    ),
    new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId("music_voldown")
        .setLabel("Vol -")
        .setEmoji("🔉")
        .setStyle(ButtonStyle.Secondary),
      new ButtonBuilder()
        .setCustomId("music_volup")
        .setLabel("Vol +")
        .setEmoji("🔊")
        .setStyle(ButtonStyle.Secondary),
      new ButtonBuilder()
        .setCustomId("music_queue")
        .setLabel("Queue")
        .setEmoji("📜")
        .setStyle(ButtonStyle.Secondary),
      new ButtonBuilder()
        .setCustomId("music_autoplay")
        .setLabel(`Autoplay: ${autoplayOn ? "ON" : "OFF"}`)
        .setEmoji("📻")
        .setStyle(autoplayOn ? ButtonStyle.Success : ButtonStyle.Secondary),
      new ButtonBuilder()
        .setCustomId("music_ai")
        .setLabel(`AI: ${aiOn ? "ON" : "OFF"}`)
        .setEmoji("🤖")
        .setStyle(aiOn ? ButtonStyle.Success : ButtonStyle.Secondary)
    ),
  ];
}

function buildNowPlayingEmbed(player) {
  const track = player.queue.current;
  const ANIMATED_SINGER = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHU4YnZ6bTR6NTR6NTR6NTR6NTR6NTR6NTR6NTR6NTR6NTR6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TKMGpxPzUfS9mVO/giphy.gif";
  const LIVE_ICON = "https://cdn.discordapp.com/emojis/1041113066373152828.gif";

  const embed = new EmbedBuilder()
    .setColor(0x00ff9d)
    .setTimestamp();

  if (!track) {
    embed
      .setAuthor({ name: "SINNERS MUSIC | SYSTEM IDLE", iconURL: LIVE_ICON })
      .setDescription(
        "```ansi\n" +
        "\u001b[1;32m┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n" +
        "\u001b[1;32m┃        \u001b[1;37m🎧  PLAYER STATUS: \u001b[1;33mSTANDBY\u001b[1;32m         ┃\n" +
        "\u001b[1;32m┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n" +
        "```\n" +
        "**Welcome to the next generation of audio.**\n" +
        "Use `!play` to ignite the stage.\n\n" +
        "**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**"
      )
      .addFields(
        { name: "📡 NETWORK", value: "```yaml\nStatus: Online\nLatency: Stable\n```", inline: true },
        { name: "🤖 INTELLIGENCE", value: `\`\`\`yaml\nAI: ${aiModeState.get(player.guildId) ? "Enabled" : "Disabled"}\nAutoplay: ${autoplayState.get(player.guildId) ? "On" : "Off"}\n\`\`\``, inline: true }
      )
      .setImage(ANIMATED_SINGER)
      .setFooter({ text: "SYSTEM READY • SINNERS MUSIC V2", iconURL: LIVE_ICON });
    return embed;
  }

  const title = track.title || track.info?.title || "Unknown Track";
  const author = track.info?.author || "Unknown Artist";
  const durationMs = track.duration ?? track.info?.duration ?? track.info?.length ?? 0;
  const duration = formatDuration(durationMs);
  const positionMs = player.position ?? 0;
  const position = formatDuration(positionMs);
  const bar = progressBar(positionMs, durationMs, 22);
  const volume = player.volume ?? 100;
  const requester = track.requester?.id ? `<@${track.requester.id}>` : "System";
  const artwork = track.info?.artworkUrl || track.info?.thumbnail || null;
  const nextUp = player.queue.tracks?.[0];
  const loopMode = (player.repeatMode || "off").toUpperCase();
  const source = sourceLabel(track.info?.sourceName || "unknown");
  const nodeName = player.node?.options?.id || "Primary";

  embed
    .setAuthor({ name: "NOW BROADCASTING • SINNERS MUSIC", iconURL: LIVE_ICON })
    .setTitle(`🎧 ${shorten(title, 80)}`)
    .setURL(track.uri || null)
    .setDescription(
      "```ansi\n" +
      `\u001b[1;32mArtist  : \u001b[1;37m${shorten(author, 40)}\n` +
      `\u001b[1;32mSource  : \u001b[1;37m${source}\n` +
      `\u001b[1;32mNode    : \u001b[1;37m${nodeName}\n` +
      "```"
    )
    .addFields(
      { 
        name: "🎵 **AUDIO PROGRESSION**", 
        value: `**${position}** ${bar} **${duration}**`, 
        inline: false 
      },
      { 
        name: "👤 **REQUESTER**", 
        value: requester, 
        inline: true 
      },
      { 
        name: "🔊 **VOLUME**", 
        value: `\`${volume}%\``, 
        inline: true 
      },
      { 
        name: "🔄 **LOOPING**", 
        value: `\`${loopMode}\``, 
        inline: true 
      },
      { 
        name: "📻 **AUTOPLAY**", 
        value: autoplayState.get(player.guildId) === true ? "✅ `ENABLED`" : "❌ `DISABLED`", 
        inline: true 
      },
      { 
        name: "🤖 **AI ENGINE**", 
        value: aiModeState.get(player.guildId) === true ? "✅ `ACTIVE`" : "❌ `OFFLINE`", 
        inline: true 
      },
      { 
        name: "📈 **QUEUE**", 
        value: `\`${player.queue.tracks.length} tracks left\``, 
        inline: true 
      },
      { 
        name: "⏭️ **UP NEXT**", 
        value: nextUp ? `\`${shorten(nextUp.title || nextUp.info?.title, 60)}\`` : "*The stage ends here.*", 
        inline: false 
      }
    )
    .setImage(ANIMATED_SINGER);

  if (artwork) embed.setThumbnail(artwork);
  
  embed.setFooter({ 
    text: `Powered by Sinners Music • High Fidelity Audio • Shard #0`, 
    iconURL: LIVE_ICON 
  });
  
  return embed;
}

function buildQueueEmbed(player) {
  const current = player.queue.current;
  const tracks = player.queue.tracks ?? [];
  const embed = new EmbedBuilder()
    .setColor(0x00ff9d)
    .setTitle("📜 Music Queue")
    .setTimestamp();

  if (!current && !tracks.length) {
    embed.setDescription("The queue is currently empty.");
    return embed;
  }

  let description = "";
  if (current) {
    description += `**Now Playing:**\n[${shorten(current.title || current.info?.title, 64)}](${current.uri})\n\n`;
  }

  if (tracks.length) {
    description += "**Up Next:**\n";
    description += tracks
      .slice(0, 10)
      .map((track, i) => `\`${i + 1}.\` ${shorten(track.title || track.info?.title, 50)}`)
      .join("\n");
    
    if (tracks.length > 10) {
      description += `\n*...and ${tracks.length - 10} more tracks*`;
    }
  } else {
    description += "*No more tracks in queue.*";
  }

  embed.setDescription(description);
  embed.setFooter({ text: `Total Tracks: ${tracks.length + (current ? 1 : 0)} | Loop: ${(player.repeatMode || "off").toUpperCase()}` });
  
  return embed;
}

async function updateControlMessage(player) {
  const discordClient = player?.LavalinkManager?.discordClient;
  if (!player || !discordClient) return;
  const info = controlState.get(player.guildId);
  if (!info) return;
  const { channelId, messageId } = info;
  const channel = discordClient.channels.cache.get(channelId);
  if (!channel) return;
  const message = await channel.messages.fetch(messageId).catch(() => null);
  if (!message) return;
  await message.edit({ embeds: [buildNowPlayingEmbed(player)], components: buildButtons(player) }).catch(() => {});
}

export const command = {
  name: "play",
  aliases: [
    "p",
    "join",
    "summon",
    "leave",
    "disconnect",
    "pause",
    "resume",
    "stop",
    "skip",
    "next",
    "nowplaying",
    "np",
    "queue",
    "q",
    "volume",
    "vol",
    "loop",
    "shuffle",
    "clearqueue",
    "clearq",
    "remove",
    "move",
    "nodes",
    "autoplay",
    "ap",
    "aimode",
    "ai",
    "vibe",
    "suggest",
  ],
  async execute({ message, args, config }) {
    const client = message.client;
    const manager = client.lavalink;
    if (!manager || !manager.useable) {
      await message.channel.send("```\n❌ Lavalink is not ready yet.\n```");
      return;
    }

    const cmd = message.content.slice(config.prefix.length).trim().split(/\s+/)[0].toLowerCase();
    const voiceChannelId = message.member.voice?.channelId;

    const getPlayer = () =>
      manager.createPlayer({
        guildId: message.guild.id,
        voiceChannelId,
        textChannelId: message.channel.id,
        selfDeaf: true,
        volume: 100,
      });

    if (cmd === "join" || cmd === "summon") {
      if (!voiceChannelId) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ Join a voice channel first.")] });
        return;
      }
      const player = getPlayer();
      if (!player.connected) await player.connect();
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("✅ Successfully joined your voice channel.")] });
      return;
    }

    if (cmd === "leave" || cmd === "disconnect") {
      const player = manager.getPlayer(message.guild.id);
      if (!player) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ I am not connected to any voice channel.")] });
        return;
      }
      await player.destroy();
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("✅ Disconnected and cleared the session.")] });
      return;
    }

    if (cmd === "play" || cmd === "p") {
      if (!voiceChannelId) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ Join a voice channel first to play music.")] });
        return;
      }
      const query = args.join(" ");
      if (!query) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xffbb00).setDescription("ℹ️ Usage: `!play <song name/url>`")] });
        return;
      }

      const player = getPlayer();
      if (!player.connected) await player.connect();
      const connectedNodes = Array.from(manager.nodeManager?.leastUsedNodes?.("playingPlayers") || [])
        .filter((node) => node?.connected)
        .map((node) => node.options.id);
      if (!connectedNodes.length) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ No healthy music nodes are available right now.")] });
        return;
      }

      const orderedNodeIds = [
        player.node?.options?.id,
        ...connectedNodes.filter((id) => id !== player.node?.options?.id),
      ].filter(Boolean);

      let result = null;
      let lastError = null;
      for (const nodeId of orderedNodeIds) {
        try {
          if (player.node?.options?.id !== nodeId) {
            await player.moveNode(nodeId);
          }
          result = await player.search(buildSearchQuery(query), message.author);
          if (result?.tracks?.length) break;
        } catch (error) {
          lastError = error;
          continue;
        }
      }

      if (!result) {
        if (isTimeoutError(lastError)) {
          await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ Search timed out. Please try again.")] });
        } else if (isSpotifyUnsupportedError(lastError)) {
          await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ Spotify links are not supported on this node. Try searching by name.")] });
        } else {
          await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription(`❌ Search failed: \`${lastError?.message || "unknown error"}\``)] });
        }
        return;
      }

      if (!result.tracks?.length) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ No results found.")] });
        return;
      }

      if (result.loadType === "playlist") {
        await player.queue.add(result.tracks);
        const playlistName = result.playlist?.name || result.playlist?.info?.name || "Playlist";
        await message.channel.send(`✅ Added playlist: **${playlistName}** (${result.tracks.length} tracks)`);
      } else {
        const track = result.tracks[0];
        await player.queue.add(track);
        const title = track.title || track.info?.title || "Unknown Track";
        await message.channel.send(`✅ Queued: **${title}**`);
      }

      if (!player.playing && !player.paused && !player.queue.current) {
        await player.play();
      }
      return;
    }

    const player = manager.getPlayer(message.guild.id);
    if (!player) {
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ The music player is not active in this server.")] });
      return;
    }

    if (cmd === "pause") {
      await player.pause();
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("⏸️ Playback has been paused.")] });
      await updateControlMessage(player);
      return;
    }

    if (cmd === "resume") {
      await player.resume();
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("▶️ Playback has been resumed.")] });
      await updateControlMessage(player);
      return;
    }

    if (cmd === "stop") {
      await player.stopPlaying(true, false);
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("⏹️ Stopped playback and cleared the queue.")] });
      await updateControlMessage(player);
      return;
    }

    if (cmd === "skip" || cmd === "next") {
      const hasNext = player.queue.tracks.length > 0;
      const isAutoplay = autoplayState.get(message.guild.id) === true || aiModeState.get(message.guild.id) === true;

      if (!hasNext && !isAutoplay) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ No more tracks in the queue to skip to.")] });
        return;
      }

      try {
        if (!hasNext && isAutoplay) {
          await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("⏳ Fetching next track via Autoplay...")] });
          await ensureAiQueue(player, player.queue.current?.requester || message.author, 1);
        }
        
        if (player.queue.tracks.length > 0) {
          await player.skip();
          await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("⏭️ Skipped to the next track.")] });
        } else {
          await player.stopPlaying(true, false);
          await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("⏹️ No tracks found. Stopped playback.")] });
        }
      } catch (err) {
        console.error("Skip error:", err);
        await message.channel.send("❌ Failed to skip track. Use `!stop` if the player is stuck.");
      }
      return;
    }

    if (cmd === "nowplaying" || cmd === "np") {
      await message.channel.send({ embeds: [buildNowPlayingEmbed(player)] });
      return;
    }

    if (cmd === "queue" || cmd === "q") {
      await message.channel.send({ embeds: [buildQueueEmbed(player)] });
      return;
    }

    if (cmd === "volume" || cmd === "vol") {
      const vol = Number(args[0]);
      if (isNaN(vol) || vol < 0 || vol > 200) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xffbb00).setDescription("ℹ️ Usage: `!volume <0-200>`")] });
        return;
      }
      await player.setVolume(vol);
      await updateControlMessage(player);
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription(`🔊 Volume set to **${vol}%**`)] });
      return;
    }

    if (cmd === "loop") {
      const mode = (args[0] || "off").toLowerCase();
      if (!["off", "track", "queue"].includes(mode)) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xffbb00).setDescription("ℹ️ Usage: `!loop <off|track|queue>`")] });
        return;
      }
      await player.setRepeatMode(mode);
      await updateControlMessage(player);
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription(`🔄 Loop mode set to **${mode.toUpperCase()}**`)] });
      return;
    }

    if (cmd === "shuffle") {
      await player.queue.shuffle();
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("🔀 Queue has been shuffled.")] });
      return;
    }

    if (cmd === "clearqueue" || cmd === "clearq") {
      if (player.queue.tracks.length) {
        await player.queue.splice(0, player.queue.tracks.length);
      }
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription("🗑️ Queue has been cleared.")] });
      return;
    }

    if (cmd === "remove") {
      const index = Number(args[0]);
      if (isNaN(index)) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xffbb00).setDescription("ℹ️ Usage: `!remove <index>`")] });
        return;
      }
      const removed = await player.queue.remove(index - 1);
      if (!removed?.removed?.length) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ Invalid track index.")] });
        return;
      }
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription(`✅ Removed **${removed.removed[0]?.title ?? "Track"}** from queue.`)] });
      return;
    }

    if (cmd === "move") {
      const from = Number(args[0]);
      const to = Number(args[1]);
      if (isNaN(from) || isNaN(to)) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xffbb00).setDescription("ℹ️ Usage: `!move <from_index> <to_index>`")] });
        return;
      }
      const fromIndex = from - 1;
      const toIndex = to - 1;
      if (
        fromIndex < 0 ||
        toIndex < 0 ||
        fromIndex >= player.queue.tracks.length ||
        toIndex >= player.queue.tracks.length
      ) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ Invalid track positions.")] });
        return;
      }
      const extracted = await player.queue.splice(fromIndex, 1);
      const track = Array.isArray(extracted) ? extracted[0] : extracted;
      if (!track) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ Failed to move track.")] });
        return;
      }
      await player.queue.add(track, toIndex);
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription(`✅ Moved track to position **${to}**`)] });
      return;
    }

    if (cmd === "nodes") {
      const nodes = Array.from(manager.nodeManager?.nodes?.values() ?? []);
      if (!nodes.length) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ No music nodes connected.")] });
        return;
      }

      const embed = new EmbedBuilder()
        .setColor(0x00ff9d)
        .setTitle("📡 Music Nodes Detailed Status")
        .setTimestamp();

      const nodeInfo = nodes.map((n) => {
        const stats = n.stats || {};
        const players = n.playingPlayers ?? 0;
        const totalPlayers = n.players?.size ?? 0;
        const cpu = stats.cpu ? `${(stats.cpu.lavalinkLoad * 100).toFixed(2)}%` : "N/A";
        const memory = stats.memory ? `${(stats.memory.used / 1024 / 1024).toFixed(0)}MB` : "N/A";
        const ping = n.ping ?? "N/A";
        const status = n.connected ? "✅ Online" : "❌ Offline";
        
        return `**${n.options.id}** [${status}]\n` +
               `┕ Host: \`${n.options.host}\`\n` +
               `┕ Ping: \`${ping}ms\` | Load: \`${cpu}\` | Mem: \`${memory}\`\n` +
               `┕ Players: \`${players} live / ${totalPlayers} total\``;
      }).join("\n\n");

      embed.setDescription(nodeInfo || "Gathering node data...");
      await message.channel.send({ embeds: [embed] });
      return;
    }

    if (cmd === "autoplay" || cmd === "ap") {
      const current = autoplayState.get(message.guild.id) === true;
      autoplayState.set(message.guild.id, !current);
      await updateControlMessage(player);
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription(`📻 Autoplay is now **${!current ? "ENABLED" : "DISABLED"}**.`)] });
      return;
    }

    if (cmd === "aimode" || cmd === "ai") {
      const current = aiModeState.get(message.guild.id) === true;
      aiModeState.set(message.guild.id, !current);
      await updateControlMessage(player);
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription(`🤖 AI Mode is now **${!current ? "ENABLED" : "DISABLED"}**.`)] });
      return;
    }

    if (cmd === "vibe") {
      const vibe = args.join(" ").trim();
      if (!vibe) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xffbb00).setDescription("ℹ️ Usage: `!vibe <mood/genre/theme>`")] });
        return;
      }
      vibeState.set(message.guild.id, vibe.slice(0, 60));
      await updateControlMessage(player);
      await message.channel.send({ embeds: [new EmbedBuilder().setColor(0x00ff9d).setDescription(`✨ Vibe engine set to: **${vibe}**`)] });
      return;
    }

    if (cmd === "suggest") {
      const prompt = args.join(" ").trim();
      if (!prompt) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xffbb00).setDescription("ℹ️ Usage: `!suggest <prompt>`")] });
        return;
      }
      const res = await player.search(buildSearchQuery(prompt), message.author).catch(() => null);
      if (!res?.tracks?.length) {
        await message.channel.send({ embeds: [new EmbedBuilder().setColor(0xff0000).setDescription("❌ No suggestions found for that prompt.")] });
        return;
      }
      const embed = new EmbedBuilder()
        .setColor(0x00ff9d)
        .setTitle("💡 Music Suggestions")
        .setDescription(res.tracks.slice(0, 5).map((track, i) => `\`${i + 1}.\` **${track.title}**`).join("\n"));
      await message.channel.send({ embeds: [embed] });
      return;
    }
  },
};

export async function register(client) {
  const manager = client.lavalink;
  if (!manager) return;

  manager.on("trackStart", async (player) => {
    if (player.queue.current?.title || player.queue.current?.info?.title) {
      lastTrackTitle.set(player.guildId, String(player.queue.current?.title || player.queue.current?.info?.title));
    }
    if (player.queue.current?.info?.author) {
      lastTrackAuthor.set(player.guildId, String(player.queue.current?.info?.author));
    }
    
    // Send a fresh control message for each new track
    const discordClient = player?.LavalinkManager?.discordClient;
    if (discordClient) {
      const channelId = player.textChannelId;
      const channel = discordClient.channels.cache.get(channelId);
      if (channel) {
        const msg = await channel.send({ 
          embeds: [buildNowPlayingEmbed(player)], 
          components: buildButtons(player) 
        }).catch(() => null);
        if (msg) {
          controlState.set(player.guildId, { channelId: msg.channel.id, messageId: msg.id });
        }
      }
    }
  });

  manager.on("trackEnd", async (player) => {
    await updateControlMessage(player);
  });

  manager.on("queueEnd", async (player) => {
    const lastRequester = player.queue.current?.requester || player.queue.previous?.[0]?.requester || null;
    if (aiModeState.get(player.guildId) === true) {
      await ensureAiQueue(player, lastRequester, 3);
      if (!player.playing && !player.paused && player.queue.tracks?.length) {
        await player.play();
      }
    } else if (autoplayState.get(player.guildId) === true) {
      await ensureAiQueue(player, lastRequester, 1);
      if (!player.playing && !player.paused && player.queue.tracks?.length) {
        await player.play();
      }
    }
    await updateControlMessage(player);
  });

  manager.on("trackError", async (player) => {
    await updateControlMessage(player);
  });
}

export async function handleInteraction({ client, interaction }) {
  if (!interaction.isButton() || !interaction.customId.startsWith("music_")) {
    return false;
  }

  const player = client.lavalink?.getPlayer(interaction.guildId);
  if (!player) {
    await interaction.reply({ content: "```\n❌ Music player is not active.\n```", flags: 64 });
    return true;
  }

  if (interaction.member?.voice?.channelId !== player.voiceChannelId) {
    await interaction.reply({ content: "```\n❌ Join the same voice channel as the bot.\n```", flags: 64 });
    return true;
  }

  const action = interaction.customId;
  if (action === "music_queue") {
    await interaction.reply({ embeds: [buildQueueEmbed(player)], flags: 64 });
    return true;
  }

  await interaction.deferUpdate();

  if (action === "music_playpause") {
    if (player.paused) await player.resume();
    else await player.pause();
  } else if (action === "music_skip") {
    const hasNext = player.queue.tracks.length > 0;
    const isAutoplay = autoplayState.get(interaction.guildId) === true || aiModeState.get(interaction.guildId) === true;

    if (!hasNext && !isAutoplay) {
      return interaction.followUp({ content: "❌ No more tracks in the queue to skip to.", flags: 64 }).catch(() => {});
    }

    try {
      if (!hasNext && isAutoplay) {
        await ensureAiQueue(player, player.queue.current?.requester || interaction.user, 1);
      }
      
      if (player.queue.tracks.length > 0) {
        await player.skip();
      } else {
        await player.stopPlaying(true, false);
      }
    } catch (err) {
      console.error("Skip interaction error:", err);
    }
  } else if (action === "music_stop") {
    await player.stopPlaying(true, false);
  } else if (action === "music_loop") {
    const current = player.repeatMode ?? "off";
    const next = current === "off" ? "track" : current === "track" ? "queue" : "off";
    await player.setRepeatMode(next);
  } else if (action === "music_shuffle") {
    await player.queue.shuffle();
  } else if (action === "music_autoplay") {
    const current = autoplayState.get(interaction.guildId) === true;
    autoplayState.set(interaction.guildId, !current);
  } else if (action === "music_ai") {
    const current = aiModeState.get(interaction.guildId) === true;
    aiModeState.set(interaction.guildId, !current);
  } else if (action === "music_voldown") {
    await player.setVolume(Math.max(0, player.volume - 10));
  } else if (action === "music_volup") {
    await player.setVolume(Math.min(200, player.volume + 10));
  }

  await updateControlMessage(player);
  return true;
}
