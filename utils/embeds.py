import discord
from datetime import datetime
from typing import Dict, List


class EmbedBuilder:
    STORE_ICON = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80"

    @staticmethod
    def create_base_embed(title: str, description: str = "", color: int = 0x00FF9D) -> discord.Embed:
        """Create base embed with branding."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text="ZeroDay Tools", icon_url=EmbedBuilder.STORE_ICON)
        return embed

    @staticmethod
    def product_embed(product: Dict) -> discord.Embed:
        """Create product display embed."""
        embed = discord.Embed(
            title=f"🛡️ {product['name']}",
            description=product['description'],
            color=0x00FF9D,
            timestamp=datetime.now()
        )

        embed.add_field(name="💰 Price", value=f"`${product['price']}`", inline=True)
        embed.add_field(name="📦 Category", value=f"`{product['category']}`", inline=True)
        embed.add_field(name="📊 Stock", value=f"`{product.get('stock', 'Unlimited')}`", inline=True)

        if product.get('features'):
            features_text = "\n".join([f"✅ {feature}" for feature in product['features']])
            embed.add_field(name="✨ Features", value=features_text, inline=False)

        if product.get('image_url'):
            embed.set_thumbnail(url=product['image_url'])

        embed.set_footer(text=f"Product ID: {product['id']} | React to purchase")
        return embed

    @staticmethod
    def products_list_embed(products: List[Dict], category: str = "All") -> discord.Embed:
        """Create products list embed."""
        embed = discord.Embed(
            title=f"🛒 Available Products - {category}",
            description="Browse our premium tools and indicators",
            color=0x00FF9D,
            timestamp=datetime.now()
        )

        if not products:
            embed.add_field(name="📭 No Products", value="No products available in this category")
            return embed

        for product in products[:10]:
            value = (
                f"💰 **${product['price']}**\n"
                f"📝 {product['description'][:100]}...\n"
                f"🆔 Product ID: `{product['id']}`"
            )
            embed.add_field(name=product['name'], value=value, inline=False)

        if len(products) > 10:
            embed.set_footer(text=f"Showing 10 of {len(products)} products | Use !product <id> for details")

        return embed

    @staticmethod
    def order_embed(order: Dict, product: Dict) -> discord.Embed:
        """Create order confirmation embed."""
        embed = discord.Embed(
            title="🎉 Order Confirmation",
            description="Thank you for your purchase!",
            color=0x00FF00,
            timestamp=datetime.now()
        )

        embed.add_field(name="📦 Product", value=product['name'], inline=False)
        embed.add_field(name="🆔 Order ID", value=f"`{order['order_id']}`", inline=True)
        embed.add_field(name="💰 Total", value=f"`${product['price']}`", inline=True)
        embed.add_field(name="📊 Status", value=f"`{order['status'].upper()}`", inline=True)
        embed.add_field(
            name="📝 Next Steps",
            value="1️⃣ Complete payment using provided details\n2️⃣ Submit payment proof\n3️⃣ Receive your product within 24hrs",
            inline=False
        )

        embed.set_thumbnail(url=product.get('image_url', ''))
        embed.set_footer(text=f"Order Date: {order['created_at']}")
        return embed

    @staticmethod
    def ticket_embed(ticket: Dict, ticket_type: str = "Support") -> discord.Embed:
        """Create ticket embed."""
        status_colors = {
            'open': 0x00FF00,
            'pending': 0xFFA500,
            'closed': 0xFF0000
        }

        embed = discord.Embed(
            title=f"🎫 Ticket #{ticket['ticket_id']}",
            description=ticket.get('description', 'No description provided'),
            color=status_colors.get(ticket['status'], 0x00FF9D),
            timestamp=datetime.now()
        )

        embed.add_field(name="📋 Type", value=ticket_type, inline=True)
        embed.add_field(name="📊 Status", value=ticket['status'].upper(), inline=True)
        embed.add_field(name="👤 User", value=f"<@{ticket['user_id']}>", inline=True)

        if ticket.get('assigned_to'):
            embed.add_field(name="👨‍💼 Assigned To", value=f"<@{ticket['assigned_to']}>", inline=True)

        embed.set_footer(text=f"Created: {ticket['created_at']}")
        return embed

    @staticmethod
    def help_embed() -> discord.Embed:
        """Create main help embed - landing page."""
        embed = discord.Embed(
            title="",
            description="",
            color=0x00FF9D,
            timestamp=datetime.utcnow()
        )

        embed.set_author(
            name="📚 ZERODAY TOOLS - COMMAND CENTER",
            icon_url=EmbedBuilder.STORE_ICON
        )

        embed.description = (
            "```ansi\n"
            "\u001b[1;36m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;36m║                                                   ║\n"
            "\u001b[1;36m║        🤖  ADVANCED BOT COMMAND GUIDE  🤖        ║\n"
            "\u001b[1;36m║                                                   ║\n"
            "\u001b[1;36m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "**Welcome to ZeroDay Tools Bot!**\n"
            "Use the buttons below to browse command categories.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        embed.add_field(
            name="📋 **COMMAND CATEGORIES**",
            value=(
                "> 🛒 **Shopping** - Products, orders, purchases\n"
                "> 🎫 **Tickets** - Support & purchase tickets\n"
                "> 🔨 **Moderation** - Server management tools\n"
                "> 💰 **Economy** - Currency, shop, gambling\n"
                "> 🎮 **Fun** - Games, memes, interactions\n"
                "> 🖼️ **Image** - Avatar manipulation tools\n"
                "> 🛠️ **Utility** - Helpful utility commands\n"
                "> 📊 **Info** - User, server, bot information\n"
                "> ⚙️ **Admin** - Administrator commands"
            ),
            inline=False
        )

        embed.add_field(
            name="",
            value=(
                "```yaml\n"
                "📊 BOT STATISTICS\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Total Commands  : 120+\n"
                "Categories      : 9\n"
                "Prefix          : !\n"
                "Help Version    : 2.0\n"
                "```"
            ),
            inline=True
        )

        embed.add_field(
            name="",
            value=(
                "```fix\n"
                "💡 QUICK TIPS\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "• Use buttons to navigate\n"
                "• <required> [optional]\n"
                "• Don't type < > or [ ]\n"
                "• Some cmds need permissions\n"
                "```"
            ),
            inline=True
        )

        embed.set_footer(
            text="ZeroDay Tools • Use buttons below to navigate • Page 1/10",
            icon_url=EmbedBuilder.STORE_ICON
        )
        embed.set_thumbnail(url=EmbedBuilder.STORE_ICON)
        return embed

    @staticmethod
    def help_shopping() -> discord.Embed:
        embed = discord.Embed(title="", description="", color=0x00D9FF, timestamp=datetime.utcnow())
        embed.set_author(name="🛒 SHOPPING COMMANDS", icon_url=EmbedBuilder.STORE_ICON)
        embed.description = (
            "```ansi\n"
            "\u001b[1;36m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;36m║           STOREFRONT & PRODUCT COMMANDS           ║\n"
            "\u001b[1;36m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(
            name="🛍️ **Browsing**",
            value=(
                "> `!products` - View all available products\n"
                "> `!product <id>` - View specific product details\n"
                "> `!cybersecurity` - Browse cybersecurity tools\n"
                "> `!setup #channel` - Deploy storefront menu"
            ),
            inline=False
        )
        embed.add_field(
            name="🛒 **Purchasing**",
            value=(
                "> `!buy <id>` - Purchase a product\n"
                "> `!orders` - View your order history\n"
                "> `!order <id>` - Check specific order status"
            ),
            inline=False
        )
        embed.add_field(
            name="📦 **Management** (Admin)",
            value=(
                "> `!addproduct` - Add new product interactively\n"
                "> `!removeproduct <id>` - Remove a product\n"
                "> `!setstatus <order_id> <status>` - Update order\n"
                "> `!stats` - View sales statistics"
            ),
            inline=False
        )
        embed.set_footer(text="ZeroDay Tools • Shopping Commands • Page 2/10")
        return embed

    @staticmethod
    def help_tickets() -> discord.Embed:
        embed = discord.Embed(title="", description="", color=0x5865F2, timestamp=datetime.utcnow())
        embed.set_author(name="🎫 TICKET COMMANDS", icon_url=EmbedBuilder.STORE_ICON)
        embed.description = (
            "```ansi\n"
            "\u001b[1;35m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;35m║             SUPPORT & TICKET SYSTEM               ║\n"
            "\u001b[1;35m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(
            name="🎟️ **User Commands**",
            value=(
                "> `!ticket <reason>` - Create support ticket\n"
                "> `!closeticket` - Close your current ticket\n"
                "> `!mytickets` - View all your tickets"
            ),
            inline=False
        )
        embed.add_field(
            name="🔧 **Staff Commands**",
            value=(
                "> `!add @user` - Add user to ticket\n"
                "> `!remove @user` - Remove user from ticket\n"
                "> `!rename <name>` - Rename ticket channel\n"
                "> `!transcript` - Generate ticket transcript"
            ),
            inline=False
        )
        embed.set_footer(text="ZeroDay Tools • Ticket Commands • Page 3/10")
        return embed

    @staticmethod
    def help_moderation() -> discord.Embed:
        embed = discord.Embed(title="", description="", color=0xFF0000, timestamp=datetime.utcnow())
        embed.set_author(name="🔨 MODERATION COMMANDS", icon_url=EmbedBuilder.STORE_ICON)
        embed.description = (
            "```ansi\n"
            "\u001b[1;31m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;31m║           SERVER MODERATION TOOLKIT               ║\n"
            "\u001b[1;31m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(
            name="👢 **Member Actions**",
            value=(
                "> `!kick @user [reason]` - Kick member with DM notification\n"
                "> `!ban @user [reason]` - Ban member with case logging\n"
                "> `!unban <user_id>` - Unban user by ID\n"
                "> `!softban @user` - Ban & unban to clear messages\n"
                "> `!tempban @user <time>` - Temporary ban\n"
                "> `!mute @user <time> [reason]` - Timeout user\n"
                "> `!unmute @user` - Remove timeout"
            ),
            inline=False
        )
        embed.add_field(
            name="⚠️ **Warning System**",
            value=(
                "> `!warn @user [reason]` - Issue warning\n"
                "> `!warnings @user` - View user warnings\n"
                "> `!clearwarns @user` - Clear all warnings\n"
                "> `!modlogs @user` - View mod history\n"
                "> `!case <id>` - View specific case\n"
                "> `!editcase <id> <reason>` - Edit case reason"
            ),
            inline=False
        )
        embed.add_field(
            name="🧹 **Message Management**",
            value=(
                "> `!purge <amount>` - Delete messages (1-100)\n"
                "> `!purgeuser @user <amount>` - Purge from user\n"
                "> `!purgebots <amount>` - Purge bot messages\n"
                "> `!purgelinks <amount>` - Purge links\n"
                "> `!purgeimages <amount>` - Purge images"
            ),
            inline=False
        )
        embed.add_field(
            name="🔒 **Channel Management**",
            value=(
                "> `!slowmode <seconds>` - Set channel slowmode\n"
                "> `!lock` - Lock current channel\n"
                "> `!unlock` - Unlock current channel\n"
                "> `!lockdown` - Lock all channels (emergency)\n"
                "> `!nuke` - Clone & delete channel (reset)"
            ),
            inline=False
        )
        embed.set_footer(text="ZeroDay Tools • Moderation Commands • Page 4/10")
        return embed

    @staticmethod
    def help_economy() -> discord.Embed:
        embed = discord.Embed(title="", description="", color=0xFFD700, timestamp=datetime.utcnow())
        embed.set_author(name="💰 ECONOMY COMMANDS", icon_url=EmbedBuilder.STORE_ICON)
        embed.description = (
            "```ansi\n"
            "\u001b[1;33m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;33m║              ECONOMY & CURRENCY SYSTEM            ║\n"
            "\u001b[1;33m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(
            name="💵 **Balance & Earning**",
            value=(
                "> `!balance [@user]` - Check balance\n"
                "> `!daily` - Claim daily reward\n"
                "> `!weekly` - Claim weekly reward\n"
                "> `!work` - Work for coins\n"
                "> `!crime` - Risky crime for coins\n"
                "> `!rob @user` - Rob another user"
            ),
            inline=False
        )
        embed.add_field(
            name="🏦 **Banking**",
            value=(
                "> `!deposit <amount|all>` - Deposit to bank\n"
                "> `!withdraw <amount|all>` - Withdraw from bank\n"
                "> `!pay @user <amount>` - Pay another user\n"
                "> `!networth [@user]` - View total net worth"
            ),
            inline=False
        )
        embed.add_field(
            name="🛍️ **Shopping**",
            value=(
                "> `!shop` - View available shop items\n"
                "> `!buyitem <item_id>` - Purchase shop item\n"
                "> `!sell <item_id>` - Sell item (50% value)\n"
                "> `!inventory [@user]` - View inventory\n"
                "> `!use <item_id>` - Use an item"
            ),
            inline=False
        )
        embed.add_field(
            name="🎰 **Gambling**",
            value=(
                "> `!gamble <amount>` - Gamble coins (45% win)\n"
                "> `!slots <amount>` - Play slot machine\n"
                "> `!blackjack <amount>` - Play blackjack\n"
                "> `!roulette <bet> <choice>` - Play roulette\n"
                "> `!coinflipbet @user <amount>` - Coinflip bet"
            ),
            inline=False
        )
        embed.add_field(
            name="📊 **Leaderboards**",
            value=(
                "> `!leaderboard` - View richest users\n"
                "> `!givecoins @user <amount>` - Give coins (Admin)\n"
                "> `!removecoins @user <amount>` - Take coins (Admin)\n"
                "> `!reseteconomy @user` - Reset economy (Admin)"
            ),
            inline=False
        )
        embed.set_footer(text="ZeroDay Tools • Economy Commands • Page 5/10")
        return embed

    @staticmethod
    def help_fun() -> discord.Embed:
        embed = discord.Embed(title="", description="", color=0xFF69B4, timestamp=datetime.utcnow())
        embed.set_author(name="🎮 FUN COMMANDS", icon_url=EmbedBuilder.STORE_ICON)
        embed.description = (
            "```ansi\n"
            "\u001b[1;35m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;35m║              FUN & ENTERTAINMENT                  ║\n"
            "\u001b[1;35m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(
            name="🎲 **Games**",
            value=(
                "> `!8ball <question>` - Ask the magic 8-ball\n"
                "> `!coinflip` - Flip a coin\n"
                "> `!roll <dice>` - Roll dice (2d6, 1d20)\n"
                "> `!rps <choice>` - Rock Paper Scissors\n"
                "> `!fight @user` - Fight simulator\n"
                "> `!trivia` - Trivia question\n"
                "> `!riddle` - Random riddle"
            ),
            inline=False
        )
        embed.add_field(
            name="😂 **Social**",
            value=(
                "> `!roast @user` - Roast someone\n"
                "> `!compliment @user` - Compliment someone\n"
                "> `!hug @user` - Hug someone\n"
                "> `!slap @user` - Slap someone\n"
                "> `!kiss @user` - Kiss someone\n"
                "> `!kill @user` - Funny kill message"
            ),
            inline=False
        )
        embed.add_field(
            name="📊 **Ratings & Generators**",
            value=(
                "> `!rate <thing>` - Rate anything 0-10\n"
                "> `!ship @user1 @user2` - Ship compatibility\n"
                "> `!iq [@user]` - Fake IQ test\n"
                "> `!pp [@user]` - Funny size generator\n"
                "> `!gayrate [@user]` - Gay percentage\n"
                "> `!simprate [@user]` - Simp percentage\n"
                "> `!hack @user` - Fake hack simulation"
            ),
            inline=False
        )
        embed.add_field(
            name="🎭 **Party Games**",
            value=(
                "> `!wouldyourather` - Would you rather\n"
                "> `!truth` - Truth question\n"
                "> `!dare` - Dare challenge\n"
                "> `!neverhaveiever` - Never have I ever\n"
                "> `!thisorthat` - This or that"
            ),
            inline=False
        )
        embed.add_field(
            name="📰 **Content**",
            value=(
                "> `!meme` - Random meme from Reddit\n"
                "> `!joke` - Random joke\n"
                "> `!fact` - Random fact\n"
                "> `!quote` - Inspirational quote"
            ),
            inline=False
        )
        embed.set_footer(text="ZeroDay Tools • Fun Commands • Page 6/10")
        return embed

    @staticmethod
    def help_image() -> discord.Embed:
        embed = discord.Embed(title="", description="", color=0x9B59B6, timestamp=datetime.utcnow())
        embed.set_author(name="🖼️ IMAGE COMMANDS", icon_url=EmbedBuilder.STORE_ICON)
        embed.description = (
            "```ansi\n"
            "\u001b[1;35m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;35m║            IMAGE MANIPULATION SUITE               ║\n"
            "\u001b[1;35m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(
            name="🎨 **Filters & Effects**",
            value=(
                "> `!blur [@user]` - Blur avatar\n"
                "> `!pixelate [@user]` - Pixelate avatar\n"
                "> `!deepfry [@user]` - Deep fry image\n"
                "> `!invert [@user]` - Invert colors\n"
                "> `!grayscale [@user]` - Grayscale filter\n"
                "> `!sepia [@user]` - Sepia filter\n"
                "> `!triggered [@user]` - Triggered effect"
            ),
            inline=False
        )
        embed.add_field(
            name="📐 **Adjustments**",
            value=(
                "> `!brightness [@user] <value>` - Adjust brightness (0.1-3.0)\n"
                "> `!contrast [@user] <value>` - Adjust contrast (0.1-3.0)\n"
                "> `!rotate [@user] <degrees>` - Rotate image\n"
                "> `!flip [@user]` - Flip vertically\n"
                "> `!mirror [@user]` - Mirror horizontally\n"
                "> `!resize [@user] <w> <h>` - Resize image"
            ),
            inline=False
        )
        embed.add_field(
            name="🎭 **Meme & Fun Images**",
            value=(
                "> `!wanted [@user]` - Generate wanted poster\n"
                "> `!jail [@user]` - Put someone in jail\n"
                "> `!rip [@user]` - RIP tombstone image\n"
                "> `!trash [@user]` - Put someone in trash"
            ),
            inline=False
        )
        embed.set_footer(text="ZeroDay Tools • Image Commands • Page 7/10")
        return embed

    @staticmethod
    def help_utility() -> discord.Embed:
        embed = discord.Embed(title="", description="", color=0x3498DB, timestamp=datetime.utcnow())
        embed.set_author(name="🛠️ UTILITY COMMANDS", icon_url=EmbedBuilder.STORE_ICON)
        embed.description = (
            "```ansi\n"
            "\u001b[1;34m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;34m║                UTILITY TOOLKIT                    ║\n"
            "\u001b[1;34m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(
            name="⏰ **Reminders & Todo**",
            value=(
                "> `!remind <time> <message>` - Set reminder (1d, 2h, 30m)\n"
                "> `!reminders` - View active reminders\n"
                "> `!todo add <task>` - Add todo task\n"
                "> `!todo list` - View your todo list\n"
                "> `!todo remove <id>` - Remove task"
            ),
            inline=False
        )
        embed.add_field(
            name="🔧 **Tools**",
            value=(
                "> `!calculate <expression>` - Math calculator\n"
                "> `!qrcode <text/url>` - Generate QR code\n"
                "> `!password [length]` - Generate password (DM)\n"
                "> `!encode <type> <text>` - Encode (base64/hex)\n"
                "> `!decode <type> <text>` - Decode text\n"
                "> `!hash <type> <text>` - Generate hash"
            ),
            inline=False
        )
        embed.add_field(
            name="📝 **Message Tools**",
            value=(
                "> `!snipe` - Recover deleted message\n"
                "> `!editsnipe` - Recover edited message\n"
                "> `!say <message>` - Bot says your message\n"
                "> `!embed` - Interactive embed builder"
            ),
            inline=False
        )
        embed.add_field(
            name="😴 **Status**",
            value=(
                "> `!afk [reason]` - Set AFK status\n"
                "> Auto-removes when you send a message\n"
                "> Notifies others when they mention you"
            ),
            inline=False
        )
        embed.set_footer(text="ZeroDay Tools • Utility Commands • Page 8/10")
        return embed

    @staticmethod
    def help_info() -> discord.Embed:
        embed = discord.Embed(title="", description="", color=0x2ECC71, timestamp=datetime.utcnow())
        embed.set_author(name="📊 INFORMATION COMMANDS", icon_url=EmbedBuilder.STORE_ICON)
        embed.description = (
            "```ansi\n"
            "\u001b[1;32m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;32m║              INFORMATION & LOOKUP                 ║\n"
            "\u001b[1;32m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(
            name="👤 **User Information**",
            value=(
                "> `!userinfo [@user]` - Full user information\n"
                "> `!av [@user]` - View avatar in HD\n"
                "> `!banner [@user]` - View profile banner\n"
                "> `!permissions [@user]` - View permissions"
            ),
            inline=False
        )
        embed.add_field(
            name="🏰 **Server Information**",
            value=(
                "> `!serverinfo` - Detailed server info\n"
                "> `!channelinfo [#channel]` - Channel info\n"
                "> `!roleinfo @role` - Role information\n"
                "> `!emojiinfo <emoji>` - Emoji details\n"
                "> `!membercount` - Member breakdown\n"
                "> `!boosters` - List server boosters"
            ),
            inline=False
        )
        embed.add_field(
            name="🤖 **Bot Information**",
            value=(
                "> `!botinfo` - Bot statistics\n"
                "> `!ping` - Bot latency\n"
                "> `!uptime` - Bot uptime\n"
                "> `!stats` - Server statistics"
            ),
            inline=False
        )
        embed.add_field(
            name="🔍 **Lookup**",
            value=(
                "> `!cnic` - CNIC/SIM database lookup\n"
                "> `!cnicinfo <cnic>` - CNIC province/gender info\n"
                "> `!inviteinfo <invite>` - Invite link info\n"
                "> `!invites [@user]` - Count user invites"
            ),
            inline=False
        )
        embed.set_footer(text="ZeroDay Tools • Info Commands • Page 9/10")
        return embed

    @staticmethod
    def help_admin() -> discord.Embed:
        embed = discord.Embed(title="", description="", color=0xE74C3C, timestamp=datetime.utcnow())
        embed.set_author(name="⚙️ ADMIN COMMANDS", icon_url=EmbedBuilder.STORE_ICON)
        embed.description = (
            "```ansi\n"
            "\u001b[1;31m╔═══════════════════════════════════════════════════╗\n"
            "\u001b[1;31m║              ADMINISTRATOR CONTROLS               ║\n"
            "\u001b[1;31m╚═══════════════════════════════════════════════════╝\n"
            "```\n"
            "⚠️ **These commands require Administrator permissions**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        embed.add_field(
            name="🏪 **Store Management**",
            value=(
                "> `!setup #channel` - Deploy storefront\n"
                "> `!setchannel <type> #channel` - Set channel\n"
                "> `!addproduct` - Add new product\n"
                "> `!removeproduct <id>` - Remove product\n"
                "> `!setstatus <order_id> <status>` - Update order"
            ),
            inline=False
        )
        embed.add_field(
            name="🔧 **Server Setup**",
            value=(
                "> `!welcome #channel` - Set welcome channel\n"
                "> `!setwelcomestyle <style>` - Change welcome style\n"
                "> `!testwelcome` - Test welcome message\n"
                "> `!disablewelcome` - Disable welcome\n"
                "> `!welcomestats` - Welcome system stats\n"
                "> `!postrules` - Post rules embed"
            ),
            inline=False
        )
        embed.add_field(
            name="💰 **Economy Admin**",
            value=(
                "> `!givecoins @user <amount>` - Give coins\n"
                "> `!removecoins @user <amount>` - Remove coins\n"
                "> `!reseteconomy @user` - Reset user economy"
            ),
            inline=False
        )
        embed.add_field(
            name="📢 **Announcements**",
            value=(
                "> `!announce` - Post announcement\n"
                "> `!say <message>` - Bot sends message\n"
                "> `!dm @user <message>` - DM user as bot"
            ),
            inline=False
        )
        embed.add_field(
            name="⚠️ **Available Welcome Styles**",
            value=(
                "```yaml\n"
                "main      : Full ZeroDay ASCII art\n"
                "compact   : Short clean welcome\n"
                "hacker    : Terminal hacker theme\n"
                "matrix    : Matrix movie theme\n"
                "minimal   : Simple one-box\n"
                "cyberpunk : Cyberpunk night city\n"
                "```"
            ),
            inline=False
        )
        embed.set_footer(text="ZeroDay Tools • Admin Commands • Page 10/10")
        return embed


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.current_page = "home"

    async def update_embed(self, interaction: discord.Interaction, page: str):
        """Update embed based on selected page."""
        self.current_page = page

        embeds = {
            "home": EmbedBuilder.help_embed,
            "shopping": EmbedBuilder.help_shopping,
            "tickets": EmbedBuilder.help_tickets,
            "moderation": EmbedBuilder.help_moderation,
            "economy": EmbedBuilder.help_economy,
            "fun": EmbedBuilder.help_fun,
            "image": EmbedBuilder.help_image,
            "utility": EmbedBuilder.help_utility,
            "info": EmbedBuilder.help_info,
            "admin": EmbedBuilder.help_admin,
        }

        embed_func = embeds.get(page, EmbedBuilder.help_embed)
        await interaction.response.edit_message(embed=embed_func(), view=self)

    @discord.ui.button(emoji="🏠", label="Home", style=discord.ButtonStyle.primary, custom_id="help_home", row=0)
    async def home_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "home")

    @discord.ui.button(emoji="🛒", label="Shop", style=discord.ButtonStyle.success, custom_id="help_shop", row=0)
    async def shop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "shopping")

    @discord.ui.button(emoji="🎫", label="Tickets", style=discord.ButtonStyle.success, custom_id="help_tickets", row=0)
    async def tickets_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "tickets")

    @discord.ui.button(emoji="🔨", label="Mod", style=discord.ButtonStyle.danger, custom_id="help_mod", row=0)
    async def mod_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "moderation")

    @discord.ui.button(emoji="💰", label="Economy", style=discord.ButtonStyle.success, custom_id="help_eco", row=1)
    async def eco_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "economy")

    @discord.ui.button(emoji="🎮", label="Fun", style=discord.ButtonStyle.primary, custom_id="help_fun", row=1)
    async def fun_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "fun")

    @discord.ui.button(emoji="🖼️", label="Image", style=discord.ButtonStyle.primary, custom_id="help_image", row=1)
    async def image_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "image")

    @discord.ui.button(emoji="🛠️", label="Utility", style=discord.ButtonStyle.secondary, custom_id="help_util", row=1)
    async def util_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "utility")

    @discord.ui.button(emoji="📊", label="Info", style=discord.ButtonStyle.secondary, custom_id="help_info", row=2)
    async def info_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "info")

    @discord.ui.button(emoji="⚙️", label="Admin", style=discord.ButtonStyle.danger, custom_id="help_admin", row=2)
    async def admin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "admin")

    @discord.ui.button(emoji="❌", label="Close", style=discord.ButtonStyle.secondary, custom_id="help_close", row=2)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


embeds = EmbedBuilder()
