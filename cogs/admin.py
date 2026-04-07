import discord
from discord.ext import commands
from utils.database import db
from utils.embeds import embeds
import datetime
import os
import platform
import resource
import shutil
import socket
import sys

OWNER_ID = 1170979888019292261

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='setstatus')
    @commands.has_permissions(administrator=True)
    async def set_order_status(self, ctx, order_id: str, status: str):
        """Update order status"""
        
        valid_statuses = ['pending', 'processing', 'completed', 'cancelled']
        
        if status.lower() not in valid_statuses:
            await ctx.send(f"❌ Invalid status! Valid options: {', '.join(valid_statuses)}")
            return
        
        order = db.get_order(order_id)
        
        if not order:
            await ctx.send("❌ Order not found!")
            return
        
        db.update_order(order_id, {'status': status.lower()})
        
        # Notify user
        user = self.bot.get_user(order['user_id'])
        product = db.get_product_by_id(order['product_id'])
        
        if user:
            status_colors = {
                'pending': 0xffa500,
                'processing': 0x00a8ff,
                'completed': 0x00ff00,
                'cancelled': 0xff0000
            }
            
            notify_embed = discord.Embed(
                title=f"📦 Order Status Updated",
                description=f"Your order **{order_id}** status has been updated",
                color=status_colors.get(status.lower(), 0x00ff9d)
            )
            
            notify_embed.add_field(name="Product", value=product['name'], inline=True)
            notify_embed.add_field(name="New Status", value=status.upper(), inline=True)
            
            if status.lower() == 'completed':
                notify_embed.add_field(
                    name="✅ Order Completed",
                    value="Thank you for your purchase! Your product has been delivered.",
                    inline=False
                )
            
            try:
                await user.send(embed=notify_embed)
            except:
                pass
        
        await ctx.send(f"✅ Order **{order_id}** status updated to **{status.upper()}**")
    
    @commands.command(name='stats')
    @commands.has_permissions(administrator=True)
    async def view_stats(self, ctx):
        """View bot statistics"""
        
        products = db.get_products()
        orders = db._read_file(db.orders_file).get('orders', [])
        tickets = db._read_file(db.tickets_file).get('tickets', [])
        
        total_revenue = sum(order['price'] for order in orders if order['status'] == 'completed')
        pending_orders = len([o for o in orders if o['status'] == 'pending'])
        open_tickets = len([t for t in tickets if t['status'] == 'open'])
        
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=0x00ff9d,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="📦 Total Products", value=f"`{len(products)}`", inline=True)
        embed.add_field(name="🛒 Total Orders", value=f"`{len(orders)}`", inline=True)
        embed.add_field(name="💰 Total Revenue", value=f"`${total_revenue:.2f}`", inline=True)
        embed.add_field(name="⏳ Pending Orders", value=f"`{pending_orders}`", inline=True)
        embed.add_field(name="🎫 Open Tickets", value=f"`{open_tickets}`", inline=True)
        embed.add_field(name="👥 Total Users", value=f"`{len(ctx.guild.members)}`", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='ping')
    async def ping_command(self, ctx):
        """Show bot latency and runtime statistics"""
        latency_ms = round(self.bot.latency * 1000, 2)
        guild_count = len(self.bot.guilds)
        user_count = sum(guild.member_count or 0 for guild in self.bot.guilds)
        command_count = len(self.bot.commands)
        uptime_delta = discord.utils.utcnow() - getattr(self.bot, 'launch_time', discord.utils.utcnow())
        uptime_text = str(uptime_delta).split('.')[0]
        process_memory_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        process_memory_mb = round(process_memory_kb / 1024, 2)
        disk_usage = shutil.disk_usage(os.getcwd())
        disk_total_gb = round(disk_usage.total / (1024 ** 3), 2)
        disk_used_gb = round(disk_usage.used / (1024 ** 3), 2)
        disk_free_gb = round(disk_usage.free / (1024 ** 3), 2)
        boot_time = None
        try:
            with open('/proc/uptime', 'r') as f:
                system_uptime_seconds = float(f.read().split()[0])
            boot_time = datetime.datetime.now() - datetime.timedelta(seconds=system_uptime_seconds)
            system_uptime_text = str(datetime.timedelta(seconds=int(system_uptime_seconds)))
        except (FileNotFoundError, ValueError, OSError):
            system_uptime_text = "Unavailable"

        try:
            load_average = ", ".join(f"{value:.2f}" for value in os.getloadavg())
        except (AttributeError, OSError):
            load_average = "Unavailable"

        embed = discord.Embed(
            title="🏓 ZeroDay Tools Status",
            description="Advanced runtime and system diagnostics for the bot.",
            color=0x00ff9d,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="Bot Runtime",
            value=(
                f"> **Latency:** `{latency_ms} ms`\n"
                f"> **Uptime:** `{uptime_text}`\n"
                f"> **PID:** `{os.getpid()}`\n"
                f"> **Commands:** `{command_count}`"
            ),
            inline=False
        )

        embed.add_field(
            name="Discord Stats",
            value=(
                f"> **Servers:** `{guild_count}`\n"
                f"> **Users:** `{user_count}`\n"
                f"> **Current Guild Users:** `{len(ctx.guild.members)}`\n"
                f"> **Avg Users / Server:** `{round(user_count / guild_count, 2) if guild_count else 0}`"
            ),
            inline=False
        )

        embed.add_field(
            name="System Details",
            value=(
                f"> **Host:** `{socket.gethostname()}`\n"
                f"> **OS:** `{platform.system()} {platform.release()}`\n"
                f"> **Kernel:** `{platform.version()[:45]}`\n"
                f"> **Arch:** `{platform.machine()}`"
            ),
            inline=False
        )

        embed.add_field(
            name="Runtime Stack",
            value=(
                f"> **Python:** `{platform.python_version()}`\n"
                f"> **discord.py:** `{discord.__version__}`\n"
                f"> **Executable:** `{sys.executable}`\n"
                f"> **Working Dir:** `{os.getcwd()}`"
            ),
            inline=False
        )

        embed.add_field(
            name="Resource Usage",
            value=(
                f"> **CPU Cores:** `{os.cpu_count()}`\n"
                f"> **Load Avg:** `{load_average}`\n"
                f"> **Process RAM:** `{process_memory_mb} MB`\n"
                f"> **Open FDs:** `{len(os.listdir('/proc/self/fd')) if os.path.exists('/proc/self/fd') else 'Unavailable'}`"
            ),
            inline=False
        )

        embed.add_field(
            name="Storage",
            value=(
                f"> **Disk Total:** `{disk_total_gb} GB`\n"
                f"> **Disk Used:** `{disk_used_gb} GB`\n"
                f"> **Disk Free:** `{disk_free_gb} GB`\n"
                f"> **CWD Exists:** `{'Yes' if os.path.exists(os.getcwd()) else 'No'}`"
            ),
            inline=False
        )

        embed.add_field(
            name="Environment",
            value=(
                f"> **System Uptime:** `{system_uptime_text}`\n"
                f"> **Boot Time:** `{boot_time.strftime('%Y-%m-%d %H:%M:%S') if boot_time else 'Unavailable'}`\n"
                f"> **TZ:** `{os.environ.get('TZ', 'System Default')}`\n"
                f"> **Token Loaded:** `{'Yes' if bool(os.getenv('DISCORD_TOKEN')) else 'No'}`"
            ),
            inline=False
        )

        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)

        embed.set_footer(text="ZeroDay Tools")
        await ctx.send(embed=embed)

    @commands.command(name='purge')
    async def purge_command(self, ctx, amount: int):
        """Owner-only bulk delete for 0-300 messages"""
        if ctx.author.id != OWNER_ID:
            await ctx.send("❌ This command is owner-only.")
            return

        if amount < 0 or amount > 300:
            await ctx.send("❌ Amount must be between 0 and 300.")
            return

        if amount == 0:
            await ctx.send("ℹ️ Nothing to purge.")
            return

        deleted = await ctx.channel.purge(limit=amount + 1)
        confirmation = await ctx.send(f"✅ Deleted `{max(len(deleted) - 1, 0)}` messages.")
        await confirmation.delete(delay=5)
    
    @commands.command(name='help')
    async def help_command(self, ctx):
        """Display help menu"""
        help_embed = embeds.help_embed()
        await ctx.send(embed=help_embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
