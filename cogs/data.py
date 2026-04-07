import discord
from discord.ext import commands
import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
import json


class DatabaseLookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_lookups = {}  # Track active lookup sessions
        self.lookup_history_file = "lookup_history.json"
    
    def save_lookup_history(self, user_id, cnic, timestamp, result_count):
        """Save lookup history to JSON file"""
        try:
            with open(self.lookup_history_file, 'r') as f:
                history = json.load(f)
        except FileNotFoundError:
            history = {"lookups": []}
        
        history["lookups"].append({
            "user_id": user_id,
            "cnic": cnic,
            "timestamp": timestamp,
            "result_count": result_count
        })
        
        with open(self.lookup_history_file, 'w') as f:
            json.dump(history, f, indent=4)
    
    def validate_cnic(self, cnic):
        """Validate CNIC format (13 digits)"""
        # Remove any spaces, dashes, or special characters
        clean_cnic = re.sub(r'[^0-9]', '', cnic)
        
        # Check if it's exactly 13 digits
        if len(clean_cnic) == 13 and clean_cnic.isdigit():
            return clean_cnic
        return None
    
    async def fetch_data_from_website(self, cnic):
        """Fetch data from the Pakistan database website"""
        url = "https://pakistandatabase.com/databases/sim.php"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://pakistandatabase.com/databases/sim.php'
        }
        
        payload = {
            'cnic': cnic,
            'submit': 'Search'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self.parse_results(html)
                    else:
                        return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def parse_results(self, html):
        """Parse HTML response and extract SIM data"""
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        
        # Find the results table (adjust selectors based on actual website structure)
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                
                if len(cols) >= 3:  # Ensure we have enough columns
                    result = {
                        'name': cols[0].get_text(strip=True) if len(cols) > 0 else 'N/A',
                        'cnic': cols[1].get_text(strip=True) if len(cols) > 1 else 'N/A',
                        'mobile': cols[2].get_text(strip=True) if len(cols) > 2 else 'N/A',
                        'address': cols[3].get_text(strip=True) if len(cols) > 3 else 'N/A',
                    }
                    results.append(result)
        
        return results if results else None
    
    @commands.command(name='lookup', aliases=['cnic', 'sim'])
    async def lookup_cnic(self, ctx):
        """
        Lookup CNIC/SIM data from Pakistan Database
        Usage: !lookup
        """
        
        # Check if user already has an active lookup session
        if ctx.author.id in self.active_lookups:
            await ctx.send(
                "```\n"
                "❌ You already have an active lookup session!\n"
                "Please complete or cancel it first.\n"
                "```"
            )
            return
        
        # Initial prompt embed
        initial_embed = discord.Embed(
            title="🔍 CNIC/SIM Database Lookup",
            description=(
                "```\n"
                "╔══════���════════════════════════════════════════════════╗\n"
                "║                                                       ║\n"
                "║         PAKISTAN DATABASE LOOKUP SYSTEM               ║\n"
                "║                                                       ║\n"
                "╚═══════════════════════════════════════════════════════╝\n"
                "```\n"
                "**📱 Enter CNIC Number to Search**\n\n"
                "Please enter the 13-digit CNIC number.\n"
                "Format: `XXXXX-XXXXXXX-X` or `XXXXXXXXXXXXX`\n\n"
                "**Example:**\n"
                "`42201-1234567-8` or `4220112345678`\n\n"
                "⏱️ **You have 60 seconds to respond**\n"
                "Type `cancel` to abort the lookup."
            ),
            color=0x00D9FF,
            timestamp=discord.utils.utcnow()
        )
        
        initial_embed.add_field(
            name="⚠️ DISCLAIMER",
            value=(
                "```diff\n"
                "- This tool is for educational purposes only\n"
                "+ Use responsibly and legally\n"
                "+ Respect privacy and data protection laws\n"
                "```"
            ),
            inline=False
        )
        
        initial_embed.set_footer(
            text="ZeroDay Tool • Database Lookup",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        )
        
        initial_embed.set_thumbnail(url="https://flagcdn.com/w320/pk.png")
        
        await ctx.send(embed=initial_embed)
        
        # Mark session as active
        self.active_lookups[ctx.author.id] = True
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            # Wait for user input
            message = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            # Check if user wants to cancel
            if message.content.lower() == 'cancel':
                del self.active_lookups[ctx.author.id]
                await ctx.send(
                    "```\n"
                    "❌ Lookup cancelled.\n"
                    "```"
                )
                return
            
            # Validate CNIC
            cnic = self.validate_cnic(message.content)
            
            if not cnic:
                del self.active_lookups[ctx.author.id]
                error_embed = discord.Embed(
                    title="❌ Invalid CNIC Format",
                    description=(
                        "```\n"
                        "ERROR: Invalid CNIC number format!\n\n"
                        "CNIC must be exactly 13 digits.\n\n"
                        "Valid formats:\n"
                        "• 42201-1234567-8\n"
                        "• 4220112345678\n"
                        "```"
                    ),
                    color=0xFF0000
                )
                await ctx.send(embed=error_embed)
                return
            
            # Show searching message
            searching_embed = discord.Embed(
                title="🔍 Searching Database...",
                description=(
                    "```\n"
                    "╔═══════════════════════════════════════════════════════╗\n"
                    "║                                                       ║\n"
                    "║              LOOKUP IN PROGRESS                       ║\n"
                    "║                                                       ║\n"
                    "╠═══════════════════════════════════════════════════════╣\n"
                    f"║   CNIC     : {cnic[:5]}-{cnic[5:12]}-{cnic[12]}               ║\n"
                    "║   Status   : Querying database...                     ║\n"
                    "║   Progress : ████████░░░░░░░░  50%                    ║\n"
                    "║                                                       ║\n"
                    "╚═══════════════════════════════════════════════════════╝\n"
                    "```\n"
                    "⏳ Please wait while we search the database..."
                ),
                color=0xFFA500
            )
            
            searching_msg = await ctx.send(embed=searching_embed)
            
            # Fetch data from website
            results = await self.fetch_data_from_website(cnic)
            
            # Delete searching message
            await searching_msg.delete()
            
            # Check if results found
            if not results or len(results) == 0:
                no_results_embed = discord.Embed(
                    title="❌ No Results Found",
                    description=(
                        "```\n"
                        "╔═══════════════════════════════════════════════════════╗\n"
                        "║                                                       ║\n"
                        "║              NO RECORDS FOUND                         ║\n"
                        "║                                                       ║\n"
                        "╠═══════════════════════════════════════════════════════╣\n"
                        f"║   CNIC : {cnic[:5]}-{cnic[5:12]}-{cnic[12]}                   ║\n"
                        "║                                                       ║\n"
                        "║   No matching records found in the database.          ║\n"
                        "║   Please verify the CNIC number and try again.        ║\n"
                        "║                                                       ║\n"
                        "╚═══════════════════════════════════════════════════════╝\n"
                        "```"
                    ),
                    color=0xFF0000,
                    timestamp=discord.utils.utcnow()
                )
                
                await ctx.send(embed=no_results_embed)
                del self.active_lookups[ctx.author.id]
                return
            
            # Send results
            await self.send_results(ctx, cnic, results)
            
            # Save to history
            self.save_lookup_history(
                ctx.author.id,
                cnic,
                discord.utils.utcnow().isoformat(),
                len(results)
            )
            
            # Remove active session
            del self.active_lookups[ctx.author.id]
            
        except asyncio.TimeoutError:
            del self.active_lookups[ctx.author.id]
            
            timeout_embed = discord.Embed(
                title="⏱️ Timeout",
                description=(
                    "```\n"
                    "╔═══════════════════════════════════════════════════════╗\n"
                    "║                                                       ║\n"
                    "║              SESSION TIMEOUT                          ║\n"
                    "║                                                       ║\n"
                    "╠═══════════════════════════════════════════════════════╣\n"
                    "║                                                       ║\n"
                    "║   You took too long to respond!                       ║\n"
                    "║   Please use !lookup to start a new search.           ║\n"
                    "║                                                       ║\n"
                    "╚═══════════════════════════════════════════════════════╝\n"
                    "```"
                ),
                color=0xFF6B35
            )
            
            await ctx.send(embed=timeout_embed)
    
    async def send_results(self, ctx, cnic, results):
        """Send formatted results to user"""
        
        # Header embed
        header_embed = discord.Embed(
            title="✅ Results Found",
            description=(
                "```\n"
                "╔═══════════════════════════════════════════════════════╗\n"
                "║                                                       ║\n"
                "║           DATABASE LOOKUP SUCCESSFUL                  ║\n"
                "║                                                       ║\n"
                "╠═══════════════════════════════════════════════════════╣\n"
                f"║   CNIC         : {cnic[:5]}-{cnic[5:12]}-{cnic[12]}           ║\n"
                f"║   Records Found: {len(results):<35} ║\n"
                "║   Status       : ✅ Complete                          ║\n"
                "║                                                       ║\n"
                "╚═══════════════════════════════════════════════════════╝\n"
                "```"
            ),
            color=0x00FF00,
            timestamp=discord.utils.utcnow()
        )
        
        header_embed.set_thumbnail(url="https://flagcdn.com/w320/pk.png")
        
        await ctx.send(embed=header_embed)
        
        # Send results (max 5 per embed to avoid hitting limits)
        for i in range(0, len(results), 5):
            chunk = results[i:i+5]
            
            result_embed = discord.Embed(
                title=f"📋 Records {i+1}-{min(i+5, len(results))} of {len(results)}",
                description="",
                color=0x00D9FF
            )
            
            for idx, result in enumerate(chunk, start=i+1):
                result_embed.add_field(
                    name=f"**Record #{idx}**",
                    value=(
                        f"```yaml\n"
                        f"Name    : {result.get('name', 'N/A')}\n"
                        f"CNIC    : {result.get('cnic', 'N/A')}\n"
                        f"Mobile  : {result.get('mobile', 'N/A')}\n"
                        f"Address : {result.get('address', 'N/A')[:50]}...\n"
                        f"```"
                    ),
                    inline=False
                )
            
            result_embed.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.send(embed=result_embed)
        
        # Footer embed with disclaimer
        footer_embed = discord.Embed(
            title="⚠️ Important Notice",
            description=(
                "```diff\n"
                "- This data is from public sources\n"
                "+ Use this information responsibly\n"
                "+ Respect privacy laws and regulations\n"
                "- Misuse may result in legal consequences\n"
                "```\n\n"
                "**📊 Data Source:** Pakistan Database\n"
                "**🔗 Website:** https://pakistandatabase.com\n"
                "**⏰ Retrieved:** " + discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            ),
            color=0xFF6B35
        )
        
        await ctx.send(embed=footer_embed)
    
    @commands.command(name='lookuphistory')
    @commands.has_permissions(administrator=True)
    async def lookup_history(self, ctx, user: discord.Member = None):
        """
        View lookup history for a user
        Usage: !lookuphistory @user
        """
        
        try:
            with open(self.lookup_history_file, 'r') as f:
                history = json.load(f)
        except FileNotFoundError:
            await ctx.send("```\n❌ No lookup history found.\n```")
            return
        
        target_user = user if user else ctx.author
        
        user_lookups = [
            lookup for lookup in history.get('lookups', [])
            if lookup['user_id'] == target_user.id
        ]
        
        if not user_lookups:
            await ctx.send(f"```\n❌ No lookup history found for {target_user.name}.\n```")
            return
        
        history_embed = discord.Embed(
            title=f"📊 Lookup History - {target_user.name}",
            description=(
                f"```\n"
                f"╔═══════════════════════════════════════════════════════╗\n"
                f"║            LOOKUP HISTORY RECORDS                     ║\n"
                f"╠═══════════════════════════════════════════════════════╣\n"
                f"║   User       : {target_user.name:<38} ║\n"
                f"║   Total      : {len(user_lookups):<38} ║\n"
                f"╚═══════════════════════════════════════════════════════╝\n"
                f"```"
            ),
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        
        for lookup in user_lookups[-10:]:  # Show last 10
            history_embed.add_field(
                name=f"CNIC: {lookup['cnic']}",
                value=(
                    f"```\n"
                    f"Timestamp: {lookup['timestamp'][:19]}\n"
                    f"Results  : {lookup['result_count']} records\n"
                    f"```"
                ),
                inline=False
            )
        
        history_embed.set_footer(text="Showing last 10 lookups")
        
        await ctx.send(embed=history_embed)
    
    @commands.command(name='cancellookup')
    async def cancel_lookup(self, ctx):
        """Cancel active lookup session"""
        
        if ctx.author.id in self.active_lookups:
            del self.active_lookups[ctx.author.id]
            await ctx.send("```\n✅ Lookup session cancelled.\n```")
        else:
            await ctx.send("```\n❌ No active lookup session found.\n```")
    
    @lookup_cnic.error
    async def lookup_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("```\n❌ You don't have permission to use this command.\n```")
        else:
            await ctx.send(f"```\n❌ An error occurred: {str(error)}\n```")


async def setup(bot):
    await bot.add_cog(DatabaseLookup(bot))