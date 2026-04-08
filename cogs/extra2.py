# ============================================================
#                    PART 2 - CONTINUED COMMANDS
# ============================================================
# Add this to the same file (cmds.py) or create a new cog

import discord
from discord.ext import commands, tasks
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
import math


class AdvancedCommandsPart2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy_file = "database/economy.json"
        self.mod_cases_file = "database/mod_cases.json"
        self.warnings_file = "database/warnings.json"
        self.shop_items = {
            'fishing_rod': {'name': '🎣 Fishing Rod', 'price': 500, 'description': 'Catch fish for coins'},
            'pickaxe': {'name': '⛏️ Pickaxe', 'price': 750, 'description': 'Mine for gems'},
            'laptop': {'name': '💻 Laptop', 'price': 2000, 'description': 'Work from home bonus'},
            'lucky_coin': {'name': '🍀 Lucky Coin', 'price': 1500, 'description': '+10% gambling luck'},
            'bank_note': {'name': '📜 Bank Note', 'price': 3000, 'description': 'Increase bank limit'},
            'shield': {'name': '🛡️ Shield', 'price': 5000, 'description': 'Protection from robbery'},
            'padlock': {'name': '🔒 Padlock', 'price': 2500, 'description': 'Extra security'},
            'trophy': {'name': '🏆 Trophy', 'price': 10000, 'description': 'Show off your wealth'},
        }
        
        # Load data
        self.economy_data = self.load_json(self.economy_file)
        self.mod_cases = self.load_json(self.mod_cases_file)
        self.warnings_data = self.load_json(self.warnings_file)
    
    def load_json(self, filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_json(self, filename, data):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get_user_economy(self, user_id):
        user_id = str(user_id)
        if user_id not in self.economy_data:
            self.economy_data[user_id] = {
                'wallet': 0,
                'bank': 0,
                'inventory': [],
                'last_daily': None,
                'last_weekly': None,
                'last_work': None,
                'last_crime': None,
                'last_rob': None
            }
            self.save_json(self.economy_file, self.economy_data)
        return self.economy_data[user_id]
    
    async def download_avatar(self, user):
        async with aiohttp.ClientSession() as session:
            async with session.get(str(user.display_avatar.url)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert('RGBA')
        return None
    
    # ============================================================
    #              MORE IMAGE MANIPULATION COMMANDS
    # ============================================================
    
    @commands.command(name='brightness')
    async def adjust_brightness(self, ctx, user: Optional[discord.Member] = None, value: float = 1.5):
        """Adjust avatar brightness"""
        user = user or ctx.author
        
        if value < 0.1 or value > 3.0:
            return await ctx.send("```\n❌ Value must be between 0.1 and 3.0!\n```")
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            enhancer = ImageEnhance.Brightness(img)
            result = enhancer.enhance(value)
            
            buffer = io.BytesIO()
            result.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='brightness.png')
            
            embed = discord.Embed(
                title=f"☀️ Brightness Adjusted ({value}x)",
                color=discord.Color.yellow()
            )
            embed.set_image(url="attachment://brightness.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='contrast')
    async def adjust_contrast(self, ctx, user: Optional[discord.Member] = None, value: float = 1.5):
        """Adjust avatar contrast"""
        user = user or ctx.author
        
        if value < 0.1 or value > 3.0:
            return await ctx.send("```\n❌ Value must be between 0.1 and 3.0!\n```")
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            enhancer = ImageEnhance.Contrast(img)
            result = enhancer.enhance(value)
            
            buffer = io.BytesIO()
            result.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='contrast.png')
            
            embed = discord.Embed(
                title=f"🎨 Contrast Adjusted ({value}x)",
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://contrast.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='rotate')
    async def rotate_avatar(self, ctx, user: Optional[discord.Member] = None, degrees: int = 90):
        """Rotate avatar"""
        user = user or ctx.author
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            rotated = img.rotate(degrees, expand=True)
            
            buffer = io.BytesIO()
            rotated.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='rotated.png')
            
            embed = discord.Embed(
                title=f"🔄 Rotated {degrees}°",
                color=discord.Color.green()
            )
            embed.set_image(url="attachment://rotated.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='flip')
    async def flip_avatar(self, ctx, user: Optional[discord.Member] = None):
        """Flip avatar vertically"""
        user = user or ctx.author
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            flipped = ImageOps.flip(img)
            
            buffer = io.BytesIO()
            flipped.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='flipped.png')
            
            embed = discord.Embed(
                title="🔃 Flipped Avatar",
                color=discord.Color.purple()
            )
            embed.set_image(url="attachment://flipped.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='mirror')
    async def mirror_avatar(self, ctx, user: Optional[discord.Member] = None):
        """Mirror avatar horizontally"""
        user = user or ctx.author
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            mirrored = ImageOps.mirror(img)
            
            buffer = io.BytesIO()
            mirrored.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='mirrored.png')
            
            embed = discord.Embed(
                title="🪞 Mirrored Avatar",
                color=discord.Color.teal()
            )
            embed.set_image(url="attachment://mirrored.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='resize')
    async def resize_avatar(self, ctx, user: Optional[discord.Member] = None, width: int = 256, height: int = 256):
        """Resize avatar"""
        user = user or ctx.author
        
        if width < 16 or width > 1024 or height < 16 or height > 1024:
            return await ctx.send("```\n❌ Size must be between 16 and 1024!\n```")
        
        async with ctx.typing():
            img = await self.download_avatar(user)
            if not img:
                return await ctx.send("❌ Failed to download avatar!")
            
            resized = img.resize((width, height), Image.LANCZOS)
            
            buffer = io.BytesIO()
            resized.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='resized.png')
            
            embed = discord.Embed(
                title=f"📐 Resized to {width}x{height}",
                color=discord.Color.orange()
            )
            embed.set_image(url="attachment://resized.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='wanted')
    async def wanted_poster(self, ctx, user: Optional[discord.Member] = None):
        """Generate wanted poster"""
        user = user or ctx.author
        
        async with ctx.typing():
            avatar = await self.download_avatar(user)
            if not avatar:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Create wanted poster
            poster = Image.new('RGB', (400, 500), color=(139, 90, 43))
            draw = ImageDraw.Draw(poster)
            
            # Add text
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                reward_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 25)
            except:
                title_font = ImageFont.load_default()
                reward_font = ImageFont.load_default()
            
            draw.text((200, 30), "WANTED", fill='black', font=title_font, anchor='mm')
            draw.text((200, 70), "DEAD OR ALIVE", fill='darkred', font=reward_font, anchor='mm')
            
            # Paste avatar
            avatar_resized = avatar.resize((250, 250))
            poster.paste(avatar_resized, (75, 100))
            
            # Add reward
            reward = random.randint(10000, 1000000)
            draw.text((200, 400), f"{user.name[:20]}", fill='black', font=reward_font, anchor='mm')
            draw.text((200, 450), f"REWARD: ${reward:,}", fill='darkgreen', font=reward_font, anchor='mm')
            
            buffer = io.BytesIO()
            poster.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='wanted.png')
            
            embed = discord.Embed(
                title="🤠 WANTED",
                description=f"{user.mention} is now wanted!",
                color=discord.Color.from_rgb(139, 90, 43)
            )
            embed.set_image(url="attachment://wanted.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='jail')
    async def jail_image(self, ctx, user: Optional[discord.Member] = None):
        """Put someone in jail"""
        user = user or ctx.author
        
        async with ctx.typing():
            avatar = await self.download_avatar(user)
            if not avatar:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Create jail image
            size = 256
            avatar = avatar.resize((size, size))
            
            # Create jail bars
            jail = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(jail)
            
            bar_width = 15
            bar_spacing = 40
            
            for x in range(0, size, bar_spacing):
                draw.rectangle([x, 0, x + bar_width, size], fill=(50, 50, 50, 200))
            
            # Combine
            avatar.paste(jail, (0, 0), jail)
            
            buffer = io.BytesIO()
            avatar.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='jail.png')
            
            embed = discord.Embed(
                title="🔒 JAILED",
                description=f"{user.mention} has been sent to jail!",
                color=discord.Color.dark_gray()
            )
            embed.set_image(url="attachment://jail.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='rip')
    async def rip_image(self, ctx, user: Optional[discord.Member] = None):
        """Generate RIP tombstone"""
        user = user or ctx.author
        
        async with ctx.typing():
            avatar = await self.download_avatar(user)
            if not avatar:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Create tombstone
            tombstone = Image.new('RGB', (300, 400), color=(80, 80, 80))
            draw = ImageDraw.Draw(tombstone)
            
            # Draw tombstone shape
            draw.rectangle([20, 50, 280, 380], fill=(120, 120, 120))
            draw.ellipse([20, 20, 280, 150], fill=(120, 120, 120))
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            draw.text((150, 60), "R.I.P", fill='white', font=font, anchor='mm')
            
            # Paste avatar
            avatar_small = avatar.resize((120, 120)).convert('L')  # Grayscale
            avatar_small = avatar_small.convert('RGB')
            tombstone.paste(avatar_small, (90, 130))
            
            draw.text((150, 280), user.name[:15], fill='white', font=small_font, anchor='mm')
            draw.text((150, 320), "Gone but not", fill='white', font=small_font, anchor='mm')
            draw.text((150, 345), "forgotten", fill='white', font=small_font, anchor='mm')
            
            buffer = io.BytesIO()
            tombstone.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='rip.png')
            
            embed = discord.Embed(
                title="⚰️ Rest In Peace",
                description=f"Press F to pay respects for {user.mention}",
                color=discord.Color.dark_gray()
            )
            embed.set_image(url="attachment://rip.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='triggered')
    async def triggered_image(self, ctx, user: Optional[discord.Member] = None):
        """Create triggered image"""
        user = user or ctx.author
        
        async with ctx.typing():
            avatar = await self.download_avatar(user)
            if not avatar:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Apply red tint and effects
            avatar = avatar.convert('RGB')
            
            # Increase red channel
            r, g, b = avatar.split()
            r = r.point(lambda i: min(255, i + 50))
            avatar = Image.merge('RGB', (r, g, b))
            
            # Add sharpness for angry look
            enhancer = ImageEnhance.Sharpness(avatar)
            avatar = enhancer.enhance(2.0)
            
            # Create triggered banner
            final = Image.new('RGB', (256, 290), color=(255, 0, 0))
            final.paste(avatar.resize((256, 256)), (0, 0))
            
            draw = ImageDraw.Draw(final)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
            except:
                font = ImageFont.load_default()
            
            draw.rectangle([0, 256, 256, 290], fill=(255, 0, 0))
            draw.text((128, 273), "TRIGGERED", fill='white', font=font, anchor='mm')
            
            buffer = io.BytesIO()
            final.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='triggered.png')
            
            embed = discord.Embed(
                title="😤 TRIGGERED",
                description=f"{user.mention} is triggered!",
                color=discord.Color.red()
            )
            embed.set_image(url="attachment://triggered.png")
            
            await ctx.send(embed=embed, file=file)
    
    @commands.command(name='trash')
    async def trash_image(self, ctx, user: Optional[discord.Member] = None):
        """Put someone in trash"""
        user = user or ctx.author
        
        async with ctx.typing():
            avatar = await self.download_avatar(user)
            if not avatar:
                return await ctx.send("❌ Failed to download avatar!")
            
            # Create trash can image
            trash = Image.new('RGB', (200, 300), color=(100, 100, 100))
            draw = ImageDraw.Draw(trash)
            
            # Draw trash can
            draw.rectangle([20, 50, 180, 280], fill=(70, 70, 70))
            draw.rectangle([10, 30, 190, 60], fill=(50, 50, 50))
            
            # Paste avatar in trash
            avatar_small = avatar.resize((120, 120))
            trash.paste(avatar_small, (40, 100))
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            draw.text((100, 250), "TRASH", fill='white', font=font, anchor='mm')
            
            buffer = io.BytesIO()
            trash.save(buffer, 'PNG')
            buffer.seek(0)
            
            file = discord.File(buffer, filename='trash.png')
            
            embed = discord.Embed(
                title="🗑️ Trash",
                description=f"{user.mention} belongs in the trash!",
                color=discord.Color.dark_gray()
            )
            embed.set_image(url="attachment://trash.png")
            
            await ctx.send(embed=embed, file=file)
    
    # ============================================================
    #              ECONOMY COMMANDS (CONTINUED)
    # ============================================================
    
    @commands.command(name='crime')
    async def commit_crime(self, ctx):
        """Commit a crime for coins (risky)"""
        data = self.get_user_economy(ctx.author.id)
        
        now = datetime.utcnow()
        last_crime = data.get('last_crime')
        
        if last_crime:
            last_time = datetime.fromisoformat(last_crime)
            if (now - last_time).total_seconds() < 3600:
                time_left = 3600 - (now - last_time).total_seconds()
                minutes = int(time_left // 60)
                return await ctx.send(f"```\n⏰ Wait {minutes} minutes before committing another crime!\n```")
        
        crimes = [
            ("🏦 Robbed a bank", 500, 2000, 0.4),
            ("💎 Stole jewelry", 300, 1500, 0.5),
            ("🚗 Stole a car", 400, 1800, 0.45),
            ("💻 Hacked a company", 600, 2500, 0.35),
            ("🎰 Rigged a casino", 800, 3000, 0.3),
        ]
        
        crime, min_reward, max_reward, success_rate = random.choice(crimes)
        
        data['last_crime'] = now.isoformat()
        
        if random.random() < success_rate:
            # Success
            reward = random.randint(min_reward, max_reward)
            data['wallet'] += reward
            
            embed = discord.Embed(
                title="✅ Crime Successful!",
                description=f"{crime}\nYou got away with **💲 {reward:,}**",
                color=discord.Color.green()
            )
        else:
            # Caught
            fine = random.randint(200, 500)
            data['wallet'] = max(0, data['wallet'] - fine)
            
            embed = discord.Embed(
                title="❌ You Got Caught!",
                description=f"The police caught you!\nYou paid a fine of **💲 {fine:,}**",
                color=discord.Color.red()
            )
        
        self.save_json(self.economy_file, self.economy_data)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rob')
    async def rob_user(self, ctx, user: discord.Member):
        """Rob another user"""
        if user.id == ctx.author.id:
            return await ctx.send("```\n❌ You can't rob yourself!\n```")
        
        if user.bot:
            return await ctx.send("```\n❌ You can't rob bots!\n```")
        
        robber_data = self.get_user_economy(ctx.author.id)
        victim_data = self.get_user_economy(user.id)
        
        now = datetime.utcnow()
        last_rob = robber_data.get('last_rob')
        
        if last_rob:
            last_time = datetime.fromisoformat(last_rob)
            if (now - last_time).total_seconds() < 7200:
                time_left = 7200 - (now - last_time).total_seconds()
                hours = int(time_left // 3600)
                minutes = int((time_left % 3600) // 60)
                return await ctx.send(f"```\n⏰ Wait {hours}h {minutes}m before robbing again!\n```")
        
        if victim_data['wallet'] < 100:
            return await ctx.send("```\n❌ They're too poor to rob!\n```")
        
        # Check for shield
        if 'shield' in victim_data.get('inventory', []):
            return await ctx.send(f"```\n🛡️ {user.name} has a shield! You can't rob them.\n```")
        
        robber_data['last_rob'] = now.isoformat()
        
        success_rate = 0.5
        
        if random.random() < success_rate:
            # Success
            steal_percent = random.uniform(0.1, 0.5)
            stolen = int(victim_data['wallet'] * steal_percent)
            
            victim_data['wallet'] -= stolen
            robber_data['wallet'] += stolen
            
            embed = discord.Embed(
                title="💰 Robbery Successful!",
                description=f"You stole **💲 {stolen:,}** from {user.mention}!",
                color=discord.Color.green()
            )
        else:
            # Failed
            fine = random.randint(100, 300)
            robber_data['wallet'] = max(0, robber_data['wallet'] - fine)
            
            embed = discord.Embed(
                title="❌ Robbery Failed!",
                description=f"{user.mention} caught you!\nYou paid **💲 {fine:,}** in damages.",
                color=discord.Color.red()
            )
        
        self.save_json(self.economy_file, self.economy_data)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='pay', aliases=['give', 'transfer'])
    async def pay_user(self, ctx, user: discord.Member, amount: int):
        """Pay another user"""
        if user.id == ctx.author.id:
            return await ctx.send("```\n❌ You can't pay yourself!\n```")
        
        if amount <= 0:
            return await ctx.send("```\n❌ Amount must be positive!\n```")
        
        payer_data = self.get_user_economy(ctx.author.id)
        receiver_data = self.get_user_economy(user.id)
        
        if payer_data['wallet'] < amount:
            return await ctx.send("```\n❌ You don't have enough money!\n```")
        
        payer_data['wallet'] -= amount
        receiver_data['wallet'] += amount
        
        self.save_json(self.economy_file, self.economy_data)
        
        embed = discord.Embed(
            title="💸 Payment Sent",
            description=f"You sent **💲 {amount:,}** to {user.mention}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='shop')
    async def view_shop(self, ctx):
        """View shop items"""
        embed = discord.Embed(
            title="🛒 Shop",
            description="Use `!buy <item>` to purchase",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        for item_id, item in self.shop_items.items():
            embed.add_field(
                name=f"{item['name']} - 💲 {item['price']:,}",
                value=f"```{item['description']}\nID: {item_id}```",
                inline=False
            )
        
        embed.set_footer(text="Use !buyitem <item_id> to purchase")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='buyitem', aliases=['shopbuy'])
    async def buy_item(self, ctx, item_id: str):
        """Buy item from shop"""
        item_id = item_id.lower()
        
        if item_id not in self.shop_items:
            return await ctx.send("```\n❌ Item not found! Use !shop to see available items.\n```")
        
        item = self.shop_items[item_id]
        data = self.get_user_economy(ctx.author.id)
        
        if data['wallet'] < item['price']:
            return await ctx.send(f"```\n❌ You need 💲 {item['price']:,} to buy this!\n```")
        
        data['wallet'] -= item['price']
        
        if 'inventory' not in data:
            data['inventory'] = []
        
        data['inventory'].append(item_id)
        
        self.save_json(self.economy_file, self.economy_data)
        
        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"You bought {item['name']} for **💲 {item['price']:,}**",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='inventory', aliases=['inv'])
    async def view_inventory(self, ctx, user: Optional[discord.Member] = None):
        """View inventory"""
        user = user or ctx.author
        data = self.get_user_economy(user.id)
        
        inventory = data.get('inventory', [])
        
        if not inventory:
            return await ctx.send(f"```\n📦 {user.name}'s inventory is empty!\n```")
        
        embed = discord.Embed(
            title=f"📦 {user.name}'s Inventory",
            color=discord.Color.blue()
        )
        
        item_counts = {}
        for item_id in inventory:
            item_counts[item_id] = item_counts.get(item_id, 0) + 1
        
        items_text = ""
        for item_id, count in item_counts.items():
            if item_id in self.shop_items:
                item = self.shop_items[item_id]
                items_text += f"{item['name']} x{count}\n"
        
        embed.description = f"```\n{items_text}```"
        
        await ctx.send(embed=embed)
    
    @commands.command(name='sell')
    async def sell_item(self, ctx, item_id: str):
        """Sell item from inventory"""
        item_id = item_id.lower()
        data = self.get_user_economy(ctx.author.id)
        
        if item_id not in data.get('inventory', []):
            return await ctx.send("```\n❌ You don't have this item!\n```")
        
        if item_id not in self.shop_items:
            return await ctx.send("```\n❌ Invalid item!\n```")
        
        item = self.shop_items[item_id]
        sell_price = item['price'] // 2  # 50% sell value
        
        data['inventory'].remove(item_id)
        data['wallet'] += sell_price
        
        self.save_json(self.economy_file, self.economy_data)
        
        embed = discord.Embed(
            title="💰 Item Sold",
            description=f"You sold {item['name']} for **💲 {sell_price:,}**",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='gamble', aliases=['bet'])
    async def gamble(self, ctx, amount: Union[int, str]):
        """Gamble your coins"""
        data = self.get_user_economy(ctx.author.id)
        
        if isinstance(amount, str):
            if amount.lower() in ['all', 'max']:
                amount = data['wallet']
            else:
                return await ctx.send("```\n❌ Invalid amount!\n```")
        
        if amount <= 0:
            return await ctx.send("```\n❌ Amount must be positive!\n```")
        
        if amount > data['wallet']:
            return await ctx.send("```\n❌ You don't have enough!\n```")
        
        # 45% win chance
        if random.random() < 0.45:
            winnings = amount * 2
            data['wallet'] += amount
            result = "won"
            color = discord.Color.green()
        else:
            winnings = -amount
            data['wallet'] -= amount
            result = "lost"
            color = discord.Color.red()
        
        self.save_json(self.economy_file, self.economy_data)
        
        embed = discord.Embed(
            title=f"🎰 You {result}!",
            description=f"You {result} **💲 {abs(winnings):,}**\nNew balance: **💲 {data['wallet']:,}**",
            color=color
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='slots')
    async def slot_machine(self, ctx, amount: int):
        """Play slot machine"""
        data = self.get_user_economy(ctx.author.id)
        
        if amount <= 0:
            return await ctx.send("```\n❌ Amount must be positive!\n```")
        
        if amount > data['wallet']:
            return await ctx.send("```\n❌ You don't have enough!\n```")
        
        data['wallet'] -= amount
        
        symbols = ['🍒', '🍋', '🍊', '🍇', '💎', '7️⃣', '🔔', '⭐']
        weights = [30, 25, 20, 15, 5, 3, 1, 1]
        
        reel1 = random.choices(symbols, weights=weights)[0]
        reel2 = random.choices(symbols, weights=weights)[0]
        reel3 = random.choices(symbols, weights=weights)[0]
        
        # Calculate winnings
        multiplier = 0
        
        if reel1 == reel2 == reel3:
            if reel1 == '7️⃣':
                multiplier = 100
            elif reel1 == '💎':
                multiplier = 50
            elif reel1 == '⭐':
                multiplier = 25
            else:
                multiplier = 10
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            multiplier = 2
        
        winnings = amount * multiplier
        data['wallet'] += winnings
        
        self.save_json(self.economy_file, self.economy_data)
        
        embed = discord.Embed(
            title="🎰 Slot Machine",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Result",
            value=f"```\n[ {reel1} | {reel2} | {reel3} ]\n```",
            inline=False
        )
        
        if multiplier > 0:
            embed.add_field(
                name="🎉 You Won!",
                value=f"**💲 {winnings:,}** ({multiplier}x)",
                inline=False
            )
            embed.color = discord.Color.green()
        else:
            embed.add_field(
                name="😔 You Lost",
                value=f"Better luck next time!",
                inline=False
            )
            embed.color = discord.Color.red()
        
        embed.add_field(name="Balance", value=f"💲 {data['wallet']:,}", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='blackjack', aliases=['bj'])
    async def blackjack(self, ctx, amount: int):
        """Play blackjack"""
        data = self.get_user_economy(ctx.author.id)
        
        if amount <= 0:
            return await ctx.send("```\n❌ Amount must be positive!\n```")
        
        if amount > data['wallet']:
            return await ctx.send("```\n❌ You don't have enough!\n```")
        
        data['wallet'] -= amount
        
        # Card values
        cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        suits = ['♠️', '♥️', '♦️', '♣️']
        
        def draw_card():
            return random.choice(cards), random.choice(suits)
        
        def calculate_hand(hand):
            value = 0
            aces = 0
            
            for card, _ in hand:
                if card in ['J', 'Q', 'K']:
                    value += 10
                elif card == 'A':
                    value += 11
                    aces += 1
                else:
                    value += int(card)
            
            while value > 21 and aces > 0:
                value -= 10
                aces -= 1
            
            return value
        
        def hand_to_string(hand):
            return ' '.join([f"[{card}{suit}]" for card, suit in hand])
        
        # Deal initial cards
        player_hand = [draw_card(), draw_card()]
        dealer_hand = [draw_card(), draw_card()]
        
        player_value = calculate_hand(player_hand)
        
        # Check for natural blackjack
        if player_value == 21:
            winnings = int(amount * 2.5)
            data['wallet'] += winnings
            self.save_json(self.economy_file, self.economy_data)
            
            embed = discord.Embed(
                title="🎰 BLACKJACK!",
                description=f"**Your Hand:** {hand_to_string(player_hand)} (21)\n**You won 💲 {winnings:,}!**",
                color=discord.Color.gold()
            )
            return await ctx.send(embed=embed)
        
        # Game embed with buttons
        embed = discord.Embed(
            title="🃏 Blackjack",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name=f"Your Hand ({player_value})",
            value=hand_to_string(player_hand),
            inline=False
        )
        
        embed.add_field(
            name="Dealer's Hand (?)",
            value=f"[{dealer_hand[0][0]}{dealer_hand[0][1]}] [??]",
            inline=False
        )
        
        embed.set_footer(text="React: ✅ Hit | ❌ Stand")
        
        message = await ctx.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == message.id
        
        while player_value < 21:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                
                if str(reaction.emoji) == '✅':
                    # Hit
                    player_hand.append(draw_card())
                    player_value = calculate_hand(player_hand)
                    
                    embed.set_field_at(0, name=f"Your Hand ({player_value})", value=hand_to_string(player_hand), inline=False)
                    await message.edit(embed=embed)
                    
                    try:
                        await message.remove_reaction(reaction, user)
                    except:
                        pass
                    
                else:
                    # Stand
                    break
                    
            except asyncio.TimeoutError:
                await ctx.send("```\n⏰ Game timed out!\n```")
                self.save_json(self.economy_file, self.economy_data)
                return
        
        # Dealer's turn
        dealer_value = calculate_hand(dealer_hand)
        
        while dealer_value < 17:
            dealer_hand.append(draw_card())
            dealer_value = calculate_hand(dealer_hand)
        
        # Determine winner
        result_embed = discord.Embed(title="🃏 Blackjack - Result", color=discord.Color.blue())
        
        result_embed.add_field(
            name=f"Your Hand ({player_value})",
            value=hand_to_string(player_hand),
            inline=False
        )
        
        result_embed.add_field(
            name=f"Dealer's Hand ({dealer_value})",
            value=hand_to_string(dealer_hand),
            inline=False
        )
        
        if player_value > 21:
            result = "Bust! You lose."
            result_embed.color = discord.Color.red()
        elif dealer_value > 21:
            result = "Dealer busts! You win!"
            winnings = amount * 2
            data['wallet'] += winnings
            result_embed.color = discord.Color.green()
        elif player_value > dealer_value:
            result = "You win!"
            winnings = amount * 2
            data['wallet'] += winnings
            result_embed.color = discord.Color.green()
        elif player_value < dealer_value:
            result = "Dealer wins. You lose."
            result_embed.color = discord.Color.red()
        else:
            result = "Push! Bet returned."
            data['wallet'] += amount
            result_embed.color = discord.Color.gold()
        
        result_embed.add_field(name="Result", value=f"**{result}**", inline=False)
        result_embed.add_field(name="Balance", value=f"💲 {data['wallet']:,}", inline=False)
        
        self.save_json(self.economy_file, self.economy_data)
        
        await message.edit(embed=result_embed)
    
    @commands.command(name='leaderboard', aliases=['lb', 'rich', 'top'])
    async def leaderboard(self, ctx):
        """View richest users"""
        sorted_users = sorted(
            self.economy_data.items(),
            key=lambda x: x[1].get('wallet', 0) + x[1].get('bank', 0),
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title="🏆 Leaderboard - Richest Users",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        description = ""
        
        medals = ['🥇', '🥈', '🥉']
        
        for i, (user_id, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(int(user_id))
            name = user.name if user else f"Unknown ({user_id})"
            total = data.get('wallet', 0) + data.get('bank', 0)
            
            medal = medals[i-1] if i <= 3 else f"#{i}"
            description += f"{medal} **{name}** - 💲 {total:,}\n"
        
        embed.description = description or "No data yet!"
        
        await ctx.send(embed=embed)
    
    @commands.command(name='networth', aliases=['nw'])
    async def networth(self, ctx, user: Optional[discord.Member] = None):
        """View total networth"""
        user = user or ctx.author
        data = self.get_user_economy(user.id)
        
        wallet = data.get('wallet', 0)
        bank = data.get('bank', 0)
        
        # Calculate inventory value
        inventory_value = 0
        for item_id in data.get('inventory', []):
            if item_id in self.shop_items:
                inventory_value += self.shop_items[item_id]['price']
        
        total = wallet + bank + inventory_value
        
        embed = discord.Embed(
            title=f"💎 {user.name}'s Net Worth",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="💵 Wallet", value=f"💲 {wallet:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"💲 {bank:,}", inline=True)
        embed.add_field(name="📦 Inventory", value=f"💲 {inventory_value:,}", inline=True)
        embed.add_field(name="💎 Total", value=f"**💲 {total:,}**", inline=False)
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='givecoins')
    @commands.has_permissions(administrator=True)
    async def give_coins(self, ctx, user: discord.Member, amount: int):
        """Admin: Give coins to user"""
        data = self.get_user_economy(user.id)
        data['wallet'] += amount
        
        self.save_json(self.economy_file, self.economy_data)
        
        await ctx.send(f"```\n✅ Gave 💲 {amount:,} to {user.name}\n```")
    
    @commands.command(name='removecoins')
    @commands.has_permissions(administrator=True)
    async def remove_coins(self, ctx, user: discord.Member, amount: int):
        """Admin: Remove coins from user"""
        data = self.get_user_economy(user.id)
        data['wallet'] = max(0, data['wallet'] - amount)
        
        self.save_json(self.economy_file, self.economy_data)
        
        await ctx.send(f"```\n✅ Removed 💲 {amount:,} from {user.name}\n```")
    
    @commands.command(name='reseteconomy')
    @commands.has_permissions(administrator=True)
    async def reset_economy(self, ctx, user: discord.Member):
        """Admin: Reset user's economy"""
        user_id = str(user.id)
        
        if user_id in self.economy_data:
            del self.economy_data[user_id]
            self.save_json(self.economy_file, self.economy_data)
        
        await ctx.send(f"```\n✅ Reset economy for {user.name}\n```")
    
    # ============================================================
    #              MODERATION COMMANDS (CONTINUED)
    # ============================================================
    
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban_user(self, ctx, user_id: int):
        """Unban a user by ID"""
        try:
            await ctx.guild.unban(discord.Object(id=user_id), reason=f"Unbanned by {ctx.author}")
            
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"User ID `{user_id}` has been unbanned.",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
        except discord.NotFound:
            await ctx.send("```\n❌ User not found in ban list!\n```")
    
    @commands.command(name='softban')
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: discord.Member, *, reason="No reason"):
        """Softban (ban + unban to clear messages)"""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("```\n❌ You can't softban this user!\n```")
        
        await member.ban(reason=f"Softban by {ctx.author} | {reason}", delete_message_days=7)
        await ctx.guild.unban(member, reason="Softban complete")
        
        embed = discord.Embed(
            title="🔨 User Softbanned",
            description=f"{member.mention} was softbanned and their messages were deleted.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='mute', aliases=['timeout'])
    @commands.has_permissions(moderate_members=True)
    async def mute_user(self, ctx, member: discord.Member, time: str, *, reason="No reason"):
        """Timeout a user"""
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("```\n❌ You can't mute this user!\n```")
        
        # Parse time
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        match = re.match(r'(\d+)([smhd])', time.lower())
        
        if not match:
            return await ctx.send("```\n❌ Invalid time! Use: 10m, 1h, 1d\n```")
        
        amount, unit = match.groups()
        seconds = int(amount) * units[unit]
        
        if seconds > 2419200:  # 28 days max
            return await ctx.send("```\n❌ Maximum timeout is 28 days!\n```")
        
        duration = timedelta(seconds=seconds)
        
        await member.timeout(duration, reason=f"Muted by {ctx.author} | {reason}")
        
        embed = discord.Embed(
            title="🔇 User Muted",
            color=discord.Color.orange()
        )
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Duration", value=time, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='unmute', aliases=['untimeout'])
    @commands.has_permissions(moderate_members=True)
    async def unmute_user(self, ctx, member: discord.Member):
        """Remove timeout from user"""
        await member.timeout(None, reason=f"Unmuted by {ctx.author}")
        
        embed = discord.Embed(
            title="🔊 User Unmuted",
            description=f"{member.mention} has been unmuted.",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn_user(self, ctx, member: discord.Member, *, reason="No reason"):
        """Warn a user"""
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        if guild_id not in self.warnings_data:
            self.warnings_data[guild_id] = {}
        
        if user_id not in self.warnings_data[guild_id]:
            self.warnings_data[guild_id][user_id] = []
        
        warning = {
            'id': len(self.warnings_data[guild_id][user_id]) + 1,
            'reason': reason,
            'moderator_id': ctx.author.id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.warnings_data[guild_id][user_id].append(warning)
        self.save_json(self.warnings_file, self.warnings_data)
        
        total_warns = len(self.warnings_data[guild_id][user_id])
        
        embed = discord.Embed(
            title="⚠️ Warning Issued",
            color=discord.Color.yellow()
        )
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Total Warnings", value=str(total_warns), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await ctx.send(embed=embed)
        
        # DM user
        try:
            dm_embed = discord.Embed(
                title=f"⚠️ Warning in {ctx.guild.name}",
                description=f"**Reason:** {reason}\n**Total Warnings:** {total_warns}",
                color=discord.Color.yellow()
            )
            await member.send(embed=dm_embed)
        except:
            pass
    
    @commands.command(name='warnings', aliases=['warns'])
    async def view_warnings(self, ctx, member: Optional[discord.Member] = None):
        """View warnings for user"""
        member = member or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        warnings = self.warnings_data.get(guild_id, {}).get(user_id, [])
        
        if not warnings:
            return await ctx.send(f"```\n✅ {member.name} has no warnings!\n```")
        
        embed = discord.Embed(
            title=f"⚠️ Warnings for {member.name}",
            description=f"Total: **{len(warnings)}** warnings",
            color=discord.Color.yellow()
        )
        
        for warn in warnings[-10:]:
            mod = self.bot.get_user(warn['moderator_id'])
            mod_name = mod.name if mod else "Unknown"
            
            embed.add_field(
                name=f"#{warn['id']} - {warn['timestamp'][:10]}",
                value=f"**Reason:** {warn['reason']}\n**By:** {mod_name}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='clearwarns', aliases=['clearwarnings'])
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: discord.Member):
        """Clear all warnings for user"""
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        if guild_id in self.warnings_data and user_id in self.warnings_data[guild_id]:
            del self.warnings_data[guild_id][user_id]
            self.save_json(self.warnings_file, self.warnings_data)
        
        await ctx.send(f"```\n✅ Cleared all warnings for {member.name}\n```")
    
    @commands.command(name='purgeuser')
    @commands.has_permissions(manage_messages=True)
    async def purge_user(self, ctx, user: discord.Member, amount: int):
        """Delete messages from specific user"""
        if amount <= 0 or amount > 100:
            return await ctx.send("```\n❌ Amount must be 1-100!\n```")
        
        def check(msg):
            return msg.author == user
        
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(f"```\n✅ Deleted {len(deleted)} messages from {user.name}\n```", delete_after=5)
    
    @commands.command(name='purgebots')
    @commands.has_permissions(manage_messages=True)
    async def purge_bots(self, ctx, amount: int):
        """Delete bot messages"""
        if amount <= 0 or amount > 100:
            return await ctx.send("```\n❌ Amount must be 1-100!\n```")
        
        def check(msg):
            return msg.author.bot
        
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(f"```\n✅ Deleted {len(deleted)} bot messages\n```", delete_after=5)
    
    @commands.command(name='purgelinks')
    @commands.has_permissions(manage_messages=True)
    async def purge_links(self, ctx, amount: int):
        """Delete messages with links"""
        if amount <= 0 or amount > 100:
            return await ctx.send("```\n❌ Amount must be 1-100!\n```")
        
        url_pattern = re.compile(r'https?://\S+')
        
        def check(msg):
            return url_pattern.search(msg.content)
        
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(f"```\n✅ Deleted {len(deleted)} messages with links\n```", delete_after=5)
    
    @commands.command(name='purgeimages')
    @commands.has_permissions(manage_messages=True)
    async def purge_images(self, ctx, amount: int):
        """Delete messages with attachments"""
        if amount <= 0 or amount > 100:
            return await ctx.send("```\n❌ Amount must be 1-100!\n```")
        
        def check(msg):
            return len(msg.attachments) > 0
        
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(f"```\n✅ Deleted {len(deleted)} messages with images\n```", delete_after=5)
    
    @commands.command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 0):
        """Set channel slowmode"""
        if seconds < 0 or seconds > 21600:
            return await ctx.send("```\n❌ Slowmode must be 0-21600 seconds!\n```")
        
        await ctx.channel.edit(slowmode_delay=seconds)
        
        if seconds == 0:
            await ctx.send("```\n✅ Slowmode disabled\n```")
        else:
            await ctx.send(f"```\n✅ Slowmode set to {seconds} seconds\n```")
    
    @commands.command(name='lock')
    @commands.has_permissions(manage_channels=True)
    async def lock_channel(self, ctx):
        """Lock current channel"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        
        embed = discord.Embed(
            title="🔒 Channel Locked",
            description="This channel has been locked by a moderator.",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx):
        """Unlock current channel"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        
        embed = discord.Embed(
            title="🔓 Channel Unlocked",
            description="This channel has been unlocked.",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='lockdown')
    @commands.has_permissions(administrator=True)
    async def lockdown(self, ctx):
        """Lock all channels"""
        locked = 0
        
        for channel in ctx.guild.text_channels:
            try:
                await channel.set_permissions(ctx.guild.default_role, send_messages=False)
                locked += 1
            except:
                pass
        
        embed = discord.Embed(
            title="🚨 LOCKDOWN ACTIVATED",
            description=f"Locked {locked} channels.",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='nuke')
    @commands.has_permissions(administrator=True)
    async def nuke_channel(self, ctx):
        """Clone and delete channel"""
        confirm_msg = await ctx.send("```\n⚠️ This will delete and recreate this channel!\nReact ✅ to confirm or ❌ to cancel.\n```")
        
        await confirm_msg.add_reaction('✅')
        await confirm_msg.add_reaction('❌')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '✅':
                new_channel = await ctx.channel.clone(reason=f"Nuked by {ctx.author}")
                await ctx.channel.delete()
                
                await new_channel.send(
                    "```\n"
                    "💥 CHANNEL NUKED\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Nuked by: {ctx.author.name}\n"
                    "All messages have been cleared.\n"
                    "```"
                )
            else:
                await ctx.send("```\n❌ Nuke cancelled.\n```")
                
        except asyncio.TimeoutError:
            await ctx.send("```\n⏰ Confirmation timed out.\n```")
    
    @commands.command(name='modlogs')
    @commands.has_permissions(manage_messages=True)
    async def mod_logs(self, ctx, member: discord.Member):
        """View moderation history"""
        guild_id = str(ctx.guild.id)
        user_id = member.id
        
        cases = self.mod_cases.get(guild_id, [])
        user_cases = [c for c in cases if c.get('user_id') == user_id]
        
        if not user_cases:
            return await ctx.send(f"```\n✅ No moderation history for {member.name}\n```")
        
        embed = discord.Embed(
            title=f"📋 Mod Logs for {member.name}",
            description=f"Total cases: **{len(user_cases)}**",
            color=discord.Color.blue()
        )
        
        for case in user_cases[-10:]:
            mod = self.bot.get_user(case.get('moderator_id'))
            mod_name = mod.name if mod else "Unknown"
            
            embed.add_field(
                name=f"Case #{case['case_id']} - {case['type'].upper()}",
                value=f"**Reason:** {case['reason']}\n**By:** {mod_name}\n**Date:** {case['timestamp'][:10]}",
                inline=False
            )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='case')
    @commands.has_permissions(manage_messages=True)
    async def view_case(self, ctx, case_id: int):
        """View specific mod case"""
        guild_id = str(ctx.guild.id)
        cases = self.mod_cases.get(guild_id, [])
        
        case = next((c for c in cases if c.get('case_id') == case_id), None)
        
        if not case:
            return await ctx.send("```\n❌ Case not found!\n```")
        
        user = self.bot.get_user(case.get('user_id'))
        mod = self.bot.get_user(case.get('moderator_id'))
        
        embed = discord.Embed(
            title=f"📋 Case #{case_id}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Type", value=case['type'].upper(), inline=True)
        embed.add_field(name="User", value=user.mention if user else f"ID: {case['user_id']}", inline=True)
        embed.add_field(name="Moderator", value=mod.mention if mod else "Unknown", inline=True)
        embed.add_field(name="Reason", value=case['reason'], inline=False)
        embed.add_field(name="Date", value=case['timestamp'][:19], inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='editcase')
    @commands.has_permissions(manage_messages=True)
    async def edit_case(self, ctx, case_id: int, *, new_reason: str):
        """Edit case reason"""
        guild_id = str(ctx.guild.id)
        cases = self.mod_cases.get(guild_id, [])
        
        for case in cases:
            if case.get('case_id') == case_id:
                case['reason'] = new_reason
                self.save_json(self.mod_cases_file, self.mod_cases)
                
                return await ctx.send(f"```\n✅ Case #{case_id} reason updated.\n```")
        
        await ctx.send("```\n❌ Case not found!\n```")
    
    # ============================================================
    #              FUN COMMANDS
    # ============================================================
    
    @commands.command(name='rps')
    async def rock_paper_scissors(self, ctx, choice: str):
        """Rock Paper Scissors"""
        choices = ['rock', 'paper', 'scissors']
        choice = choice.lower()
        
        if choice not in choices:
            return await ctx.send("```\n❌ Choose rock, paper, or scissors!\n```")
        
        bot_choice = random.choice(choices)
        
        emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
        
        if choice == bot_choice:
            result = "It's a tie!"
            color = discord.Color.gold()
        elif (choice == 'rock' and bot_choice == 'scissors') or \
             (choice == 'paper' and bot_choice == 'rock') or \
             (choice == 'scissors' and bot_choice == 'paper'):
            result = "You win!"
            color = discord.Color.green()
        else:
            result = "You lose!"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="✊ Rock Paper Scissors",
            color=color
        )
        
        embed.add_field(name="Your Choice", value=f"{emojis[choice]} {choice.title()}", inline=True)
        embed.add_field(name="Bot's Choice", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
        embed.add_field(name="Result", value=f"**{result}**", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='fight')
    async def fight_user(self, ctx, user: discord.Member):
        """Fight another user"""
        if user.id == ctx.author.id:
            return await ctx.send("```\n❌ You can't fight yourself!\n```")
        
        fighter1 = ctx.author
        fighter2 = user
        
        hp1 = 100
        hp2 = 100
        
        attacks = [
            ("punched", 10, 25),
            ("kicked", 15, 30),
            ("slapped", 5, 15),
            ("headbutted", 20, 35),
            ("dropkicked", 25, 40),
            ("uppercut", 18, 32),
        ]
        
        log = []
        
        while hp1 > 0 and hp2 > 0:
            # Fighter 1 attacks
            attack, min_dmg, max_dmg = random.choice(attacks)
            damage = random.randint(min_dmg, max_dmg)
            hp2 -= damage
            log.append(f"⚔️ {fighter1.name} {attack} {fighter2.name} for {damage} damage!")
            
            if hp2 <= 0:
                break
            
            # Fighter 2 attacks
            attack, min_dmg, max_dmg = random.choice(attacks)
            damage = random.randint(min_dmg, max_dmg)
            hp1 -= damage
            log.append(f"⚔️ {fighter2.name} {attack} {fighter1.name} for {damage} damage!")
        
        winner = fighter1 if hp2 <= 0 else fighter2
        loser = fighter2 if hp2 <= 0 else fighter1
        
        embed = discord.Embed(
            title="⚔️ FIGHT!",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="Battle Log",
            value="```\n" + "\n".join(log[-5:]) + "\n```",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Winner",
            value=f"**{winner.name}** wins!",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='roast')
    async def roast_user(self, ctx, user: Optional[discord.Member] = None):
        """Roast someone"""
        user = user or ctx.author
        
        roasts = [
            f"{user.name} is the reason we have warning labels on everything.",
            f"I'd explain it to {user.name}, but I don't have crayons.",
            f"{user.name} isn't playing with a full deck of cards.",
            f"If {user.name} was any more inbred, they'd be a sandwich.",
            f"{user.name} has the personality of a wet mop.",
            f"I've seen smarter rocks than {user.name}.",
            f"{user.name}'s family tree must be a cactus, because everyone on it is a prick.",
            f"If brains were dynamite, {user.name} wouldn't have enough to blow their nose.",
            f"{user.name} is proof that evolution can go in reverse.",
            f"The best part of {user.name} ran down their mother's leg.",
        ]
        
        roast = random.choice(roasts)
        
        embed = discord.Embed(
            title="🔥 ROASTED",
            description=roast,
            color=discord.Color.red()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='compliment')
    async def compliment_user(self, ctx, user: Optional[discord.Member] = None):
        """Compliment someone"""
        user = user or ctx.author
        
        compliments = [
            f"{user.name}, you're more beautiful than a sunset!",
            f"{user.name} is the reason unicorns believe in humans.",
            f"If {user.name} was a vegetable, they'd be a cute-cumber!",
            f"{user.name} has a smile that lights up the room.",
            f"The world is better because {user.name} is in it.",
            f"{user.name} is like a ray of sunshine on a cloudy day.",
            f"Someone as amazing as {user.name} deserves all the good things!",
            f"{user.name}, you're stronger than you know!",
            f"{user.name} is proof that good people still exist.",
            f"Being around {user.name} is always a pleasure!",
        ]
        
        compliment = random.choice(compliments)
        
        embed = discord.Embed(
            title="💖 Compliment",
            description=compliment,
            color=discord.Color.pink()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='hug')
    async def hug_user(self, ctx, user: discord.Member):
        """Hug someone"""
        if user.id == ctx.author.id:
            description = f"{ctx.author.mention} hugs themselves... 🥺"
        else:
            description = f"{ctx.author.mention} hugs {user.mention}! 🤗"
        
        embed = discord.Embed(
            title="🤗 Hug!",
            description=description,
            color=discord.Color.pink()
        )
        
        # Random hug GIF
        gifs = [
            "https://media.tenor.com/3XdRCwytmg4AAAAC/hug.gif",
            "https://media.tenor.com/KmvdYEoP3-AAAAAC/hugs.gif",
        ]
        
        await ctx.send(embed=embed)
    
    @commands.command(name='slap')
    async def slap_user(self, ctx, user: discord.Member):
        """Slap someone"""
        if user.id == ctx.author.id:
            description = f"{ctx.author.mention} slaps themselves... why? 😕"
        else:
            description = f"{ctx.author.mention} slaps {user.mention}! 👋"
        
        embed = discord.Embed(
            title="👋 Slap!",
            description=description,
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='kiss')
    async def kiss_user(self, ctx, user: discord.Member):
        """Kiss someone"""
        if user.id == ctx.author.id:
            description = f"{ctx.author.mention} kisses the mirror... 💋"
        else:
            description = f"{ctx.author.mention} kisses {user.mention}! 💋"
        
        embed = discord.Embed(
            title="💋 Kiss!",
            description=description,
            color=discord.Color.pink()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='kill')
    async def kill_user(self, ctx, user: discord.Member):
        """Funny kill message"""
        kills = [
            f"💀 {ctx.author.name} yeeted {user.name} into the sun.",
            f"💀 {ctx.author.name} pushed {user.name} off a cliff.",
            f"💀 {ctx.author.name} sent {user.name} to the shadow realm.",
            f"💀 {ctx.author.name} deleted {user.name} from existence.",
            f"💀 {ctx.author.name} turned {user.name} into a fine mist.",
            f"💀 {ctx.author.name} used /kill on {user.name}. It was super effective!",
        ]
        
        embed = discord.Embed(
            title="💀 Fatality",
            description=random.choice(kills),
            color=discord.Color.dark_red()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rate')
    async def rate_thing(self, ctx, *, thing: str):
        """Rate anything"""
        rating = random.randint(0, 10)
        
        if rating <= 3:
            emoji = "😬"
        elif rating <= 6:
            emoji = "😐"
        elif rating <= 8:
            emoji = "😊"
        else:
            emoji = "🔥"
        
        embed = discord.Embed(
            title="⭐ Rating",
            description=f"I rate **{thing}** a **{rating}/10** {emoji}",
            color=discord.Color.gold()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ship')
    async def ship_users(self, ctx, user1: discord.Member, user2: Optional[discord.Member] = None):
        """Ship two users"""
        user2 = user2 or ctx.author
        
        # Generate consistent ship percentage
        seed = min(user1.id, user2.id) + max(user1.id, user2.id)
        random.seed(seed)
        percentage = random.randint(0, 100)
        random.seed()
        
        # Ship name
        name1 = user1.name[:len(user1.name)//2]
        name2 = user2.name[len(user2.name)//2:]
        ship_name = name1 + name2
        
        # Progress bar
        filled = int(percentage / 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        if percentage >= 80:
            status = "💕 Soulmates!"
            color = discord.Color.pink()
        elif percentage >= 60:
            status = "❤️ Great match!"
            color = discord.Color.red()
        elif percentage >= 40:
            status = "💛 Potential!"
            color = discord.Color.gold()
        elif percentage >= 20:
            status = "💔 Maybe not..."
            color = discord.Color.orange()
        else:
            status = "💀 Terrible match!"
            color = discord.Color.dark_gray()
        
        embed = discord.Embed(
            title="💘 Love Calculator",
            color=color
        )
        
        embed.add_field(
            name="Ship Name",
            value=f"**{ship_name}**",
            inline=False
        )
        
        embed.add_field(
            name="Compatibility",
            value=f"```\n[{bar}] {percentage}%\n```",
            inline=False
        )
        
        embed.add_field(name="Status", value=status, inline=False)
        
        embed.set_footer(text=f"{user1.name} 💕 {user2.name}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='iq')
    async def fake_iq(self, ctx, user: Optional[discord.Member] = None):
        """Fake IQ test"""
        user = user or ctx.author
        
        iq = random.randint(1, 200)
        
        if iq < 70:
            comment = "Smooth brain detected 🧠"
        elif iq < 100:
            comment = "Below average... yikes"
        elif iq < 120:
            comment = "Average intelligence"
        elif iq < 150:
            comment = "Above average! Smart!"
        else:
            comment = "GENIUS! Big brain energy! 🧠"
        
        embed = discord.Embed(
            title="🧠 IQ Test",
            description=f"{user.mention}'s IQ is **{iq}**\n\n*{comment}*",
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='pp')
    async def pp_size(self, ctx, user: Optional[discord.Member] = None):
        """Funny PP size generator"""
        user = user or ctx.author
        
        size = random.randint(1, 15)
        pp = "8" + "=" * size + "D"
        
        embed = discord.Embed(
            title="📏 PP Size Machine",
            description=f"{user.mention}'s PP:\n```\n{pp}\n```",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='gayrate')
    async def gay_rate(self, ctx, user: Optional[discord.Member] = None):
        """Gay percentage (joke)"""
        user = user or ctx.author
        
        percentage = random.randint(0, 100)
        
        embed = discord.Embed(
            title="🏳️‍🌈 Gay Rate",
            description=f"{user.mention} is **{percentage}%** gay! 🏳️‍🌈",
            color=discord.Color.from_rgb(255, 0, 255)
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='simprate')
    async def simp_rate(self, ctx, user: Optional[discord.Member] = None):
        """Simp percentage"""
        user = user or ctx.author
        
        percentage = random.randint(0, 100)
        
        if percentage >= 80:
            status = "MEGA SIMP! 🤡"
        elif percentage >= 50:
            status = "Certified simp 😏"
        elif percentage >= 25:
            status = "Minor simping detected"
        else:
            status = "Not a simp! ✅"
        
        embed = discord.Embed(
            title="💖 Simp Rate",
            description=f"{user.mention} is **{percentage}%** simp!\n\n*{status}*",
            color=discord.Color.pink()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='hack')
    async def fake_hack(self, ctx, user: discord.Member):
        """Fake hack simulation"""
        embed = discord.Embed(
            title="💻 Hacking in progress...",
            color=discord.Color.dark_green()
        )
        
        message = await ctx.send(embed=embed)
        
        steps = [
            "Connecting to target...",
            "Bypassing firewall...",
            "Accessing mainframe...",
            "Downloading data...",
            "Retrieving passwords...",
            "Hacking complete!"
        ]
        
        for step in steps:
            embed.description = f"```\n{step}\n```"
            await message.edit(embed=embed)
            await asyncio.sleep(1)
        
        # Final result
        fake_email = f"{user.name.lower()}@gmail.com"
        fake_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        fake_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        final_embed = discord.Embed(
            title=f"💻 Hacked {user.name}!",
            color=discord.Color.green()
        )
        
        final_embed.add_field(
            name="Retrieved Data",
            value=f"```yaml\n"
                  f"Email: {fake_email}\n"
                  f"Password: {fake_password}\n"
                  f"IP: {fake_ip}\n"
                  f"Last Location: Mom's Basement\n"
                  f"Browser History: 99% Embarrassing\n"
                  f"```",
            inline=False
        )
        
        final_embed.set_footer(text="Just kidding! This is fake 😂")
        
        await message.edit(embed=final_embed)
    
    @commands.command(name='meme')
    async def random_meme(self, ctx):
        """Get random meme from Reddit"""
        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://meme-api.com/gimme') as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            embed = discord.Embed(
                                title=data.get('title', 'Meme'),
                                color=discord.Color.blue()
                            )
                            
                            embed.set_image(url=data.get('url'))
                            embed.set_footer(text=f"👍 {data.get('ups', 0)} | r/{data.get('subreddit', 'memes')}")
                            
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send("```\n❌ Failed to fetch meme!\n```")
            except:
                await ctx.send("```\n❌ Failed to fetch meme!\n```")
    
    @commands.command(name='joke')
    async def random_joke(self, ctx):
        """Get random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "I'm reading a book about anti-gravity. It's impossible to put down!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems.",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why don't programmers like nature? It has too many bugs.",
            "What do you call a dog that does magic? A Labracadabrador!",
        ]
        
        joke = random.choice(jokes)
        
        embed = discord.Embed(
            title="😂 Random Joke",
            description=joke,
            color=discord.Color.gold()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='fact')
    async def random_fact(self, ctx):
        """Get random fact"""
        facts = [
            "Honey never spoils. Archaeologists have found 3000-year-old honey that was still edible.",
            "Octopuses have three hearts and blue blood.",
            "A day on Venus is longer than a year on Venus.",
            "Bananas are berries, but strawberries aren't.",
            "The shortest war in history lasted 38-45 minutes.",
            "A group of flamingos is called a 'flamboyance'.",
            "Cows have best friends and get stressed when separated.",
            "Sharks existed before trees.",
            "The inventor of Pringles is buried in a Pringles can.",
            "A jiffy is an actual unit of time: 1/100th of a second.",
        ]
        
        fact = random.choice(facts)
        
        embed = discord.Embed(
            title="🧠 Random Fact",
            description=fact,
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='quote')
    async def random_quote(self, ctx):
        """Get inspirational quote"""
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
            ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
            ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
            ("The only impossible journey is the one you never begin.", "Tony Robbins"),
            ("Life is what happens when you're busy making other plans.", "John Lennon"),
        ]
        
        quote, author = random.choice(quotes)
        
        embed = discord.Embed(
            title="💭 Inspirational Quote",
            description=f'*"{quote}"*\n\n— **{author}**',
            color=discord.Color.purple()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='wouldyourather', aliases=['wyr'])
    async def would_you_rather(self, ctx):
        """Would you rather game"""
        scenarios = [
            ("be able to fly", "be invisible"),
            ("have unlimited money", "unlimited knowledge"),
            ("live without music", "live without TV"),
            ("be famous", "be rich"),
            ("have super strength", "super speed"),
            ("read minds", "see the future"),
            ("live in the past", "live in the future"),
            ("be alone for a year", "never be alone for a year"),
        ]
        
        option1, option2 = random.choice(scenarios)
        
        embed = discord.Embed(
            title="🤔 Would You Rather...",
            description=f"**A:** {option1}\n\n**OR**\n\n**B:** {option2}",
            color=discord.Color.purple()
        )
        
        embed.set_footer(text="React with 🅰️ or 🅱️")
        
        message = await ctx.send(embed=embed)
        await message.add_reaction('🅰️')
        await message.add_reaction('🅱️')
    
    @commands.command(name='truth')
    async def truth_question(self, ctx):
        """Get truth question"""
        truths = [
            "What's your biggest fear?",
            "What's the most embarrassing thing you've done?",
            "What's a secret you've never told anyone?",
            "What's your biggest regret?",
            "Have you ever lied to your best friend?",
            "What's the worst thing you've ever done?",
            "Who was your first crush?",
            "What's the craziest dream you've had?",
            "What's the most childish thing you still do?",
            "Have you ever cheated on a test?",
        ]
        
        truth = random.choice(truths)
        
        embed = discord.Embed(
            title="🎯 Truth",
            description=truth,
            color=discord.Color.blue()
        )
        
        embed.set_footer(text="Answer honestly!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='dare')
    async def dare_challenge(self, ctx):
        """Get dare challenge"""
        dares = [
            "Send the last photo you took to this channel",
            "Let someone post something on your status",
            "Do 10 push-ups right now",
            "Talk in an accent for the next 10 minutes",
            "Send your search history screenshot",
            "Change your nickname to something funny for an hour",
            "Send a voice message singing a song",
            "Compliment everyone in the chat",
            "Tell a joke and make someone laugh",
            "Share your most played song",
        ]
        
        dare = random.choice(dares)
        
        embed = discord.Embed(
            title="😈 Dare",
            description=dare,
            color=discord.Color.red()
        )
        
        embed.set_footer(text="You must complete the dare!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='neverhaveiever', aliases=['nhie'])
    async def never_have_i_ever(self, ctx):
        """Never have I ever game"""
        statements = [
            "Never have I ever lied about my age",
            "Never have I ever been on TV",
            "Never have I ever broken a bone",
            "Never have I ever been to a concert",
            "Never have I ever pulled an all-nighter",
            "Never have I ever been in a car accident",
            "Never have I ever met a celebrity",
            "Never have I ever gone skinny dipping",
            "Never have I ever failed a class",
            "Never have I ever been outside my country",
        ]
        
        statement = random.choice(statements)
        
        embed = discord.Embed(
            title="🙊 Never Have I Ever",
            description=statement,
            color=discord.Color.orange()
        )
        
        embed.set_footer(text="React 👍 if you have, 👎 if you haven't")
        
        message = await ctx.send(embed=embed)
        await message.add_reaction('👍')
        await message.add_reaction('👎')
    
    @commands.command(name='thisorthat', aliases=['tot'])
    async def this_or_that(self, ctx):
        """This or that game"""
        choices = [
            ("Dogs", "Cats"),
            ("Summer", "Winter"),
            ("Morning", "Night"),
            ("Beach", "Mountains"),
            ("Coffee", "Tea"),
            ("Movies", "TV Shows"),
            ("Books", "Video Games"),
            ("Pizza", "Burger"),
            ("Apple", "Android"),
            ("Rain", "Snow"),
        ]
        
        option1, option2 = random.choice(choices)
        
        embed = discord.Embed(
            title="🔀 This or That?",
            description=f"**🅰️** {option1}\n\n**VS**\n\n**🅱️** {option2}",
            color=discord.Color.teal()
        )
        
        message = await ctx.send(embed=embed)
        await message.add_reaction('🅰️')
        await message.add_reaction('🅱️')
    
    @commands.command(name='trivia')
    async def trivia_question(self, ctx):
        """Trivia question"""
        questions = [
            {"question": "What is the capital of France?", "answer": "Paris"},
            {"question": "How many planets are in our solar system?", "answer": "8"},
            {"question": "What year did World War II end?", "answer": "1945"},
            {"question": "Who painted the Mona Lisa?", "answer": "Leonardo da Vinci"},
            {"question": "What is the largest ocean?", "answer": "Pacific"},
            {"question": "How many legs does a spider have?", "answer": "8"},
            {"question": "What is the chemical symbol for gold?", "answer": "Au"},
            {"question": "Who wrote Romeo and Juliet?", "answer": "Shakespeare"},
        ]
        
        q = random.choice(questions)
        
        embed = discord.Embed(
            title="🧩 Trivia Time!",
            description=q['question'],
            color=discord.Color.gold()
        )
        
        embed.set_footer(text="You have 30 seconds to answer!")
        
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            message = await self.bot.wait_for('message', timeout=30.0, check=check)
            
            if message.content.lower() == q['answer'].lower():
                await ctx.send("```\n✅ Correct! Well done!\n```")
            else:
                await ctx.send(f"```\n❌ Wrong! The answer was: {q['answer']}\n```")
                
        except asyncio.TimeoutError:
            await ctx.send(f"```\n⏰ Time's up! The answer was: {q['answer']}\n```")
    
    @commands.command(name='riddle')
    async def random_riddle(self, ctx):
        """Random riddle"""
        riddles = [
            {"riddle": "What has keys but no locks?", "answer": "A piano"},
            {"riddle": "What has hands but can't clap?", "answer": "A clock"},
            {"riddle": "What can you catch but not throw?", "answer": "A cold"},
            {"riddle": "What has a head and a tail but no body?", "answer": "A coin"},
            {"riddle": "What gets wetter the more it dries?", "answer": "A towel"},
            {"riddle": "What can travel around the world while staying in a corner?", "answer": "A stamp"},
        ]
        
        r = random.choice(riddles)
        
        embed = discord.Embed(
            title="🧩 Riddle Me This!",
            description=r['riddle'],
            color=discord.Color.purple()
        )
        
        embed.set_footer(text="React 🔍 to reveal the answer")
        
        message = await ctx.send(embed=embed)
        await message.add_reaction('🔍')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '🔍'
        
        try:
            await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            
            answer_embed = discord.Embed(
                title="🧩 Answer",
                description=f"**{r['answer']}**",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=answer_embed)
            
        except asyncio.TimeoutError:
            pass


async def setup(bot):
    await bot.add_cog(AdvancedCommandsPart2(bot))
