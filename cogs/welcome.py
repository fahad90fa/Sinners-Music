import discord
from discord.ext import commands
import json
from datetime import datetime
import random
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
#                    BOT SETUP
# ============================================================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# ============================================================
#                    WELCOME SYSTEM COG
# ============================================================

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "config.json"

    # --------------------------------------------------------
    #                 HELPER FUNCTIONS
    # --------------------------------------------------------

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default = {"welcome_channel": None}
            with open(self.config_file, 'w') as f:
                json.dump(default, f, indent=4)
            return default

    def save_config(self, config):
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    # --------------------------------------------------------
    #                 COMMANDS
    # --------------------------------------------------------

    @commands.command(name='welcome')
    @commands.has_permissions(administrator=True)
    async def setup_welcome(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            msg = (
                "```\n"
                "╔═══════════════════════════════════════════════════════╗\n"
                "║                  ❌ ERROR                             ║\n"
                "╠═══════════════════════════════════════════════════════╣\n"
                "║                                                       ║\n"
                "║   No channel specified!                               ║\n"
                "║                                                       ║\n"
                "║   Usage   : !welcome #channel                         ║\n"
                "║   Example : !welcome #welcome                         ║\n"
                "║                                                       ║\n"
                "╚═══════════════════════════════════════════════════════╝\n"
                "```"
            )
            await ctx.send(msg)
            return

        config = self.load_config()
        config['welcome_channel'] = channel.id
        self.save_config(config)

        confirmation = (
            "```\n"
            "╔═══════════════════════════════════════════════════════╗\n"
            "║                                                       ║\n"
            "║       ✅  WELCOME SYSTEM ACTIVATED SUCCESSFULLY       ║\n"
            "║                                                       ║\n"
            "╠═══════════════════════════════════════════════════════╣\n"
            "║                                                       ║\n"
            f"║   📢  Welcome Channel : #{channel.name:<30} ║\n"
            f"║   🆔  Channel ID      : {str(channel.id):<30} ║\n"
            "║   ⚙️  Status          : ENABLED                       ║\n"
            "║                                                       ║\n"
            "╠═══════════════════════════════════════════════════════╣\n"
            "║                                                       ║\n"
            "║   COMMANDS:                                           ║\n"
            "║   • !welcome #channel   - Change welcome channel      ║\n"
            "║   • !testwelcome        - Test welcome message        ║\n"
            "║   • !disablewelcome     - Disable welcome system      ║\n"
            "║   • !welcomestats       - View system statistics      ║\n"
            "║   • !setwelcomestyle    - Change welcome style        ║\n"
            "║                                                       ║\n"
            "╚═══════════════════════════════════════════════════════╝\n"
            "```"
        )

        await ctx.send(confirmation)

        setup_notice = (
            "```\n"
            "╔═══════════════════════════════════════════════════════╗\n"
            "║       🎉  WELCOME SYSTEM CONFIGURED  🎉               ║\n"
            "╠═══════════════════════════════════════════════════════╣\n"
            "║                                                       ║\n"
            "║   This channel will now display welcome messages      ║\n"
            "║   for all new members joining ZeroDay Tool.           ║\n"
            "║                                                       ║\n"
            f"║   Setup by : {ctx.author.name:<40} ║\n"
            f"║   Time     : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC':<40} ║\n"
            "║                                                       ║\n"
            "╚═══════════════════════════════════════════════════════╝\n"
            "```"
        )

        await channel.send(setup_notice)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name='testwelcome')
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx):
        config = self.load_config()
        welcome_channel_id = config.get('welcome_channel')

        if not welcome_channel_id:
            await ctx.send(
                "```\n"
                "❌ Welcome channel not set!\n"
                "Use !welcome #channel first.\n"
                "```"
            )
            return

        channel = self.bot.get_channel(welcome_channel_id)

        if not channel:
            await ctx.send(
                "```\n"
                "❌ Welcome channel not found!\n"
                "Please re-run !welcome #channel\n"
                "```"
            )
            return

        await self.send_welcome_message(channel, ctx.author, is_test=True)

        await ctx.send(
            f"```\n"
            f"✅ Test welcome message sent to #{channel.name}\n"
            f"```",
            delete_after=5
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name='disablewelcome')
    @commands.has_permissions(administrator=True)
    async def disable_welcome(self, ctx):
        config = self.load_config()
        config['welcome_channel'] = None
        self.save_config(config)

        msg = (
            "```\n"
            "╔═══════════════════════════════════════════════════════╗\n"
            "║                                                       ║\n"
            "║         🔴  WELCOME SYSTEM DISABLED  🔴               ║\n"
            "║                                                       ║\n"
            "╠═══════════════════════════════════════════════════════╣\n"
            "║                                                       ║\n"
            "║   Welcome messages will no longer be sent.            ║\n"
            "║   Use !welcome #channel to re-enable anytime.         ║\n"
            "║                                                       ║\n"
            "╚═══════════════════════════════════════════════════════╝\n"
            "```"
        )

        await ctx.send(msg)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name='welcomestats')
    @commands.has_permissions(administrator=True)
    async def welcome_stats(self, ctx):
        config = self.load_config()
        welcome_channel_id = config.get('welcome_channel')

        if welcome_channel_id:
            channel = self.bot.get_channel(welcome_channel_id)
            status = "✅ ENABLED"
            channel_name = f"#{channel.name}" if channel else "Not found"
        else:
            status = "❌ DISABLED"
            channel_name = "Not configured"

        style = config.get('welcome_style', 'main')

        stats = (
            "```\n"
            "╔═══════════════════════════════════════════════════════╗\n"
            "║            📊 WELCOME SYSTEM STATISTICS 📊            ║\n"
            "╠═══════════════════════════════════════════════════════╣\n"
            "║                                                       ║\n"
            f"║   Status         : {status:<33} ║\n"
            f"║   Channel        : {channel_name:<33} ║\n"
            f"║   Server Members : {str(ctx.guild.member_count):<33} ║\n"
            f"║   Active Style   : {style:<33} ║\n"
            "║   Bot Uptime     : Active                             ║\n"
            "║                                                       ║\n"
            "╠═══════════════════════════════════════════════════════╣\n"
            "║                                                       ║\n"
            "║   AVAILABLE STYLES:                                   ║\n"
            "║   • main       - Full ZeroDay welcome message         ║\n"
            "║   • compact    - Short and clean welcome              ║\n"
            "║   • hacker     - Terminal/hacker themed               ║\n"
            "║   • matrix     - Matrix themed welcome                ║\n"
            "║   • minimal    - Simple one-box welcome               ║\n"
            "║   • cyberpunk  - Cyberpunk night city theme           ║\n"
            "║                                                       ║\n"
            "╚═══════════════════════════════════════════════════════╝\n"
            "```"
        )

        await ctx.send(stats)

    @commands.command(name='setwelcomestyle')
    @commands.has_permissions(administrator=True)
    async def set_welcome_style(self, ctx, style: str = None):
        valid_styles = ['main', 'compact', 'hacker', 'matrix', 'minimal', 'cyberpunk']

        if style is None or style.lower() not in valid_styles:
            await ctx.send(
                "```\n"
                "╔═══════════════════════════════════════════════════════╗\n"
                "║              ❌ INVALID STYLE                         ║\n"
                "╠═══════════════════════════════════════════════════════╣\n"
                "║                                                       ║\n"
                "║   Usage: !setwelcomestyle <style>                     ║\n"
                "║                                                       ║\n"
                "║   Available Styles:                                   ║\n"
                "║   • main       - Full ZeroDay welcome                 ║\n"
                "║   • compact    - Short and clean                      ║\n"
                "║   • hacker     - Terminal themed                      ║\n"
                "║   • matrix     - Matrix themed                        ║\n"
                "║   • minimal    - Simple one box                       ║\n"
                "║   • cyberpunk  - Cyberpunk themed                     ║\n"
                "║                                                       ║\n"
                "╚═══════════════════════════════════════════════════════╝\n"
                "```"
            )
            return

        config = self.load_config()
        config['welcome_style'] = style.lower()
        self.save_config(config)

        await ctx.send(
            f"```\n"
            f"✅ Welcome style changed to: {style.upper()}\n"
            f"Use !testwelcome to preview.\n"
            f"```"
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass

    # --------------------------------------------------------
    #                 EVENT LISTENER
    # --------------------------------------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        config = self.load_config()
        welcome_channel_id = config.get('welcome_channel')

        if not welcome_channel_id:
            return

        channel = self.bot.get_channel(welcome_channel_id)

        if not channel:
            return

        await self.send_welcome_message(channel, member)

    # --------------------------------------------------------
    #                 WELCOME MESSAGE ROUTER
    # --------------------------------------------------------

    async def send_welcome_message(self, channel, member, is_test=False):
        config = self.load_config()
        style = config.get('welcome_style', 'main')

        if style == 'compact':
            await self.send_compact_welcome(channel, member, is_test)
        elif style == 'hacker':
            await self.send_hacker_welcome(channel, member, is_test)
        elif style == 'matrix':
            await self.send_matrix_welcome(channel, member, is_test)
        elif style == 'minimal':
            await self.send_minimal_welcome(channel, member, is_test)
        elif style == 'cyberpunk':
            await self.send_cyberpunk_welcome(channel, member, is_test)
        else:
            await self.send_main_welcome(channel, member, is_test)

    # --------------------------------------------------------
    #                 STYLE 1 - MAIN WELCOME
    # --------------------------------------------------------

    async def send_main_welcome(self, channel, member, is_test=False):
        guild = member.guild
        member_count = guild.member_count
        account_age = (datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
        test_label = "[🧪 TEST MESSAGE]\n" if is_test else ""

        welcome_phrases = [
            "Welcome to the dark side!",
            "A new hacker has arrived!",
            "The system has a new user!",
            "Access granted!",
            "New agent detected!",
            "Initializing new operative...",
            "Connection established!",
            "New member synced!",
            "Welcome to the matrix!",
            "Neural link established!",
        ]

        random_phrase = random.choice(welcome_phrases)

        part1 = (
            f"{test_label}"
            "```\n"
            "╔═══════════════════════════════════════════════════════════════════════════╗\n"
            "║                                                                           ║\n"
            "║   ███████╗███████╗██████╗  ██████╗ ██████╗  █████╗ ██╗   ██╗             ║\n"
            "║   ╚══███╔╝██╔════╝██╔══██╗██╔═══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝             ║\n"
            "║     ███╔╝ █████╗  ██████╔╝██║   ██║██║  ██║███████║ ╚████╔╝              ║\n"
            "║    ███╔╝  ██╔══╝  ██╔══██╗██║   ██║██║  ██║██╔══██║  ╚██╔╝               ║\n"
            "║   ███████╗███████╗██║  ██║╚██████╔╝██████╔╝██║  ██║   ██║                ║\n"
            "║   ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝               ║\n"
            "║                                                                           ║\n"
            "║                          T O O L S                                       ║\n"
            "║                                                                           ║\n"
            "╠═══════════════════════════════════════════════════════════════════════════╣\n"
            f"║   🎉  {random_phrase.center(67)}  ║\n"
            "╚═══════════════════════════════════════════════════════════════════════════╝\n"
            "```"
        )

        part2 = (
            f"**👤 Welcome to ZeroDay Tool, {member.mention}!**\n"
            "```\n"
            "┌───────────────────────────────────────────────────────────────────────────┐\n"
            "│                          📋 MEMBER INFORMATION                            │\n"
            "├───────────────────────────────────────────────────────────────────────────┤\n"
            "│                                                                           │\n"
            f"│   👤  Username    :  {member.name:<51} │\n"
            f"│   🆔  User ID     :  {str(member.id):<51} │\n"
            f"│   📅  Account Age :  {str(account_age) + ' days old':<51} │\n"
            f"│   🏆  Member #    :  {str(member_count):<51} │\n"
            f"│   ⏰  Joined At   :  {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC':<51} │\n"
            "│                                                                           │\n"
            "└───────────────────────────────────────────────────────────────────────────┘\n"
            "```"
        )

        part3 = (
            "```\n"
            "┌───────────────────────────────────────────────────────────────────────────┐\n"
            "│                          🚀 GETTING STARTED                               │\n"
            "├───────────────────────────────────────────────────────────────────────────┤\n"
            "│                                                                           │\n"
            "│   1️⃣   Read the rules in #rules channel                                   │\n"
            "│   2️⃣   React with ✅ to accept and get verified                           │\n"
            "│   3️⃣   Browse our premium products in the sales channel                   │\n"
            "│   4️⃣   Use !ticket for purchases and support inquiries                    │\n"
            "│   5️⃣   Enjoy our community and connect with members!                      │\n"
            "│                                                                           │\n"
            "└───────────────────────────────────────────────────────────────────────────┘\n"
            "```"
        )

        part4 = (
            "```\n"
            "┌───────────────────────────────────────────────────────────────────────────┐\n"
            "│                          🛒 WHAT WE OFFER                                 │\n"
            "├───────────────────────────────────────────────────────────────────────────┤\n"
            "│                                                                           │\n"
            "│   🛡️   Cybersecurity Tools    →  95+  Premium Custom Tools                │\n"
            "│   📈   Trading Indicators     →  30+  High Win-Rate Signals               │\n"
            "│   🤖   MT5 Algo Bots          →  30+  Automated Trading EAs               │\n"
            "│                                                                           │\n"
            "│   💎   Total Products  : 180+                                             │\n"
            "│   ⚡   Delivery        : Instant                                          │\n"
            "│   🎫   Support         : 24/7 via Tickets                                 │\n"
            "│   💰   Payment         : Flexible Options Available                       │\n"
            "│                                                                           │\n"
            "└───────────────────────────────────────────────────────────────────────────┘\n"
            "```"
        )

        part5 = (
            "```\n"
            "┌───────────────────────────────────────────────────────────────────────────┐\n"
            "│                          📌 QUICK COMMANDS                                │\n"
            "├───────────────────────────────────────────────────────────────────────────┤\n"
            "│                                                                           │\n"
            "│   !help        →  View all available bot commands                        │\n"
            "│   !products    →  Browse our complete product catalog                    │\n"
            "│   !ticket      →  Create a support or purchase ticket                    │\n"
            "│   !rules       →  View the full server rules                             │\n"
            "│                                                                           │\n"
            "└───────────────────────────────────────────────────────────────────────────┘\n"
            "```"
        )

        part6 = (
            "```\n"
            "┌───────────────────────────────────────────────────────────────────────────┐\n"
            "│                       ⚠️  IMPORTANT REMINDERS                             │\n"
            "├───────────────────────────────────────────────────────────────────────────┤\n"
            "│                                                                           │\n"
            "│   •  All cybersecurity tools require proper legal authorization           │\n"
            "│   •  Trading results are not guaranteed - invest responsibly              │\n"
            "│   •  Respect all members and follow the community guidelines              │\n"
            "│   •  Use tickets for all purchase and support inquiries only              │\n"
            "│   •  No sharing or reselling of any purchased products allowed            │\n"
            "│                                                                           │\n"
            "└───────────────────────────────────────────────────────────────────────────┘\n"
            "```"
        )

        part7 = (
            "```\n"
            "═══════════════════════════════════════════════════════════════════════════\n"
            "        🔥  Welcome to the elite! We are glad to have you here!  🔥\n"
            "═══════════════════════════════════════════════════════════════════════════\n"
            "```"
        )

        await channel.send(part1)
        await channel.send(part2)
        await channel.send(part3)
        await channel.send(part4)
        await channel.send(part5)
        await channel.send(part6)
        await channel.send(part7)

    # --------------------------------------------------------
    #                 STYLE 2 - COMPACT WELCOME
    # --------------------------------------------------------

    async def send_compact_welcome(self, channel, member, is_test=False):
        test_label = "[🧪 TEST]\n" if is_test else ""

        msg = (
            f"{test_label}"
            "```\n"
            "╔══════════════════════════════════════════════════════════╗\n"
            "║            🎉  NEW MEMBER ALERT  🎉                      ║\n"
            "╠══════════════════════════════════════════════════════════╣\n"
            "║                                                          ║\n"
            "║   ██╗    ██╗███████╗██╗      ██████╗ ██████╗ ███╗   ███╗║\n"
            "║   ██║    ██║██╔════╝██║     ██╔════╝██╔═══██╗████╗ ████║║\n"
            "║   ██║ █╗ ██║█████╗  ██║     ██║     ██║   ██║██╔████╔██║║\n"
            "║   ██║███╗██║██╔══╝  ██║     ██║     ██║   ██║██║╚██╔╝██║║\n"
            "║   ╚███╔███╔╝███████╗███████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║║\n"
            "║    ╚══╝╚══╝ ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝║\n"
            "║                                                          ║\n"
            "╠══════════════════════════════════════════════════════════╣\n"
            f"║   👤  {member.name:<50} ║\n"
            f"║   🏆  Member #{str(member.guild.member_count):<47} ║\n"
            "╠══════════════════════════════════════════════════════════╣\n"
            "║   📜 Read #rules  │  🛒 Browse #sales  │  🎫 !ticket     ║\n"
            "╚══════════════════════════════════════════════════════════╝\n"
            "```\n"
            f"Welcome {member.mention} to **ZeroDay Tool**! 🔥\n"
            "Get started by reading the rules and exploring our products!"
        )

        await channel.send(msg)

    # --------------------------------------------------------
    #                 STYLE 3 - HACKER WELCOME
    # --------------------------------------------------------

    async def send_hacker_welcome(self, channel, member, is_test=False):
        test_label = "[🧪 TEST]\n" if is_test else ""
        account_age = (datetime.utcnow() - member.created_at.replace(tzinfo=None)).days

        msg = (
            f"{test_label}"
            "```\n"
            " ____________________________________________________\n"
            "|                                                    |\n"
            "|  [SYSTEM] NEW CONNECTION DETECTED                  |\n"
            "|____________________________________________________|\n"
            "|                                                    |\n"
            "|  > Initializing user profile................. DONE  |\n"
            "|  > Scanning credentials...................... DONE  |\n"
            "|  > Checking authorization................... DONE  |\n"
            "|  > Access level: PENDING                           |\n"
            "|  > Status: CONNECTED                               |\n"
            "|                                                    |\n"
            "|  ┌──────────────────────────────────────────────┐  |\n"
            "|  │  USER DATA DUMP:                             │  |\n"
            "|  │  ─────────────────────────────────────────── │  |\n"
            f"|  │  HANDLE   : {member.name:<32} │  |\n"
            f"|  │  ID       : {str(member.id):<32} │  |\n"
            f"|  │  AGE      : {str(account_age) + ' days':<32} │  |\n"
            f"|  │  POSITION : #{str(member.guild.member_count):<31} │  |\n"
            "|  │  STATUS   : ONLINE                           │  |\n"
            "|  └──────────────────────────────────────────────┘  |\n"
            "|                                                    |\n"
            "|  [!] READ #rules TO GAIN FULL ACCESS               |\n"
            "|  [!] USE !ticket FOR SECURE COMMUNICATION          |\n"
            "|  [!] BROWSE #sales FOR AVAILABLE TOOLS             |\n"
            "|                                                    |\n"
            "|  > Connection established to ZeroDay Tool.         |\n"
            "|  > Welcome to the network.                         |\n"
            "|                                                    |\n"
            "|____________________________________________________|\n"
            "```\n"
            f"🔓 Access granted, {member.mention}. Welcome to the network."
        )

        await channel.send(msg)

    # --------------------------------------------------------
    #                 STYLE 4 - MATRIX WELCOME
    # --------------------------------------------------------

    async def send_matrix_welcome(self, channel, member, is_test=False):
        test_label = "[🧪 TEST]\n" if is_test else ""

        msg = (
            f"{test_label}"
            "```\n"
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃                                                               ┃\n"
            "┃  01011010 01100101 01110010 01101111 01000100 01100001 01111001┃\n"
            "┃                                                               ┃\n"
            "┃  ╔═══════════════════════════════════════════════════════╗    ┃\n"
            "┃  ║                                                       ║    ┃\n"
            "┃  ║            Z E R O D A Y   T O O L                   ║    ┃\n"
            "┃  ║                                                       ║    ┃\n"
            "┃  ║     Free your mind. Enter the Matrix.                 ║    ┃\n"
            "┃  ║                                                       ║    ┃\n"
            "┃  ╚═══════════════════════════════════════════════════════╝    ┃\n"
            "┃                                                               ┃\n"
            "┃  ┌─────────────────────────────────────────────────────────┐  ┃\n"
            "┃  │  NEURAL LINK ESTABLISHED                                │  ┃\n"
            "┃  │                                                         │  ┃\n"
            f"┃  │  Operative    : {member.name:<40} │  ┃\n"
            f"┃  │  Designation  : #{str(member.guild.member_count):<39} │  ┃\n"
            "┃  │  Clearance    : PENDING - Accept rules for access      │  ┃\n"
            "┃  │  Status       : CONNECTED                              │  ┃\n"
            "┃  │                                                         │  ┃\n"
            "┃  └─────────────────────────────────────────────────────────┘  ┃\n"
            "┃                                                               ┃\n"
            "┃  > Follow the white rabbit...                                 ┃\n"
            "┃  > Read #rules  →  Accept  →  Unlock full access             ┃\n"
            "┃  > Visit #sales for premium tools                            ┃\n"
            "┃  > Use !ticket for all support inquiries                     ┃\n"
            "┃                                                               ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n"
            "```\n"
            f"Wake up, {member.mention}... Welcome to the real world. 💊"
        )

        await channel.send(msg)

    # --------------------------------------------------------
    #                 STYLE 5 - MINIMAL WELCOME
    # --------------------------------------------------------

    async def send_minimal_welcome(self, channel, member, is_test=False):
        test_label = "[🧪 TEST]\n" if is_test else ""

        msg = (
            f"{test_label}"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "                  🎉 NEW MEMBER JOINED\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "\n"
            f"    👤  Username : {member.name}\n"
            f"    🆔  User ID  : {member.id}\n"
            f"    🏆  Member # : {member.guild.member_count}\n"
            "\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "    📜 #rules  •  🛒 #sales  •  🎫 !ticket  •  ❓ !help\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "```\n"
            f"Welcome to **ZeroDay Tool**, {member.mention}! 👋"
        )

        await channel.send(msg)

    # --------------------------------------------------------
    #                 STYLE 6 - CYBERPUNK WELCOME
    # --------------------------------------------------------

    async def send_cyberpunk_welcome(self, channel, member, is_test=False):
        test_label = "[🧪 TEST]\n" if is_test else ""

        msg = (
            f"{test_label}"
            "```\n"
            "▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄\n"
            "█                                                           █\n"
            "█    ░▒▓█  ZERODAY TOOL - NIGHT CITY NETWORK  █▓▒░          █\n"
            "█                                                           █\n"
            "█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█\n"
            "█                                                           █\n"
            "█   ╭───────────────────────────────────────────────────╮   █\n"
            "█   │  ◢◤  NEW NETRUNNER DETECTED  ◢◤                   │   █\n"
            "█   │                                                   │   █\n"
            f"█   │  ALIAS    ▸ {member.name:<41}│   █\n"
            f"█   │  NODE ID  ▸ {str(member.id):<41}│   █\n"
            f"█   │  RANK     ▸ Netrunner #{str(member.guild.member_count):<32}│   █\n"
            "█   │  STATUS   ▸ ● ONLINE                             │   █\n"
            "█   │                                                   │   █\n"
            "█   ╰───────────────────────────────────────────────────╯   █\n"
            "█                                                           █\n"
            "█   ◆ ENTRY PROTOCOLS ◆                                     █\n"
            "█   ├─► Read #rules to bypass the firewall                  █\n"
            "█   ├─► Visit #sales for black market tech                  █\n"
            "█   └─► Use !ticket for encrypted communications            █\n"
            "█                                                           █\n"
            "█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█\n"
            "█   ░▒▓  In the dark future, there is only ZeroDay  ▓▒░    █\n"
            "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀\n"
            "```\n"
            f"Jack in, {member.mention}. The network awaits. ⚡"
        )

        await channel.send(msg)

    # --------------------------------------------------------
    #                 ERROR HANDLERS
    # --------------------------------------------------------

    @setup_welcome.error
    async def welcome_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("```\n❌ You need Administrator permission to use this command.\n```")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("```\n❌ Invalid channel! Please mention a valid text channel.\n```")

    @test_welcome.error
    async def test_welcome_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("```\n❌ You need Administrator permission to use this command.\n```")

    @disable_welcome.error
    async def disable_welcome_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("```\n❌ You need Administrator permission to use this command.\n```")

    @welcome_stats.error
    async def welcome_stats_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("```\n❌ You need Administrator permission to use this command.\n```")

    @set_welcome_style.error
    async def set_style_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("```\n❌ You need Administrator permission to use this command.\n```")


# ============================================================
#                    BOT EVENTS
# ============================================================

@bot.event
async def on_ready():
    print(
        f"\n"
        f"╔═══════════════════════════════════════════════╗\n"
        f"║                                               ║\n"
        f"║        🤖  ZERODAY TOOL BOT  ONLINE  🤖       ║\n"
        f"║                                               ║\n"
        f"╠═══════════════════════════════════════════════╣\n"
        f"║                                               ║\n"
        f"║  Bot Name  : {bot.user.name:<31} ║\n"
        f"║  Bot ID    : {str(bot.user.id):<31} ║\n"
        f"║  Servers   : {str(len(bot.guilds)):<31} ║\n"
        f"║                                               ║\n"
        f"╚═══════════════════════════════════════════════╝\n"
    )

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="ZeroDay Tool | !help"
        ),
        status=discord.Status.online
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("```\n❌ You do not have permission to use this command.\n```")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"```\n❌ Missing required argument: {error.param.name}\n```")


# ============================================================
#                    LOAD COGS & RUN
# ============================================================

async def main():
    async with bot:
        await bot.add_cog(WelcomeSystem(bot))
        await bot.start(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())