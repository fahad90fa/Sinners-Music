import discord
from discord.ext import commands
import wavelink
import asyncio
import json
import os
import random
from collections import deque
from typing import Deque, Dict, Optional, Tuple


class MusicControlView(discord.ui.View):
    def __init__(self, cog: "Music", guild_id: int):
        super().__init__(timeout=900)
        self.cog = cog
        self.guild_id = guild_id

    async def _get_player(self, interaction: discord.Interaction) -> Optional[wavelink.Player]:
        guild = interaction.guild
        if not guild:
            return None
        player = guild.voice_client
        if not player:
            await interaction.response.send_message("```\\n❌ I am not in a voice channel.\\n```", ephemeral=True)
            return None
        if interaction.user and interaction.user.voice and interaction.user.voice.channel:
            if player.channel != interaction.user.voice.channel:
                await interaction.response.send_message(
                    "```\\n❌ You must be in the same voice channel as the bot.\\n```",
                    ephemeral=True,
                )
                return None
        else:
            await interaction.response.send_message("```\\n❌ Join a voice channel first.\\n```", ephemeral=True)
            return None
        return player

    async def _safe_defer(self, interaction: discord.Interaction) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(label="Play/Pause", style=discord.ButtonStyle.primary, custom_id="music_playpause")
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._get_player(interaction)
        if not player:
            return
        await self._safe_defer(interaction)
        if player.paused:
            await player.pause(False)
        else:
            await player.pause(True)
        await self.cog._refresh_now_playing_message(player.guild)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, custom_id="music_skip")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._get_player(interaction)
        if not player:
            return
        await self._safe_defer(interaction)
        await player.skip()

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, custom_id="music_stop")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._get_player(interaction)
        if not player:
            return
        await self._safe_defer(interaction)
        self.cog._get_queue(player.guild.id).clear()
        await player.skip()
        await self.cog._refresh_now_playing_message(player.guild)

    @discord.ui.button(label="Loop", style=discord.ButtonStyle.secondary, custom_id="music_loop")
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._get_player(interaction)
        if not player:
            return
        await self._safe_defer(interaction)
        current = self.cog._get_loop_mode(self.guild_id)
        next_mode = {"off": "track", "track": "queue", "queue": "off"}[current]
        self.cog._set_loop_mode(self.guild_id, next_mode)
        await self.cog._refresh_now_playing_message(player.guild)

    @discord.ui.button(label="Shuffle", style=discord.ButtonStyle.secondary, custom_id="music_shuffle")
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._get_player(interaction)
        if not player:
            return
        await self._safe_defer(interaction)
        queue = self.cog._get_queue(self.guild_id)
        if len(queue) > 1:
            items = list(queue)
            queue.clear()
            random.shuffle(items)
            queue.extend(items)
        await self.cog._refresh_now_playing_message(player.guild)

    @discord.ui.button(label="Vol -", style=discord.ButtonStyle.secondary, custom_id="music_voldown")
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._get_player(interaction)
        if not player:
            return
        await self._safe_defer(interaction)
        new_vol = max(0, player.volume - 10)
        await player.set_volume(new_vol)
        await self.cog._refresh_now_playing_message(player.guild)

    @discord.ui.button(label="Vol +", style=discord.ButtonStyle.secondary, custom_id="music_volup")
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._get_player(interaction)
        if not player:
            return
        await self._safe_defer(interaction)
        new_vol = min(200, player.volume + 10)
        await player.set_volume(new_vol)
        await self.cog._refresh_now_playing_message(player.guild)

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.secondary, custom_id="music_queue")
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = await self._get_player(interaction)
        if not player:
            return
        queue = list(self.cog._get_queue(self.guild_id))
        lines = []
        if player.current:
            lines.append(f"Now: {player.current.title}")
        for idx, track in enumerate(queue[:10], start=1):
            lines.append(f"{idx}. {track.title}")
        if len(queue) > 10:
            lines.append(f"...and {len(queue) - 10} more")
        if not lines:
            lines = ["Queue is empty."]
        await interaction.response.send_message("```\n" + "\n".join(lines) + "\n```", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: Dict[int, Deque[wavelink.Playable]] = {}
        self.loop_mode: Dict[int, str] = {}
        self.control_messages: Dict[int, Tuple[int, int]] = {}
        self.last_voice_channel: Dict[int, int] = {}
        self.reconnect_tasks: Dict[int, asyncio.Task] = {}

    def _get_queue(self, guild_id: int) -> Deque[wavelink.Playable]:
        return self.queues.setdefault(guild_id, deque())

    def _get_loop_mode(self, guild_id: int) -> str:
        return self.loop_mode.get(guild_id, "off")

    def _set_loop_mode(self, guild_id: int, mode: str) -> None:
        self.loop_mode[guild_id] = mode

    def _load_config(self) -> dict:
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    async def _log(self, message: str) -> None:
        cfg = self._load_config()
        channel_id = cfg.get("log_channel")
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(f"```\n{message}\n```")

    def _node_configs(self) -> list:
        cfg = self._load_config()

        # Explicit env vars override everything (single node).
        if os.getenv("LAVALINK_HOST"):
            host = os.getenv("LAVALINK_HOST")
            port = int(os.getenv("LAVALINK_PORT", 2333))
            password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
            https_env = os.getenv("LAVALINK_HTTPS")
            https = https_env.lower() in ("1", "true", "yes", "on") if https_env else False
            return [{
                "identifier": "env-node",
                "host": host,
                "port": port,
                "password": password,
                "https": https,
            }]

        nodes = cfg.get("lavalink_nodes", [])
        if nodes:
            return nodes

        single = cfg.get("lavalink", {})
        return [{
            "identifier": "default-node",
            "host": single.get("host", "127.0.0.1"),
            "port": int(single.get("port", 2333)),
            "password": single.get("password", "youshallnotpass"),
            "https": bool(single.get("https", False)),
        }]

    async def _ensure_node(self) -> None:
        if wavelink.Pool.nodes:
            return
        nodes = []
        for node_cfg in self._node_configs():
            scheme = "https" if node_cfg.get("https") else "http"
            uri = f"{scheme}://{node_cfg['host']}:{node_cfg['port']}"
            nodes.append(
                wavelink.Node(
                    uri=uri,
                    password=node_cfg["password"],
                    identifier=node_cfg.get("identifier"),
                )
            )
        await wavelink.Pool.connect(nodes=nodes, client=self.bot)

    async def _get_player(self, ctx: commands.Context) -> Optional[wavelink.Player]:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("```\n❌ You need to join a voice channel first.\n```")
            return None

        player = ctx.voice_client
        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            except wavelink.InvalidChannelStateException:
                await ctx.send("```\n❌ I can't join that channel (permissions or invalid state).\n```")
                return None
            except wavelink.ChannelTimeoutException:
                await ctx.send("```\n❌ Timed out while connecting to voice.\n```")
                return None
            except Exception as e:
                await ctx.send(f"```\n❌ Failed to connect: {e}\n```")
                return None
        elif player.channel != ctx.author.voice.channel:
            await ctx.send("```\n❌ You must be in the same voice channel as the bot.\n```")
            return None
        player.autoplay = wavelink.AutoPlayMode.disabled
        player.text_channel = ctx.channel
        self.last_voice_channel[ctx.guild.id] = ctx.author.voice.channel.id
        return player

    async def _start_next(self, player: wavelink.Player) -> None:
        if player.playing:
            return
        queue = self._get_queue(player.guild.id)
        if not queue:
            return
        track = queue.popleft()
        try:
            await player.play(track)
        except Exception as e:
            await self._log(f"Play failed in guild {player.guild.id}: {e}")

    async def _refresh_now_playing_message(self, guild: discord.Guild) -> None:
        info = self.control_messages.get(guild.id)
        if not info:
            return
        channel_id, message_id = info
        channel = guild.get_channel(channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(message_id)
        except Exception:
            return
        embed = self._build_now_playing_embed(guild)
        view = MusicControlView(self, guild.id)
        try:
            await message.edit(embed=embed, view=view)
        except Exception:
            pass

    def _build_now_playing_embed(self, guild: discord.Guild) -> discord.Embed:
        player = guild.voice_client
        embed = discord.Embed(
            title="Music Control Center",
            color=0x00FF9D,
            timestamp=discord.utils.utcnow(),
        )
        if not player or not player.current:
            embed.description = "No track is currently playing."
            return embed

        track = player.current
        duration = self._format_duration(track.length)
        loop_mode = self._get_loop_mode(guild.id)
        requester_id = None
        try:
            requester_id = track.extras.get("requester")
        except Exception:
            requester_id = None

        embed.add_field(name="Now Playing", value=track.title, inline=False)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Volume", value=f"{player.volume}%", inline=True)
        embed.add_field(name="Loop", value=loop_mode, inline=True)

        if requester_id:
            embed.add_field(name="Requested By", value=f"<@{requester_id}>", inline=True)
        if track.uri:
            embed.add_field(name="Link", value=track.uri, inline=False)

        return embed

    def _format_duration(self, milliseconds: int) -> str:
        seconds = int(milliseconds / 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02}:{seconds:02}"
        return f"{minutes}:{seconds:02}"

    def _parse_time(self, value: str) -> Optional[int]:
        value = value.strip()
        if value.isdigit():
            return int(value) * 1000
        if ":" in value:
            parts = value.split(":")
            if not all(p.isdigit() for p in parts):
                return None
            parts = [int(p) for p in parts]
            seconds = 0
            for part in parts:
                seconds = seconds * 60 + part
            return seconds * 1000
        return None

    @commands.Cog.listener()
    async def on_ready(self):
        await self._ensure_node()

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        await self._log(f"Lavalink node ready: {payload.node.identifier}")

    @commands.Cog.listener()
    async def on_wavelink_node_closed(self, node: wavelink.Node, disconnected: list[wavelink.Player]):
        await self._log(f"Lavalink node closed: {node.identifier} | disconnected={len(disconnected)}")

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        player = payload.player
        guild_id = player.guild.id if player and player.guild else "unknown"
        await self._log(f"Lavalink track exception | guild={guild_id} | {payload.exception}")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        guild_id = player.guild.id
        mode = self._get_loop_mode(guild_id)

        original = payload.original or payload.track
        if mode == "track" and original:
            await player.play(original)
            return
        if mode == "queue" and original:
            self._get_queue(guild_id).append(original)

        await self._start_next(player)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player = payload.player
        if not player:
            return
        guild = player.guild
        embed = self._build_now_playing_embed(guild)
        view = MusicControlView(self, guild.id)

        info = self.control_messages.get(guild.id)
        if info:
            channel_id, message_id = info
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    await message.edit(embed=embed, view=view)
                    return
                except Exception:
                    pass

        channel = getattr(player, "text_channel", None)
        if not channel:
            return
        message = await channel.send(embed=embed, view=view)
        self.control_messages[guild.id] = (channel.id, message.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if not member or not member.guild:
            return
        if member.id != self.bot.user.id:
            return
        guild_id = member.guild.id

        if before.channel and not after.channel:
            await self._log(f"Voice disconnect in guild {guild_id} from {before.channel.id}")
            queue = self._get_queue(guild_id)
            if queue:
                if guild_id not in self.reconnect_tasks or self.reconnect_tasks[guild_id].done():
                    self.reconnect_tasks[guild_id] = asyncio.create_task(self._attempt_reconnect(member.guild, before.channel.id))
        elif after.channel:
            await self._log(f"Voice connected in guild {guild_id} to {after.channel.id}")

    async def _attempt_reconnect(self, guild: discord.Guild, channel_id: int):
        await asyncio.sleep(2)
        channel = guild.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.VoiceChannel):
            await self._log(f"Reconnect failed: channel {channel_id} not found.")
            return
        try:
            await channel.connect(cls=wavelink.Player)
            await self._log(f"Reconnected to voice channel {channel_id}.")
        except Exception as e:
            await self._log(f"Reconnect error in guild {guild.id}: {e}")

    @commands.command(name="join", aliases=["summon"])
    async def join(self, ctx: commands.Context):
        """Join your voice channel."""
        await self._ensure_node()
        player = await self._get_player(ctx)
        if not player:
            return
        await ctx.send(f"```\n✅ Joined {player.channel.name}\n```")

    @commands.command(name="leave", aliases=["disconnect"])
    async def leave(self, ctx: commands.Context):
        """Leave the voice channel."""
        player = ctx.voice_client
        if not player:
            await ctx.send("```\n❌ I am not in a voice channel.\n```")
            return
        self._get_queue(ctx.guild.id).clear()
        await player.disconnect()
        await ctx.send("```\n✅ Disconnected.\n```")

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song or add it to the queue."""
        await self._ensure_node()
        player = await self._get_player(ctx)
        if not player:
            return

        results = await wavelink.Playable.search(query)
        if not results:
            await ctx.send("```\n❌ No results found.\n```")
            return

        queue = self._get_queue(ctx.guild.id)

        if isinstance(results, wavelink.Playlist):
            for track in results.tracks:
                track.extras = {"requester": ctx.author.id}
                queue.append(track)
            await ctx.send(f"```\n✅ Added playlist: {results.name} ({len(results.tracks)} tracks)\n```")
            await self._start_next(player)
            return

        track = results[0]
        track.extras = {"requester": ctx.author.id}
        queue.append(track)

        if not player.playing:
            await self._start_next(player)
            await ctx.send(f"```\n▶️ Now playing: {track.title}\n```")
        else:
            await ctx.send(f"```\n✅ Queued: {track.title}\n```")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        """Pause playback."""
        player = ctx.voice_client
        if not player or not player.playing:
            await ctx.send("```\n❌ Nothing is playing.\n```")
            return
        await player.pause(True)
        await ctx.send("```\n⏸️ Paused.\n```")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        """Resume playback."""
        player = ctx.voice_client
        if not player or not player.paused:
            await ctx.send("```\n❌ Nothing is paused.\n```")
            return
        await player.pause(False)
        await ctx.send("```\n▶️ Resumed.\n```")

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
        """Stop playback and clear the queue."""
        player = ctx.voice_client
        if not player:
            await ctx.send("```\n❌ Nothing is playing.\n```")
            return
        self._get_queue(ctx.guild.id).clear()
        await player.skip()
        await ctx.send("```\n⏹️ Stopped and cleared the queue.\n```")

    @commands.command(name="skip", aliases=["next"])
    async def skip(self, ctx: commands.Context):
        """Skip the current track."""
        player = ctx.voice_client
        if not player or not player.playing:
            await ctx.send("```\n❌ Nothing is playing.\n```")
            return
        await player.skip()
        await ctx.send("```\n⏭️ Skipped.\n```")

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx: commands.Context):
        """Show the current track."""
        player = ctx.voice_client
        if not player or not player.current:
            await ctx.send("```\n❌ Nothing is playing.\n```")
            return
        track = player.current
        duration = self._format_duration(track.length)
        await ctx.send(f"```\n🎵 Now Playing: {track.title}\n⏱️ Duration: {duration}\n```")

    @commands.command(name="queue", aliases=["q"])
    async def show_queue(self, ctx: commands.Context):
        """Show the queue."""
        queue = list(self._get_queue(ctx.guild.id))
        player = ctx.voice_client
        if not player or (not player.current and not queue):
            await ctx.send("```\n❌ Queue is empty.\n```")
            return

        lines = []
        if player and player.current:
            lines.append(f"Now: {player.current.title}")

        for idx, track in enumerate(queue[:10], start=1):
            lines.append(f"{idx}. {track.title}")

        if len(queue) > 10:
            lines.append(f"...and {len(queue) - 10} more")

        await ctx.send("```\n" + "\n".join(lines) + "\n```")

    @commands.command(name="volume", aliases=["vol"])
    async def volume(self, ctx: commands.Context, value: int):
        """Set the player volume (0-200)."""
        player = ctx.voice_client
        if not player:
            await ctx.send("```\n❌ Nothing is playing.\n```")
            return
        if value < 0 or value > 200:
            await ctx.send("```\n❌ Volume must be between 0 and 200.\n```")
            return
        await player.set_volume(value)
        await ctx.send(f"```\n🔊 Volume set to {value}%.\n```")

    @commands.command(name="seek")
    async def seek(self, ctx: commands.Context, position: str):
        """Seek to a position (seconds or mm:ss)."""
        player = ctx.voice_client
        if not player or not player.current:
            await ctx.send("```\n❌ Nothing is playing.\n```")
            return
        ms = self._parse_time(position)
        if ms is None:
            await ctx.send("```\n❌ Invalid time. Use seconds or mm:ss.\n```")
            return
        await player.seek(ms)
        await ctx.send(f"```\n⏩ Seeked to {position}.\n```")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the queue."""
        queue = self._get_queue(ctx.guild.id)
        if len(queue) < 2:
            await ctx.send("```\n❌ Not enough tracks to shuffle.\n```")
            return
        items = list(queue)
        queue.clear()
        random.shuffle(items)
        queue.extend(items)
        await ctx.send("```\n🔀 Queue shuffled.\n```")

    @commands.command(name="loop")
    async def loop(self, ctx: commands.Context, mode: str):
        """Set loop mode: off, track, queue."""
        mode = mode.lower()
        if mode not in ("off", "track", "queue"):
            await ctx.send("```\n❌ Invalid loop mode. Use: off, track, queue.\n```")
            return
        self._set_loop_mode(ctx.guild.id, mode)
        await ctx.send(f"```\n🔁 Loop mode set to {mode}.\n```")

    @commands.command(name="remove")
    async def remove(self, ctx: commands.Context, index: int):
        """Remove a track from the queue by index."""
        queue = self._get_queue(ctx.guild.id)
        if index < 1 or index > len(queue):
            await ctx.send("```\n❌ Invalid queue index.\n```")
            return
        items = list(queue)
        removed = items.pop(index - 1)
        queue.clear()
        queue.extend(items)
        await ctx.send(f"```\n🗑️ Removed: {removed.title}\n```")

    @commands.command(name="move")
    async def move(self, ctx: commands.Context, index: int, new_index: int):
        """Move a track in the queue."""
        queue = self._get_queue(ctx.guild.id)
        if index < 1 or index > len(queue) or new_index < 1 or new_index > len(queue):
            await ctx.send("```\n❌ Invalid queue index.\n```")
            return
        items = list(queue)
        track = items.pop(index - 1)
        items.insert(new_index - 1, track)
        queue.clear()
        queue.extend(items)
        await ctx.send(f"```\n✅ Moved track to position {new_index}.\n```")

    @commands.command(name="clearqueue", aliases=["clearq"])
    async def clearqueue(self, ctx: commands.Context):
        """Clear the queue."""
        queue = self._get_queue(ctx.guild.id)
        if not queue:
            await ctx.send("```\n❌ Queue is already empty.\n```")
            return
        queue.clear()
        await ctx.send("```\n✅ Queue cleared.\n```")

    @commands.command(name="nodes")
    async def nodes(self, ctx: commands.Context):
        """Show Lavalink node status."""
        nodes = list(wavelink.NodePool.nodes.values())
        if not nodes:
            await ctx.send("```\n❌ No Lavalink nodes are connected.\n```")
            return
        lines = []
        for node in nodes:
            try:
                stats = getattr(node, "stats", None)
                players = getattr(stats, "players", "N/A") if stats else "N/A"
                playing = getattr(stats, "playing_players", "N/A") if stats else "N/A"
                uptime = getattr(stats, "uptime", None) if stats else None
                uptime_s = int(uptime / 1000) if uptime is not None else None
                uptime_text = f"{uptime_s}s" if uptime_s is not None else "N/A"
            except Exception:
                players = "N/A"
                playing = "N/A"
                uptime_text = "N/A"

            lines.append(
                f"{node.identifier} | {node.host}:{node.port} | players={players} playing={playing} uptime={uptime_text}"
            )
        await ctx.send("```\n" + "\n".join(lines) + "\n```")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "```\n"
                f"❌ Missing argument: {error.param.name}\n"
                f"Usage: !{ctx.command.qualified_name} {ctx.command.signature}\n"
                "```"
            )
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "```\n"
                "❌ Invalid argument provided.\n"
                f"Usage: !{ctx.command.qualified_name} {ctx.command.signature}\n"
                "```"
            )
            return
        raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
