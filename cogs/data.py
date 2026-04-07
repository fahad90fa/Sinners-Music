import discord
from discord.ext import commands
import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup


class CNICLookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://pakistandatabase.com/databases/sim.php"
    
    @commands.command(name='cniclookup')
    async def cnic_lookup(self, ctx):
        """Interactive CNIC lookup command"""
        
        prompt_embed = discord.Embed(
            title="🔍 CNIC/SIM Database Lookup",
            description=(
                "```ansi\n"
                "\u001b[1;36m╔═══════════════════════════════════════════════════════╗\n"
                "\u001b[1;36m║                                                       ║\n"
                "\u001b[1;36m║        PAKISTAN DATABASE LOOKUP SYSTEM                ║\n"
                "\u001b[1;36m║                                                       ║\n"
                "\u001b[1;36m╚═══════════════════════════════════════════════════════╝\n"
                "```\n"
                "**Please enter the 13-digit CNIC number:**\n\n"
                "📝 Format: `XXXXX-XXXXXXX-X` or `XXXXXXXXXXXXX`\n\n"
                "**Example:**\n"
                "`42201-1234567-8`\n"
                "`4220112345678`\n\n"
                "⏱️ **Timeout: 60 seconds**\n"
                "Type `cancel` to abort."
            ),
            color=0x00D9FF
        )
        
        prompt_embed.add_field(
            name="⚠️ LEGAL DISCLAIMER",
            value=(
                "```diff\n"
                "- Educational purposes only\n"
                "+ Use responsibly and legally\n"
                "+ Data from public sources\n"
                "- Respect privacy laws\n"
                "```"
            ),
            inline=False
        )
        
        await ctx.send(embed=prompt_embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            if msg.content.lower() == 'cancel':
                await ctx.send("```\n❌ Lookup cancelled.\n```")
                return
            
            # Clean and validate CNIC
            cnic = re.sub(r'[^0-9]', '', msg.content)
            
            if len(cnic) != 13:
                await ctx.send(
                    "```\n"
                    "❌ Invalid CNIC!\n"
                    "Must be exactly 13 digits.\n"
                    "```"
                )
                return
            
            # Show loading
            loading_embed = discord.Embed(
                title="🔄 Processing Request",
                description=(
                    "```\n"
                    "┌───────────────────────────────────────────┐\n"
                    "│  Status: Connecting to database...       │\n"
                    "│  CNIC  : " + f"{cnic[:5]}-{cnic[5:12]}-{cnic[12]}" + "                │\n"
                    "│  ████████████░░░░░░░░  60%                │\n"
                    "└───────────────────────────────────────────┘\n"
                    "```"
                ),
                color=0xFFA500
            )
            
            loading_msg = await ctx.send(embed=loading_embed)
            
            # Fetch data
            results = await self.scrape_data(cnic)
            
            await loading_msg.delete()
            
            if not results:
                no_result_embed = discord.Embed(
                    title="❌ No Results Found",
                    description=(
                        "```\n"
                        "╔═══════════════════════════════════════════════════════╗\n"
                        "║              NO RECORDS FOUND                         ║\n"
                        "╠═══════════════════════════════════════════════════════╣\n"
                        f"║   CNIC: {cnic[:5]}-{cnic[5:12]}-{cnic[12]}                    ║\n"
                        "║                                                       ║\n"
                        "║   No matching records in database.                    ║\n"
                        "║   Verify CNIC and try again.                          ║\n"
                        "╚═══════════════════════════════════════════════════════╝\n"
                        "```"
                    ),
                    color=0xFF0000
                )
                await ctx.send(embed=no_result_embed)
                return
            
            # Send results
            await self.display_results(ctx, cnic, results)
            
        except asyncio.TimeoutError:
            await ctx.send(
                "```\n"
                "⏱️ Timeout!\n"
                "You took too long to respond.\n"
                "Use !cniclookup to try again.\n"
                "```"
            )
    
    async def scrape_data(self, cnic):
        """Scrape data from website"""
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://pakistandatabase.com/',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'cnic': cnic,
            'submit': 'Search'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, data=data, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self.parse_html(html)
                    return None
        except Exception as e:
            print(f"Scraping error: {e}")
            return None
    
    def parse_html(self, html):
        """Parse HTML and extract data"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Look for result tables
        tables = soup.find_all('table', class_='table')  # Adjust selector as needed
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Skip header
                cells = row.find_all('td')
                
                if len(cells) >= 4:
                    results.append({
                        'name': cells[0].get_text(strip=True),
                        'cnic': cells[1].get_text(strip=True),
                        'number': cells[2].get_text(strip=True),
                        'address': cells[3].get_text(strip=True)
                    })
        
        return results if results else None
    
    async def display_results(self, ctx, cnic, results):
        """Display results in formatted embeds"""
        
        success_embed = discord.Embed(
            title="✅ Lookup Successful",
            description=(
                "```\n"
                "╔══════���════════════════════════════════════════════════╗\n"
                "║           DATABASE QUERY COMPLETE                     ║\n"
                "╠═══════════════════════════════════════════════════════╣\n"
                f"║   CNIC   : {cnic[:5]}-{cnic[5:12]}-{cnic[12]}                  ║\n"
                f"║   Results: {len(results)} record(s) found                      ║\n"
                "╚═══════════════════════════════════════════════════════╝\n"
                "```"
            ),
            color=0x00FF00
        )
        
        await ctx.send(embed=success_embed)
        
        for i, result in enumerate(results[:10], 1):  # Max 10 results
            result_embed = discord.Embed(
                title=f"📋 Record #{i}",
                color=0x00D9FF
            )
            
            result_embed.add_field(
                name="👤 Name",
                value=f"`{result.get('name', 'N/A')}`",
                inline=False
            )
            
            result_embed.add_field(
                name="🆔 CNIC",
                value=f"`{result.get('cnic', 'N/A')}`",
                inline=True
            )
            
            result_embed.add_field(
                name="📱 Mobile",
                value=f"`{result.get('number', 'N/A')}`",
                inline=True
            )
            
            result_embed.add_field(
                name="📍 Address",
                value=f"`{result.get('address', 'N/A')[:100]}...`",
                inline=False
            )
            
            result_embed.set_footer(
                text=f"Requested by {ctx.author.name}",
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.send(embed=result_embed)
        
        if len(results) > 10:
            await ctx.send(f"```\nℹ️ Showing 10 of {len(results)} results.\n```")


async def setup(bot):
    await bot.add_cog(CNICLookup(bot))