import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, Union
import json
import asyncio
import aiohttp
import io
import random
import hashlib
import base64
import string
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import qrcode
import math


class AdvancedCommandsSuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy_file = "database/economy.json"
        self.mod_cases_file = "database/mod_cases.json"
        self.warnings_file = "database/warnings.json"
        self.reminders_file = "database/reminders.json"
        self.todos_file = "database/todos.json"
        self.deleted_messages = {}
        self.edited_messages = {}
        self.tempbans = {}
        
        # Load data
        self.economy_data = self.load_json(self.economy_file)
        self.mod_cases = self.load_json(self.mod_cases_file)
        self.warnings_data = self.load_json(self.warnings_file)
        self.reminders_data = self.load_json(self.reminders_file)
        self.todos_data = self.load_json(self.todos_file)
        
        # Start background tasks
        self.check_reminders.start()
        self.check_tempbans.start()
    
    def cog_unload(self):
        self.check_reminders.cancel()
        self.check_tempbans.cancel()
    
    # ============================================================
    #                    UTILITY FUNCTIONS
    # ============================================================
    
    def load_json(self, filename):
        """Load JSON file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_json(self, filename, data):
        """Save JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_user_economy(self, user_id):
        """Get user economy data"""
        user_id = str(user_id)
        if user_id not in self.economy_data:
            self.economy_data[user_id] = {
                'wallet': 0,
                'bank': 0,
                'inventory': [],
                'last_daily': None,
                'last_weekly': None,
                'last_work': None
            }
            self.save_json(self.economy_file, self.economy_data)
        return self.economy_data[user_id]
    
    async def download_avatar(self, user):
        """Download user avatar as PIL Image"""
        async with aiohttp.ClientSession() as session:
            async with session.get(str(user.display_avatar.url)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert('RGBA')
        return None
    
    def parse_time(self, time_string):
        """Parse time string like 1d, 2h, 30m to timedelta"""
        units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800
        }
        
        match = re.match(r'(\d+)([smhdw])', time_string.lower())
        if match:
            amount, unit = match.groups()
            return timedelta(seconds=int(amount) * units[unit])
        return None

    def _command_usage(self, ctx):
        signature = ctx.command.signature.strip() if ctx.command and ctx.command.signature else ""
        return f"!{ctx.command.qualified_name} {signature}".strip() if ctx.command else "!help"

    async def _send_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("```\n❌ You don't have permission to use this command.\n```")
            return
        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(f"```\n❌ I need these permissions: {perms}\n```")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "```\n"
                f"❌ Missing argument: {error.param.name}\n"
                f"Usage: {self._command_usage(ctx)}\n"
                "```"
            )
            return
        if isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
            await ctx.send(
                "```\n"
                "❌ Invalid argument provided.\n"
                f"Usage: {self._command_usage(ctx)}\n"
                "```"
            )
            return
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"```\n❌ This command is on cooldown. Try again in {error.retry_after:.1f}s.\n```"
            )
            return
        raise error
    
    # ============================================================
    #                    IMAGE MANIPULATION COMMANDS
    # ============================================================
    
    @commands.command(name='blur')
    async def blur_avatar(self, ctx, user: Optional[discord.Member] = None):
        """Blur user's avatar"""
        user = user or ctx.author
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Apply blur
            blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
            
            # Save to bytes
            buffer = io.BytesIO()
            blurred.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='blurred.png')
            
            embed = discord.Embed(
                title="🌫️ Blurred Avatar",
                description=f"**User:** {user.mention}",
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://blurred.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='pixelate')
    async def pixelate_avatar(self, ctx, user: Optional[discord.Member] = None):
        """Pixelate user's avatar"""
        user = user or ctx.author
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Pixelate effect
            small = img.resize((16, 16), Image.NEAREST)
            pixelated = small.resize(img.size, Image.NEAREST)
            
            buffer = io.BytesIO()
            pixelated.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='pixelated.png')
            
            embed = discord.Embed(
                title="🟦 Pixelated Avatar",
                description=f"**User:** {user.mention}",
                color=discord.Color.green()
            )
            embed.set_image(url="attachment://pixelated.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='deepfry')
    async def deepfry_avatar(self, ctx, user: Optional[discord.Member] = None):
        """Deep fry user's avatar"""
        user = user or ctx.author
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Deep fry effects
            img = img.convert('RGB')
            
            # Increase contrast
            contrast = ImageEnhance.Contrast(img)
            img = contrast.enhance(3.0)
            
            # Increase saturation
            color = ImageEnhance.Color(img)
            img = color.enhance(3.0)
            
            # Increase sharpness
            sharpness = ImageEnhance.Sharpness(img)
            img = sharpness.enhance(100.0)
            
            # Add noise (compression artifacts)
            buffer = io.BytesIO()
            img.save(buffer, 'JPEG', quality=1)
            buffer.seek(0)
            
            file = discord.File(buffer, filename='deepfried.jpg')
            
            embed = discord.Embed(
                title="🔥 Deep Fried Avatar",
                description=f"**User:** {user.mention}",
                color=discord.Color.orange()
            )
            embed.set_image(url="attachment://deepfried.jpg")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='invert')
    async def invert_avatar(self, ctx, user: Optional[discord.Member] = None):
        """Invert avatar colors"""
        user = user or ctx.author
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Invert colors
            inverted = ImageOps.invert(img.convert('RGB'))
            
            buffer = io.BytesIO()
            inverted.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='inverted.png')
            
            embed = discord.Embed(
                title="🔄 Inverted Avatar",
                color=discord.Color.purple()
            )
            embed.set_image(url="attachment://inverted.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='grayscale')
    async def grayscale_avatar(self, ctx, user: Optional[discord.Member] = None):
        """Convert avatar to grayscale"""
        user = user or ctx.author
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Convert to grayscale
            gray = ImageOps.grayscale(img)
            
            buffer = io.BytesIO()
            gray.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='grayscale.png')
            
            embed = discord.Embed(
                title="⚫ Grayscale Avatar",
                color=discord.Color.dark_gray()
            )
            embed.set_image(url="attachment://grayscale.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='sepia')
    async def sepia_avatar(self, ctx, user: Optional[discord.Member] = None):
        """Apply sepia filter to avatar"""
        user = user or ctx.author
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Convert to sepia
            img = img.convert('RGB')
            width, height = img.size
            pixels = img.load()
            
            for py in range(height):
                for px in range(width):
                    r, g, b = img.getpixel((px, py))
                    
                    tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                    tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                    tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                    
                    pixels[px, py] = (min(tr, 255), min(tg, 255), min(tb, 255))
            
            buffer = io.BytesIO()
            img.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='sepia.png')
            
            embed = discord.Embed(
                title="🟤 Sepia Filter",
                color=discord.Color.from_rgb(112, 66, 20)
            )
            embed.set_image(url="attachment://sepia.png")
            
            await ctx.send(embed=embed, file=file)
    
    # ============================================================
    #                    ECONOMY COMMANDS
    # ============================================================
    
    @commands.command(name='balance', aliases=['bal', 'money'])
    async def balance(self, ctx, user: Optional[discord.Member] = None):
        """Check balance"""
        user = user or ctx.author
        data = self.get_user_economy(user.id)
        
        total = data['wallet'] + data['bank']
        
        embed = discord.Embed(
            title=f"💰 {user.name}'s Balance",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="💵 Wallet",
            value=f"```💲 {data['wallet']:,}```",
            inline=True
        )
        
        embed.add_field(
            name="🏦 Bank",
            value=f"```💲 {data['bank']:,}```",
            inline=True
        )
        
        embed.add_field(
            name="💎 Net Worth",
            value=f"```💲 {total:,}```",
            inline=True
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='daily')
    async def daily_reward(self, ctx):
        """Claim daily reward"""
        data = self.get_user_economy(ctx.author.id)
        
        now = datetime.utcnow()
        last_daily = data.get('last_daily')
        
        if last_daily:
            last_time = datetime.fromisoformat(last_daily)
            if (now - last_time).total_seconds() < 86400:
                time_left = 86400 - (now - last_time).total_seconds()
                hours = int(time_left // 3600)
                minutes = int((time_left % 3600) // 60)
                
                return await ctx.send(
                    f"```\n⏰ Daily already claimed!\n"
                    f"Come back in {hours}h {minutes}m\n```"
                )
        
        # Give reward
        reward = random.randint(500, 1000)
        data['wallet'] += reward
        data['last_daily'] = now.isoformat()
        
        self.save_json(self.economy_file, self.economy_data)
        
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You received **💲 {reward:,}**",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💵 New Balance",
            value=f"```💲 {data['wallet']:,}```"
        )
        
        embed.set_footer(text="Come back tomorrow for another reward!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='weekly')
    async def weekly_reward(self, ctx):
        """Claim weekly reward"""
        data = self.get_user_economy(ctx.author.id)
        
        now = datetime.utcnow()
        last_weekly = data.get('last_weekly')
        
        if last_weekly:
            last_time = datetime.fromisoformat(last_weekly)
            if (now - last_time).total_seconds() < 604800:
                time_left = 604800 - (now - last_time).total_seconds()
                days = int(time_left // 86400)
                hours = int((time_left % 86400) // 3600)
                
                return await ctx.send(
                    f"```\n⏰ Weekly already claimed!\n"
                    f"Come back in {days}d {hours}h\n```"
                )
        
        # Give reward
        reward = random.randint(5000, 10000)
        data['wallet'] += reward
        data['last_weekly'] = now.isoformat()
        
        self.save_json(self.economy_file, self.economy_data)
        
        embed = discord.Embed(
            title="🎁 Weekly Reward Claimed!",
            description=f"You received **💲 {reward:,}**",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='work')
    async def work(self, ctx):
        """Work for coins"""
        data = self.get_user_economy(ctx.author.id)
        
        now = datetime.utcnow()
        last_work = data.get('last_work')
        
        if last_work:
            last_time = datetime.fromisoformat(last_work)
            if (now - last_time).total_seconds() < 3600:
                time_left = 3600 - (now - last_time).total_seconds()
                minutes = int(time_left // 60)
                
                return await ctx.send(f"```\n⏰ You're tired! Rest for {minutes} minutes\n```")
        
        jobs = [
            ("👨‍💻 Coded a website", 200, 500),
            ("🍕 Delivered pizzas", 150, 400),
            ("🚗 Drove an Uber", 180, 450),
            ("📦 Amazon delivery", 160, 420),
            ("🏗️ Construction work", 200, 550),
            ("🎨 Designed a logo", 250, 600),
            ("📝 Wrote articles", 220, 500),
            ("🎬 Edited videos", 280, 650),
        ]
        
        job, min_pay, max_pay = random.choice(jobs)
        payment = random.randint(min_pay, max_pay)
        
        data['wallet'] += payment
        data['last_work'] = now.isoformat()
        
        self.save_json(self.economy_file, self.economy_data)
        
        embed = discord.Embed(
            title="💼 Work Complete!",
            description=f"{job}\nYou earned **💲 {payment:,}**",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='deposit', aliases=['dep'])
    async def deposit(self, ctx, amount: Union[int, str]):
        """Deposit money to bank"""
        data = self.get_user_economy(ctx.author.id)
        
        if isinstance(amount, str):
            if amount.lower() in ['all', 'max']:
                amount = data['wallet']
            else:
                return await ctx.send("```\n❌ Invalid amount!\n```")
        
        if amount <= 0:
            return await ctx.send("```\n❌ Amount must be positive!\n```")
        
        if amount > data['wallet']:
            return await ctx.send("```\n❌ You don't have that much!\n```")
        
        data['wallet'] -= amount
        data['bank'] += amount
        
        self.save_json(self.economy_file, self.economy_data)
        
        await ctx.send(
            f"```\n"
            f"✅ Deposited 💲 {amount:,} to bank\n"
            f"💵 Wallet: 💲 {data['wallet']:,}\n"
            f"🏦 Bank: 💲 {data['bank']:,}\n"
            f"```"
        )
    
    @commands.command(name='withdraw', aliases=['with'])
    async def withdraw(self, ctx, amount: Union[int, str]):
        """Withdraw money from bank"""
        data = self.get_user_economy(ctx.author.id)
        
        if isinstance(amount, str):
            if amount.lower() in ['all', 'max']:
                amount = data['bank']
            else:
                return await ctx.send("```\n❌ Invalid amount!\n```")
        
        if amount <= 0:
            return await ctx.send("```\n❌ Amount must be positive!\n```")
        
        if amount > data['bank']:
            return await ctx.send("```\n❌ You don't have that much in bank!\n```")
        
        data['bank'] -= amount
        data['wallet'] += amount
        
        self.save_json(self.economy_file, self.economy_data)
        
        await ctx.send(
            f"```\n"
            f"✅ Withdrew 💲 {amount:,} from bank\n"
            f"💵 Wallet: 💲 {data['wallet']:,}\n"
            f"🏦 Bank: 💲 {data['bank']:,}\n"
            f"```"
        )
    
    # ============================================================
    #                    MODERATION COMMANDS
    # ============================================================
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member"""
        
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("```\n❌ You can't kick this user!\n```")
        
        # Try to DM user
        try:
            dm_embed = discord.Embed(
                title="⚠️ You were kicked",
                description=f"**Server:** {ctx.guild.name}\n**Reason:** {reason}",
                color=discord.Color.orange()
            )
            await member.send(embed=dm_embed)
        except:
            pass
        
        # Kick
        await member.kick(reason=f"Kicked by {ctx.author} | {reason}")
        
        # Log case
        case_id = len(self.mod_cases.get(str(ctx.guild.id), [])) + 1
        
        if str(ctx.guild.id) not in self.mod_cases:
            self.mod_cases[str(ctx.guild.id)] = []
        
        self.mod_cases[str(ctx.guild.id)].append({
            'case_id': case_id,
            'type': 'kick',
            'user_id': member.id,
            'moderator_id': ctx.author.id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        self.save_json(self.mod_cases_file, self.mod_cases)
        
        # Send confirmation
        embed = discord.Embed(
            title="👢 Member Kicked",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{member.mention}\n`{member.id}`", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Case ID", value=f"`#{case_id}`", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: Union[discord.Member, int], *, reason="No reason provided"):
        """Ban a member"""
        
        if isinstance(member, discord.Member):
            if member.top_role >= ctx.author.top_role:
                return await ctx.send("```\n❌ You can't ban this user!\n```")
            
            # Try to DM
            try:
                dm_embed = discord.Embed(
                    title="🔨 You were banned",
                    description=f"**Server:** {ctx.guild.name}\n**Reason:** {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            user_id = member.id
            await member.ban(reason=f"Banned by {ctx.author} | {reason}")
        else:
            user_id = member
            await ctx.guild.ban(discord.Object(id=user_id), reason=f"Banned by {ctx.author} | {reason}")
        
        # Log case
        case_id = len(self.mod_cases.get(str(ctx.guild.id), [])) + 1
        
        if str(ctx.guild.id) not in self.mod_cases:
            self.mod_cases[str(ctx.guild.id)] = []
        
        self.mod_cases[str(ctx.guild.id)].append({
            'case_id': case_id,
            'type': 'ban',
            'user_id': user_id,
            'moderator_id': ctx.author.id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        self.save_json(self.mod_cases_file, self.mod_cases)
        
        embed = discord.Embed(
            title="🔨 Member Banned",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Case ID", value=f"`#{case_id}`", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='purge', aliases=['clear', 'clean'])
    @commands.has_permissions(manage_messages=True)
    async def purge_messages(self, ctx, amount: int):
        """Delete messages in bulk"""
        
        if amount <= 0 or amount > 100:
            return await ctx.send("```\n❌ Amount must be between 1 and 100!\n```")
        
        deleted = await ctx.channel.purge(limit=amount + 1)
        
        await ctx.send(
            f"```\n✅ Deleted {len(deleted) - 1} messages\n```",
            delete_after=5
        )
    
    # ============================================================
    #                    UTILITY COMMANDS
    # ============================================================
    
    @commands.command(name='remind', aliases=['reminder', 'remindme'])
    async def set_reminder(self, ctx, time: str, *, message: str):
        """Set a reminder"""
        
        duration = self.parse_time(time)
        
        if not duration:
            return await ctx.send("```\n❌ Invalid time format! Use: 1d, 2h, 30m, etc.\n```")
        
        remind_time = datetime.utcnow() + duration
        
        user_id = str(ctx.author.id)
        
        if user_id not in self.reminders_data:
            self.reminders_data[user_id] = []
        
        reminder_id = len(self.reminders_data[user_id]) + 1
        
        self.reminders_data[user_id].append({
            'id': reminder_id,
            'message': message,
            'channel_id': ctx.channel.id,
            'remind_at': remind_time.isoformat(),
            'created_at': datetime.utcnow().isoformat()
        })
        
        self.save_json(self.reminders_file, self.reminders_data)
        
        await ctx.send(
            f"```\n"
            f"⏰ Reminder set!\n"
            f"I'll remind you in {time}\n"
            f"Message: {message[:50]}...\n"
            f"```"
        )
    
    @commands.command(name='calculate', aliases=['calc', 'math'])
    async def calculator(self, ctx, *, expression: str):
        """Calculate math expression"""
        
        try:
            # Safe eval (limited)
            allowed = '0123456789+-*/().^ '
            
            if not all(c in allowed for c in expression.replace('**', '^')):
                return await ctx.send("```\n❌ Invalid characters in expression!\n```")
            
            expression = expression.replace('^', '**')
            
            result = eval(expression, {"__builtins__": {}}, {})
            
            embed = discord.Embed(
                title="🧮 Calculator",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Expression", value=f"```{expression}```", inline=False)
            embed.add_field(name="Result", value=f"```{result}```", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"```\n❌ Error: {str(e)}\n```")
    
    @commands.command(name='qrcode', aliases=['qr'])
    async def generate_qr(self, ctx, *, data: str):
        """Generate QR code"""
        
        async with ctx.typing():
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='qrcode.png')
            
            embed = discord.Embed(
                title="📱 QR Code Generated",
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://qrcode.png")
            embed.set_footer(text=f"Data: {data[:100]}...")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='password', aliases=['genpass', 'passgen'])
    async def generate_password(self, ctx, length: int = 16):
        """Generate random password"""
        
        if length < 8 or length > 64:
            return await ctx.send("```\n❌ Length must be between 8 and 64!\n```")
        
        chars = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(chars) for _ in range(length))
        
        try:
            await ctx.author.send(
                f"```\n"
                f"🔐 Generated Password\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{password}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Length: {length} characters\n"
                f"```"
            )
            await ctx.send("✅ Password sent to your DMs!")
        except:
            await ctx.send("❌ Enable DMs to receive password!")
    
    @commands.command(name='snipe')
    async def snipe_message(self, ctx):
        """Recover last deleted message"""
        
        channel_id = ctx.channel.id
        
        if channel_id not in self.deleted_messages:
            return await ctx.send("```\n❌ No recently deleted messages!\n```")
        
        msg_data = self.deleted_messages[channel_id]
        
        embed = discord.Embed(
            title="🎯 Message Sniped",
            description=msg_data['content'],
            color=discord.Color.red(),
            timestamp=msg_data['deleted_at']
        )
        
        embed.set_author(
            name=msg_data['author_name'],
            icon_url=msg_data['author_avatar']
        )
        
        embed.set_footer(text=f"Deleted by {msg_data['author_name']}")
        
        await ctx.send(embed=embed)
    
    # ============================================================
    #                    FUN COMMANDS
    # ============================================================
    
    @commands.command(name='8ball')
    async def magic_8ball(self, ctx, *, question: str):
        """Ask the magic 8ball"""
        
        responses = [
            "Yes, definitely!",
            "Without a doubt!",
            "Absolutely!",
            "My sources say yes",
            "Most likely",
            "Maybe...",
            "Ask again later",
            "Cannot predict now",
            "Don't count on it",
            "No way!",
            "Absolutely not!",
            "My sources say no"
        ]
        
        answer = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8Ball",
            color=discord.Color.purple()
        )
        
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=f"**{answer}**", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='coinflip', aliases=['flip'])
    async def coin_flip(self, ctx):
        """Flip a coin"""
        
        result = random.choice(['Heads', 'Tails'])
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on **{result}**!",
            color=discord.Color.gold()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='roll')
    async def roll_dice(self, ctx, dice: str = "1d6"):
        """Roll dice (format: NdN)"""
        
        try:
            rolls, sides = map(int, dice.lower().split('d'))
            
            if rolls < 1 or rolls > 100:
                return await ctx.send("```\n❌ Number of rolls must be 1-100!\n```")
            
            if sides < 2 or sides > 1000:
                return await ctx.send("```\n❌ Sides must be 2-1000!\n```")
            
            results = [random.randint(1, sides) for _ in range(rolls)]
            total = sum(results)
            
            embed = discord.Embed(
                title=f"🎲 Dice Roll: {dice}",
                color=discord.Color.blue()
            )
            
            if len(results) <= 20:
                embed.add_field(name="Results", value=f"```{', '.join(map(str, results))}```", inline=False)
            
            embed.add_field(name="Total", value=f"```{total}```", inline=True)
            embed.add_field(name="Average", value=f"```{total/rolls:.2f}```", inline=True)
            
            await ctx.send(embed=embed)
            
        except:
            await ctx.send("```\n❌ Invalid dice format! Use: 2d6, 1d20, etc.\n```")
    
    # ============================================================
    #                    BACKGROUND TASKS
    # ============================================================
    
    @tasks.loop(seconds=60)
    async def check_reminders(self):
        """Check for due reminders"""
        
        now = datetime.utcnow()
        
        for user_id, reminders in list(self.reminders_data.items()):
            for reminder in reminders[:]:
                remind_time = datetime.fromisoformat(reminder['remind_at'])
                
                if now >= remind_time:
                    # Send reminder
                    user = self.bot.get_user(int(user_id))
                    channel = self.bot.get_channel(reminder['channel_id'])
                    
                    if user and channel:
                        embed = discord.Embed(
                            title="⏰ Reminder!",
                            description=reminder['message'],
                            color=discord.Color.blue(),
                            timestamp=datetime.fromisoformat(reminder['created_at'])
                        )
                        
                        embed.set_footer(text=f"Set {(now - datetime.fromisoformat(reminder['created_at'])).days} days ago")
                        
                        try:
                            await channel.send(f"{user.mention}", embed=embed)
                        except:
                            pass
                    
                    # Remove reminder
                    reminders.remove(reminder)
        
        self.save_json(self.reminders_file, self.reminders_data)
    
    @tasks.loop(seconds=60)
    async def check_tempbans(self):
        """Check for expired tempbans"""
        
        now = datetime.utcnow()
        
        for guild_id, bans in list(self.tempbans.items()):
            guild = self.bot.get_guild(int(guild_id))
            
            if not guild:
                continue
            
            for user_id, unban_time in list(bans.items()):
                if now >= datetime.fromisoformat(unban_time):
                    try:
                        await guild.unban(discord.Object(id=int(user_id)), reason="Tempban expired")
                        del self.tempbans[guild_id][user_id]
                    except:
                        pass
    
    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()
    
    @check_tempbans.before_loop
    async def before_check_tempbans(self):
        await self.bot.wait_until_ready()
    
    # ============================================================
    #                    EVENT LISTENERS
    # ============================================================
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Track deleted messages for snipe"""
        
        if message.author.bot:
            return
        
        self.deleted_messages[message.channel.id] = {
            'content': message.content,
            'author_name': message.author.name,
            'author_avatar': str(message.author.display_avatar.url),
            'deleted_at': datetime.utcnow()
        }
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Track edited messages"""
        
        if before.author.bot:
            return
        
        self.edited_messages[before.channel.id] = {
            'before': before.content,
            'after': after.content,
            'author_name': before.author.name,
            'edited_at': datetime.utcnow()
        }

    async def cog_command_error(self, ctx, error):
        if getattr(ctx.command, "on_error", None):
            return
        await self._send_command_error(ctx, error)


async def setup(bot):
    await bot.add_cog(AdvancedCommandsSuite(bot))
