import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import asyncio
from typing import Optional
import io
import aiohttp


class AdvancedCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}  # Store AFK users {user_id: {'reason': str, 'time': datetime}}
        self.afk_file = "database/afk_users.json"
        self.load_afk_users()
    
    def load_afk_users(self):
        """Load AFK users from JSON file"""
        try:
            with open(self.afk_file, 'r') as f:
                data = json.load(f)
                # Convert ISO timestamps back to datetime
                for user_id, info in data.items():
                    self.afk_users[int(user_id)] = {
                        'reason': info['reason'],
                        'time': datetime.fromisoformat(info['time'])
                    }
        except FileNotFoundError:
            self.afk_users = {}
    
    def save_afk_users(self):
        """Save AFK users to JSON file"""
        data = {}
        for user_id, info in self.afk_users.items():
            data[str(user_id)] = {
                'reason': info['reason'],
                'time': info['time'].isoformat()
            }
        
        try:
            with open(self.afk_file, 'w') as f:
                json.dump(data, f, indent=4)
        except:
            pass
    
    # ============================================================
    #                    !AV (AVATAR) COMMAND
    # ============================================================
    
    @commands.command(name='av', aliases=['avatar', 'pfp', 'profilepic'])
    async def avatar(self, ctx, user: Optional[discord.Member] = None):
        """
        Display user's avatar in high quality with multiple formats
        Usage: !av [@user]
        """
        
        target = user or ctx.author
        
        # Get avatar URLs in different formats
        avatar_url = target.display_avatar.url
        avatar_png = target.display_avatar.replace(format='png', size=4096).url
        avatar_jpg = target.display_avatar.replace(format='jpg', size=4096).url
        avatar_webp = target.display_avatar.replace(format='webp', size=4096).url
        
        # Check if user has GIF avatar
        is_animated = target.display_avatar.is_animated()
        if is_animated:
            avatar_gif = target.display_avatar.replace(format='gif', size=4096).url
        
        # Create main embed
        embed = discord.Embed(
            title="",
            description="",
            color=target.color if target.color != discord.Color.default() else discord.Color.random(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(
            name=f"{target.name}'s Avatar",
            icon_url=target.display_avatar.url
        )
        
        # Avatar preview
        embed.set_image(url=avatar_url)
        
        # User info section
        embed.add_field(
            name="👤 User Information",
            value=(
                f"```yaml\n"
                f"Username    : {target.name}\n"
                f"Display Name: {target.display_name}\n"
                f"User ID     : {target.id}\n"
                f"Bot Account : {'Yes' if target.bot else 'No'}\n"
                f"Animated    : {'Yes' if is_animated else 'No'}\n"
                f"```"
            ),
            inline=False
        )
        
        # Download links
        download_links = (
            f"[PNG (4096x4096)]({avatar_png}) • "
            f"[JPG (4096x4096)]({avatar_jpg}) • "
            f"[WEBP (4096x4096)]({avatar_webp})"
        )
        
        if is_animated:
            download_links += f" • [GIF (4096x4096)]({avatar_gif})"
        
        embed.add_field(
            name="🔗 Download Links",
            value=download_links,
            inline=False
        )
        
        # Avatar analysis
        embed.add_field(
            name="📊 Avatar Details",
            value=(
                f"```ini\n"
                f"[Format]     = {avatar_url.split('.')[-1].split('?')[0].upper()}\n"
                f"[Max Size]   = 4096x4096\n"
                f"[Type]       = {'Animated GIF' if is_animated else 'Static Image'}\n"
                f"[URL Length] = {len(avatar_url)} chars\n"
                f"```"
            ),
            inline=False
        )
        
        # Server avatar if different
        if ctx.guild and target.guild_avatar:
            embed.add_field(
                name="🏰 Server Avatar",
                value=f"[View Server Avatar]({target.guild_avatar.url})\n*Different from global avatar*",
                inline=False
            )
        
        embed.set_footer(
            text=f"Requested by {ctx.author.name} • ZeroDay Tool",
            icon_url=ctx.author.display_avatar.url
        )
        
        # Create button view
        view = AvatarButtonView(target)
        
        await ctx.send(embed=embed, view=view)
    
    # ============================================================
    #                    !AFK COMMAND
    # ============================================================
    
    @commands.command(name='afk')
    async def set_afk(self, ctx, *, reason: str = "AFK"):
        """
        Set yourself as AFK with an optional reason
        Usage: !afk [reason]
        """
        
        # Store AFK status
        self.afk_users[ctx.author.id] = {
            'reason': reason[:100],  # Limit reason length
            'time': datetime.utcnow()
        }
        
        self.save_afk_users()
        
        # Create AFK embed
        afk_embed = discord.Embed(
            title="😴 AFK Status Set",
            description="",
            color=0xFFA500,
            timestamp=datetime.utcnow()
        )
        
        afk_embed.set_author(
            name=ctx.author.name,
            icon_url=ctx.author.display_avatar.url
        )
        
        afk_embed.add_field(
            name="📝 Reason",
            value=f"```{reason}```",
            inline=False
        )
        
        afk_embed.add_field(
            name="⏰ Started",
            value=f"<t:{int(datetime.utcnow().timestamp())}:R>",
            inline=True
        )
        
        afk_embed.add_field(
            name="👤 User",
            value=f"{ctx.author.mention}",
            inline=True
        )
        
        afk_embed.add_field(
            name="💡 Info",
            value=(
                "```yaml\n"
                "• You will be marked as AFK\n"
                "• Sending any message removes AFK\n"
                "• Others will be notified when mentioning you\n"
                "• Nickname will show [AFK] tag\n"
                "```"
            ),
            inline=False
        )
        
        afk_embed.set_footer(
            text="Send any message to remove AFK status",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )
        
        await ctx.send(embed=afk_embed)
        
        # Try to add [AFK] tag to nickname
        try:
            if not ctx.author.display_name.startswith('[AFK]'):
                new_nick = f"[AFK] {ctx.author.display_name}"[:32]  # Discord nickname limit
                await ctx.author.edit(nick=new_nick)
        except discord.Forbidden:
            pass
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle AFK status removal and mentions"""
        
        if message.author.bot:
            return
        
        # Check if user is AFK and sent a message (remove AFK)
        if message.author.id in self.afk_users:
            # Don't remove AFK if it's the !afk command itself
            if not message.content.startswith(('!afk', '?afk', '.afk')):
                afk_data = self.afk_users[message.author.id]
                afk_duration = datetime.utcnow() - afk_data['time']
                
                # Remove from AFK list
                del self.afk_users[message.author.id]
                self.save_afk_users()
                
                # Calculate duration
                hours, remainder = divmod(int(afk_duration.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                duration_str = ""
                if hours > 0:
                    duration_str += f"{hours}h "
                if minutes > 0:
                    duration_str += f"{minutes}m "
                duration_str += f"{seconds}s"
                
                # Send welcome back message
                welcome_embed = discord.Embed(
                    title="👋 Welcome Back!",
                    description=f"{message.author.mention} is no longer AFK",
                    color=0x00FF00
                )
                
                welcome_embed.add_field(
                    name="⏱️ AFK Duration",
                    value=f"```{duration_str}```",
                    inline=True
                )
                
                welcome_embed.add_field(
                    name="📝 Reason",
                    value=f"```{afk_data['reason']}```",
                    inline=True
                )
                
                welcome_embed.set_footer(text="AFK status removed automatically")
                
                await message.channel.send(embed=welcome_embed, delete_after=10)
                
                # Remove [AFK] tag from nickname
                try:
                    if message.author.display_name.startswith('[AFK]'):
                        new_nick = message.author.display_name.replace('[AFK] ', '', 1)
                        await message.author.edit(nick=new_nick if new_nick != message.author.name else None)
                except discord.Forbidden:
                    pass
        
        # Check if message mentions any AFK users
        for mentioned_user in message.mentions:
            if mentioned_user.id in self.afk_users:
                afk_data = self.afk_users[mentioned_user.id]
                afk_duration = datetime.utcnow() - afk_data['time']
                
                hours, remainder = divmod(int(afk_duration.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                duration_str = ""
                if hours > 0:
                    duration_str += f"{hours}h "
                if minutes > 0:
                    duration_str += f"{minutes}m "
                duration_str += f"{seconds}s"
                
                afk_notice = discord.Embed(
                    title="💤 User is AFK",
                    description=f"{mentioned_user.mention} is currently AFK",
                    color=0xFFA500
                )
                
                afk_notice.add_field(
                    name="📝 Reason",
                    value=f"```{afk_data['reason']}```",
                    inline=False
                )
                
                afk_notice.add_field(
                    name="⏰ Duration",
                    value=f"```{duration_str}```",
                    inline=True
                )
                
                afk_notice.add_field(
                    name="🕐 Since",
                    value=f"<t:{int(afk_data['time'].timestamp())}:R>",
                    inline=True
                )
                
                afk_notice.set_footer(text="They will be notified when they return")
                
                await message.channel.send(embed=afk_notice, delete_after=15)
    
    # ============================================================
    #                    !BANNER COMMAND
    # ============================================================
    
    @commands.command(name='banner', aliases=['userbanner', 'ub'])
    async def user_banner(self, ctx, user: Optional[discord.User] = None):
        """
        Display user's profile banner
        Usage: !banner [@user]
        """
        
        target = user or ctx.author
        
        # Fetch full user to get banner
        try:
            fetched_user = await self.bot.fetch_user(target.id)
        except:
            await ctx.send("```\n❌ Could not fetch user data!\n```")
            return
        
        # Check if user has a banner
        if not fetched_user.banner:
            no_banner_embed = discord.Embed(
                title="❌ No Banner",
                description=f"{target.mention} does not have a profile banner set.",
                color=0xFF0000
            )
            
            no_banner_embed.set_thumbnail(url=target.display_avatar.url)
            
            no_banner_embed.add_field(
                name="💡 How to Set Banner",
                value=(
                    "```\n"
                    "1. Subscribe to Discord Nitro\n"
                    "2. Go to User Settings\n"
                    "3. Click 'Edit Profile'\n"
                    "4. Upload banner image\n"
                    "```"
                ),
                inline=False
            )
            
            await ctx.send(embed=no_banner_embed)
            return
        
        # Get banner URLs
        banner_url = fetched_user.banner.url
        banner_png = fetched_user.banner.replace(format='png', size=4096).url
        banner_jpg = fetched_user.banner.replace(format='jpg', size=4096).url
        banner_webp = fetched_user.banner.replace(format='webp', size=4096).url
        
        is_animated = fetched_user.banner.is_animated()
        if is_animated:
            banner_gif = fetched_user.banner.replace(format='gif', size=4096).url
        
        # Get accent color
        accent_color = fetched_user.accent_color or discord.Color.random()
        
        # Create banner embed
        embed = discord.Embed(
            title="",
            description="",
            color=accent_color,
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(
            name=f"{target.name}'s Banner",
            icon_url=target.display_avatar.url
        )
        
        embed.set_image(url=banner_url)
        
        # User info
        embed.add_field(
            name="👤 User Details",
            value=(
                f"```yaml\n"
                f"Username     : {target.name}\n"
                f"Display Name : {target.display_name}\n"
                f"User ID      : {target.id}\n"
                f"Nitro Status : Active (Has Banner)\n"
                f"Animated     : {'Yes' if is_animated else 'No'}\n"
                f"```"
            ),
            inline=False
        )
        
        # Download links
        download_links = (
            f"[PNG]({banner_png}) • "
            f"[JPG]({banner_jpg}) • "
            f"[WEBP]({banner_webp})"
        )
        
        if is_animated:
            download_links += f" • [GIF]({banner_gif})"
        
        embed.add_field(
            name="🔗 Download Links (4096x4096)",
            value=download_links,
            inline=False
        )
        
        # Color info
        if fetched_user.accent_color:
            hex_color = f"#{fetched_user.accent_color.value:06x}"
            rgb = fetched_user.accent_color.to_rgb()
            
            embed.add_field(
                name="🎨 Accent Color",
                value=(
                    f"```ini\n"
                    f"[HEX] = {hex_color}\n"
                    f"[RGB] = rgb({rgb[0]}, {rgb[1]}, {rgb[2]})\n"
                    f"[DEC] = {fetched_user.accent_color.value}\n"
                    f"```"
                ),
                inline=False
            )
        
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        # Create button view
        view = BannerButtonView(fetched_user)
        
        await ctx.send(embed=embed, view=view)
    
    # ============================================================
    #                    !USERINFO COMMAND
    # ============================================================
    
    @commands.command(name='userinfo', aliases=['ui', 'whois', 'user', 'memberinfo'])
    async def user_info(self, ctx, user: Optional[discord.Member] = None):
        """
        Display comprehensive user information
        Usage: !userinfo [@user]
        """
        
        target = user or ctx.author
        
        # Fetch full user data
        try:
            fetched_user = await self.bot.fetch_user(target.id)
        except:
            fetched_user = target
        
        # Calculate account age
        account_age = datetime.utcnow() - target.created_at.replace(tzinfo=None)
        account_days = account_age.days
        
        # Calculate join age (if in guild)
        if ctx.guild and target.joined_at:
            join_age = datetime.utcnow() - target.joined_at.replace(tzinfo=None)
            join_days = join_age.days
            
            # Calculate join position
            members_sorted = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.utcnow())
            join_position = members_sorted.index(target) + 1
        else:
            join_days = 0
            join_position = 0
        
        # Determine user status
        status_emoji = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🟡 Idle",
            discord.Status.dnd: "🔴 Do Not Disturb",
            discord.Status.offline: "⚫ Offline"
        }
        
        status = status_emoji.get(target.status, "⚫ Unknown")
        
        # Get badges
        badges = []
        if target.public_flags:
            flag_mapping = {
                'staff': '<:staff:1234567890> Discord Staff',
                'partner': '<:partner:1234567890> Partnered Server Owner',
                'hypesquad': '<:hypesquad:1234567890> HypeSquad Events',
                'bug_hunter': '<:bughunter:1234567890> Bug Hunter',
                'hypesquad_bravery': '🟦 HypeSquad Bravery',
                'hypesquad_brilliance': '🟪 HypeSquad Brilliance',
                'hypesquad_balance': '🟩 HypeSquad Balance',
                'early_supporter': '<:earlysupporter:1234567890> Early Supporter',
                'verified_bot_developer': '<:developer:1234567890> Early Verified Bot Developer',
                'discord_certified_moderator': '<:moderator:1234567890> Discord Certified Moderator',
                'active_developer': '<:activedev:1234567890> Active Developer'
            }
            
            for flag, emoji in flag_mapping.items():
                if getattr(target.public_flags, flag, False):
                    badges.append(emoji)
        
        # Check for Nitro
        if hasattr(fetched_user, 'banner') and fetched_user.banner:
            badges.append('💎 Nitro')
        
        # Check for boost status
        if ctx.guild and target.premium_since:
            badges.append('💖 Server Booster')
        
        # Main embed
        embed = discord.Embed(
            title="",
            description="",
            color=target.color if target.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(
            name=f"{target.name}'s Information",
            icon_url=target.display_avatar.url
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Basic info
        embed.add_field(
            name="📋 Basic Information",
            value=(
                f"```yaml\n"
                f"Username     : {target.name}\n"
                f"Display Name : {target.display_name}\n"
                f"User ID      : {target.id}\n"
                f"Bot Account  : {'Yes ✅' if target.bot else 'No ❌'}\n"
                f"Status       : {status}\n"
                f"```"
            ),
            inline=False
        )
        
        # Account dates
        embed.add_field(
            name="📅 Account Information",
            value=(
                f"**Created:** <t:{int(target.created_at.timestamp())}:F>\n"
                f"**Age:** `{account_days} days old`\n"
                f"**Relative:** <t:{int(target.created_at.timestamp())}:R>"
            ),
            inline=True
        )
        
        # Server join info
        if ctx.guild and target.joined_at:
            embed.add_field(
                name="🏰 Server Information",
                value=(
                    f"**Joined:** <t:{int(target.joined_at.timestamp())}:F>\n"
                    f"**Duration:** `{join_days} days`\n"
                    f"**Join Position:** `#{join_position}`"
                ),
                inline=True
            )
        
        # Badges
        if badges:
            embed.add_field(
                name=f"🎖️ Badges ({len(badges)})",
                value=" ".join(badges),
                inline=False
            )
        
        # Roles (if in guild)
        if ctx.guild and len(target.roles) > 1:
            roles = [role.mention for role in sorted(target.roles[1:], reverse=True)]
            roles_text = " ".join(roles[:15])
            
            if len(target.roles) > 16:
                roles_text += f" **+{len(target.roles) - 16} more**"
            
            embed.add_field(
                name=f"🎭 Roles ({len(target.roles) - 1})",
                value=roles_text,
                inline=False
            )
        
        # Permissions (top 10)
        if ctx.guild:
            perms = target.guild_permissions
            important_perms = []
            
            perm_list = [
                ('administrator', 'Administrator'),
                ('manage_guild', 'Manage Server'),
                ('manage_roles', 'Manage Roles'),
                ('manage_channels', 'Manage Channels'),
                ('kick_members', 'Kick Members'),
                ('ban_members', 'Ban Members'),
                ('manage_messages', 'Manage Messages'),
                ('mention_everyone', 'Mention Everyone'),
                ('manage_webhooks', 'Manage Webhooks'),
                ('manage_emojis', 'Manage Emojis')
            ]
            
            for perm, name in perm_list:
                if getattr(perms, perm, False):
                    important_perms.append(f"✅ {name}")
            
            if important_perms:
                embed.add_field(
                    name="🔑 Key Permissions",
                    value="\n".join(important_perms[:10]),
                    inline=True
                )
        
        # Boost info
        if ctx.guild and target.premium_since:
            embed.add_field(
                name="💖 Server Boost",
                value=(
                    f"**Boosting Since:** <t:{int(target.premium_since.timestamp())}:R>\n"
                    f"**Duration:** `{(datetime.utcnow() - target.premium_since.replace(tzinfo=None)).days} days`"
                ),
                inline=True
            )
        
        # Activity
        if target.activities:
            activity = target.activities[0]
            activity_text = f"**Type:** {activity.type.name.title()}\n"
            
            if isinstance(activity, discord.Game):
                activity_text += f"**Playing:** {activity.name}"
            elif isinstance(activity, discord.Streaming):
                activity_text += f"**Streaming:** [{activity.name}]({activity.url})"
            elif isinstance(activity, discord.Spotify):
                activity_text += f"**Listening to:** {activity.title} by {activity.artist}"
            elif isinstance(activity, discord.CustomActivity):
                activity_text += f"**Custom:** {activity.name or 'N/A'}"
            
            embed.add_field(
                name="🎮 Current Activity",
                value=activity_text,
                inline=False
            )
        
        # Voice state
        if ctx.guild and target.voice:
            voice_text = f"**Channel:** {target.voice.channel.mention}\n"
            voice_text += f"**Muted:** {'Yes' if target.voice.self_mute else 'No'}\n"
            voice_text += f"**Deafened:** {'Yes' if target.voice.self_deaf else 'No'}"
            
            embed.add_field(
                name="🎤 Voice Status",
                value=voice_text,
                inline=True
            )
        
        # AFK status
        if target.id in self.afk_users:
            afk_data = self.afk_users[target.id]
            embed.add_field(
                name="😴 AFK Status",
                value=f"**Reason:** {afk_data['reason']}\n**Since:** <t:{int(afk_data['time'].timestamp())}:R>",
                inline=True
            )
        
        # Acknowledgements
        acknowledgements = []
        if ctx.guild:
            if target.id == ctx.guild.owner_id:
                acknowledgements.append("👑 Server Owner")
            if perms.administrator:
                acknowledgements.append("🔧 Administrator")
            if perms.manage_guild:
                acknowledgements.append("⚙️ Server Manager")
            if target.premium_since:
                acknowledgements.append("💎 Server Booster")
        
        if acknowledgements:
            embed.add_field(
                name="🏅 Acknowledgements",
                value=" • ".join(acknowledgements),
                inline=False
            )
        
        # Banner preview (if exists)
        if hasattr(fetched_user, 'banner') and fetched_user.banner:
            embed.set_image(url=fetched_user.banner.url)
        
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        # Create button view
        view = UserInfoButtonView(target, fetched_user)
        
        await ctx.send(embed=embed, view=view)
    
    # Error handlers
    @avatar.error
    async def avatar_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("```\n❌ User not found!\n```")
    
    @user_banner.error
    async def banner_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("```\n❌ User not found!\n```")
    
    @user_info.error
    async def userinfo_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("```\n❌ User not found!\n```")


# ============================================================
#                    BUTTON VIEWS
# ============================================================

class AvatarButtonView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.user = user
        
        # Add download buttons
        self.add_item(discord.ui.Button(
            label="PNG",
            url=user.display_avatar.replace(format='png', size=4096).url,
            style=discord.ButtonStyle.link
        ))
        
        self.add_item(discord.ui.Button(
            label="JPG",
            url=user.display_avatar.replace(format='jpg', size=4096).url,
            style=discord.ButtonStyle.link
        ))
        
        self.add_item(discord.ui.Button(
            label="WEBP",
            url=user.display_avatar.replace(format='webp', size=4096).url,
            style=discord.ButtonStyle.link
        ))
        
        if user.display_avatar.is_animated():
            self.add_item(discord.ui.Button(
                label="GIF",
                url=user.display_avatar.replace(format='gif', size=4096).url,
                style=discord.ButtonStyle.link
            ))
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=1)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Avatar refreshed!", ephemeral=True)


class BannerButtonView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.user = user
        
        if user.banner:
            self.add_item(discord.ui.Button(
                label="PNG",
                url=user.banner.replace(format='png', size=4096).url,
                style=discord.ButtonStyle.link
            ))
            
            self.add_item(discord.ui.Button(
                label="JPG",
                url=user.banner.replace(format='jpg', size=4096).url,
                style=discord.ButtonStyle.link
            ))
            
            if user.banner.is_animated():
                self.add_item(discord.ui.Button(
                    label="GIF",
                    url=user.banner.replace(format='gif', size=4096).url,
                    style=discord.ButtonStyle.link
                ))


class UserInfoButtonView(discord.ui.View):
    def __init__(self, member, user):
        super().__init__(timeout=300)
        self.member = member
        self.user = user
    
    @discord.ui.button(label="📷 Avatar", style=discord.ButtonStyle.primary)
    async def view_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=f"{self.member.name}'s Avatar",
            color=self.member.color
        )
        embed.set_image(url=self.member.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🎨 Banner", style=discord.ButtonStyle.primary)
    async def view_banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        if hasattr(self.user, 'banner') and self.user.banner:
            embed = discord.Embed(
                title=f"{self.member.name}'s Banner",
                color=self.member.color
            )
            embed.set_image(url=self.user.banner.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ User has no banner!", ephemeral=True)
    
    @discord.ui.button(label="📊 JSON Data", style=discord.ButtonStyle.secondary)
    async def view_json(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data = {
            'id': str(self.member.id),
            'username': self.member.name,
            'discriminator': self.member.discriminator,
            'bot': self.member.bot,
            'created_at': self.member.created_at.isoformat(),
            'avatar_url': str(self.member.display_avatar.url)
        }
        
        json_text = json.dumps(user_data, indent=2)
        await interaction.response.send_message(
            f"```json\n{json_text}\n```",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(AdvancedCommands(bot))