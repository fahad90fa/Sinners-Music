import discord
from discord.ext import commands
import asyncio
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time


class CNICLookupSelenium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://pakistandatabase.com/databases/sim.php"
        self.active_lookups = set()
    
    def get_driver(self):
        """Initialize Chrome driver with headless mode"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute JavaScript to hide webdriver
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def validate_cnic(self, cnic_input):
        """Validate CNIC format"""
        clean_cnic = re.sub(r'[^0-9]', '', cnic_input)
        return clean_cnic if len(clean_cnic) == 13 else None
    
    @commands.command(name='cnic', aliases=['lookup', 'sim'])
    async def cnic_lookup(self, ctx):
        """CNIC/SIM Database Lookup using Selenium"""
        
        if ctx.author.id in self.active_lookups:
            await ctx.send("```\n❌ You already have an active lookup! Please wait.\n```")
            return
        
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
                "📝 **Format:** `XXXXX-XXXXXXX-X` or `XXXXXXXXXXXXX`\n\n"
                "**Example:**\n"
                "`37405-1989162-8`\n"
                "`3740519891628`\n\n"
                "⏱️ **Timeout:** 60 seconds\n"
                "Type `cancel` to abort."
            ),
            color=0x00D9FF,
            timestamp=discord.utils.utcnow()
        )
        
        prompt_embed.add_field(
            name="⚠️ DISCLAIMER",
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
        
        prompt_embed.set_footer(text="ZeroDay Tool • Powered by Browser Automation")
        prompt_embed.set_thumbnail(url="https://flagcdn.com/w320/pk.png")
        
        await ctx.send(embed=prompt_embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            if msg.content.lower() == 'cancel':
                await ctx.send("```\n❌ Lookup cancelled.\n```")
                return
            
            cnic = self.validate_cnic(msg.content)
            
            if not cnic:
                error_embed = discord.Embed(
                    title="❌ Invalid CNIC Format",
                    description=(
                        "```\n"
                        "ERROR: CNIC must be exactly 13 digits!\n\n"
                        "Valid formats:\n"
                        "• 37405-1989162-8\n"
                        "• 3740519891628\n"
                        "```"
                    ),
                    color=0xFF0000
                )
                await ctx.send(embed=error_embed)
                return
            
            formatted_cnic = f"{cnic[:5]}-{cnic[5:12]}-{cnic[12]}"
            
            loading_embed = discord.Embed(
                title="🌐 Launching Browser Automation",
                description=(
                    "```\n"
                    "┌───────────────────────────────────────────────────┐\n"
                    "│                                                   │\n"
                    f"│  CNIC     : {formatted_cnic}                      │\n"
                    "│  Status   : Starting headless browser...         │\n"
                    "│  Progress : ████░░░░░░░░░░░░░░░░  20%            │\n"
                    "│                                                   │\n"
                    "│  This may take 15-30 seconds...                   │\n"
                    "│                                                   │\n"
                    "└───────────────────────────────────────────────────┘\n"
                    "```"
                ),
                color=0xFFA500
            )
            
            loading_msg = await ctx.send(embed=loading_embed)
            
            self.active_lookups.add(ctx.author.id)
            
            # Run selenium in executor to avoid blocking
            results = await self.bot.loop.run_in_executor(
                None, 
                self.scrape_with_selenium, 
                cnic, 
                ctx, 
                loading_msg
            )
            
            await loading_msg.delete()
            
            if not results or len(results) == 0:
                no_result_embed = discord.Embed(
                    title="❌ No Results Found",
                    description=(
                        "```\n"
                        "╔═══════════════════════════════════════════════════════╗\n"
                        "║              NO RECORDS FOUND                         ║\n"
                        "╠═══════════════════════════════════════════════════════╣\n"
                        f"║   CNIC: {formatted_cnic}                    ║\n"
                        "║                                                       ║\n"
                        "║   Possible reasons:                                   ║\n"
                        "║   • CNIC not in database                              ║\n"
                        "║   • Website structure changed                         ║\n"
                        "║   • Temporary access issues                           ║\n"
                        "║                                                       ║\n"
                        "╚═══════════════════════════════════════════════════════╝\n"
                        "```"
                    ),
                    color=0xFF0000,
                    timestamp=discord.utils.utcnow()
                )
                
                no_result_embed.add_field(
                    name="💡 Try",
                    value=(
                        "• Verify CNIC is correct\n"
                        "• Check website: https://pakistandatabase.com\n"
                        "• Try again in a few minutes"
                    ),
                    inline=False
                )
                
                await ctx.send(embed=no_result_embed)
                self.active_lookups.discard(ctx.author.id)
                return
            
            await self.display_results(ctx, formatted_cnic, results)
            self.active_lookups.discard(ctx.author.id)
            
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏱️ Session Timeout",
                description="```\n⏱️ Request timeout!\nUse !cnic to try again.\n```",
                color=0xFF6B35
            )
            await ctx.send(embed=timeout_embed)
            self.active_lookups.discard(ctx.author.id)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"```\nError: {str(e)}\n```",
                color=0xFF0000
            )
            await ctx.send(embed=error_embed)
            self.active_lookups.discard(ctx.author.id)
    
    def scrape_with_selenium(self, cnic, ctx, loading_msg):
        """Scrape data using Selenium browser automation"""
        driver = None
        
        try:
            driver = self.get_driver()
            
            # Navigate to website
            driver.get(self.base_url)
            
            # Wait for page to load
            time.sleep(2)
            
            # Update loading message (async)
            asyncio.run_coroutine_threadsafe(
                loading_msg.edit(embed=discord.Embed(
                    title="🔍 Searching Database",
                    description=(
                        "```\n"
                        "┌───────────────────────────────────────────────────┐\n"
                        "│  Status   : Page loaded, entering CNIC...        │\n"
                        "│  Progress : ████████████░░░░░░░░  60%            │\n"
                        "└───────────────────────────────────────────────────┘\n"
                        "```"
                    ),
                    color=0xFFA500
                )),
                self.bot.loop
            )
            
            # Find CNIC input field (try multiple selectors)
            cnic_input = None
            selectors = [
                "input[name='cnic']",
                "input[id='cnic']",
                "input[type='text']",
                "input[placeholder*='CNIC']",
                "input[placeholder*='cnic']"
            ]
            
            for selector in selectors:
                try:
                    cnic_input = driver.find_element(By.CSS_SELECTOR, selector)
                    if cnic_input:
                        break
                except:
                    continue
            
            if not cnic_input:
                # Try by xpath
                try:
                    cnic_input = driver.find_element(By.XPATH, "//input[@type='text']")
                except:
                    pass
            
            if not cnic_input:
                print("Could not find CNIC input field")
                return None
            
            # Clear and enter CNIC
            cnic_input.clear()
            cnic_input.send_keys(cnic)
            
            time.sleep(1)
            
            # Find and click submit button
            submit_button = None
            button_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value='Search']",
                "button:contains('Search')",
                "input[name='submit']"
            ]
            
            for selector in button_selectors:
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button:
                        break
                except:
                    continue
            
            if not submit_button:
                try:
                    submit_button = driver.find_element(By.XPATH, "//input[@type='submit']")
                except:
                    pass
            
            if submit_button:
                submit_button.click()
            else:
                # Try form submission
                cnic_input.submit()
            
            # Wait for results
            time.sleep(3)
            
            # Update loading
            asyncio.run_coroutine_threadsafe(
                loading_msg.edit(embed=discord.Embed(
                    title="📊 Extracting Data",
                    description=(
                        "```\n"
                        "┌───────────────────────────────────────────────────┐\n"
                        "│  Status   : Parsing results...                   │\n"
                        "│  Progress : ████████████████████  95%            │\n"
                        "└───────────────────────────────────────────────────┘\n"
                        "```"
                    ),
                    color=0xFFA500
                )),
                self.bot.loop
            )
            
            # Extract results from page
            results = self.extract_results(driver)
            
            return results
            
        except Exception as e:
            print(f"Selenium error: {e}")
            return None
            
        finally:
            if driver:
                driver.quit()
    
    def extract_results(self, driver):
        """Extract results from loaded page"""
        results = []
        
        try:
            # Wait for results to appear
            wait = WebDriverWait(driver, 10)
            
            # Method 1: Try to find result table
            try:
                tables = driver.find_elements(By.TAG_NAME, "table")
                
                for table in tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    
                    for row in rows[1:]:  # Skip header
                        cells = row.find_elements(By.TAG_NAME, "td")
                        
                        if len(cells) >= 3:
                            result = {
                                'name': cells[0].text.strip() if len(cells) > 0 else 'N/A',
                                'cnic': cells[1].text.strip() if len(cells) > 1 else 'N/A',
                                'number': cells[2].text.strip() if len(cells) > 2 else 'N/A',
                                'address': cells[3].text.strip() if len(cells) > 3 else 'N/A'
                            }
                            
                            if result['name'] != 'N/A' or result['number'] != 'N/A':
                                results.append(result)
            except:
                pass
            
            # Method 2: Try finding result divs
            if not results:
                try:
                    result_divs = driver.find_elements(By.CSS_SELECTOR, ".result, .record, .data-row")
                    
                    for div in result_divs:
                        text = div.text
                        result = self.parse_text_result(text)
                        if result:
                            results.append(result)
                except:
                    pass
            
            # Method 3: Get entire page text and parse
            if not results:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                results = self.parse_page_text(page_text)
            
            # Method 4: Take screenshot for debugging (optional)
            # driver.save_screenshot('debug_screenshot.png')
            
            return results
            
        except Exception as e:
            print(f"Extraction error: {e}")
            return None
    
    def parse_text_result(self, text):
        """Parse result from text block"""
        result = {}
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            if 'name' in line_lower and ':' in line:
                result['name'] = line.split(':', 1)[1].strip()
            elif 'cnic' in line_lower and ':' in line:
                result['cnic'] = line.split(':', 1)[1].strip()
            elif any(x in line_lower for x in ['mobile', 'number', 'phone']) and ':' in line:
                result['number'] = line.split(':', 1)[1].strip()
            elif 'address' in line_lower and ':' in line:
                result['address'] = line.split(':', 1)[1].strip()
        
        return result if len(result) >= 2 else None
    
    def parse_page_text(self, text):
        """Parse entire page text for results"""
        results = []
        
        # Find mobile numbers
        mobile_pattern = r'(?:\+92|0)?3[0-9]{9}'
        mobiles = re.findall(mobile_pattern, text)
        
        # Find CNICs
        cnic_pattern = r'\d{5}-?\d{7}-?\d'
        cnics = re.findall(cnic_pattern, text)
        
        # Try to find names (capital letters pattern)
        name_pattern = r'(?:Name|NAME)[:\s]+([A-Z][A-Za-z\s]+)'
        names = re.findall(name_pattern, text)
        
        # Combine results
        max_len = max(len(names), len(cnics), len(mobiles))
        
        for i in range(max_len):
            result = {
                'name': names[i] if i < len(names) else 'N/A',
                'cnic': cnics[i] if i < len(cnics) else 'N/A',
                'number': mobiles[i] if i < len(mobiles) else 'N/A',
                'address': 'See website for full details'
            }
            results.append(result)
        
        return results if results else None
    
    async def display_results(self, ctx, cnic, results):
        """Display results in embeds"""
        
        success_embed = discord.Embed(
            title="✅ Records Found",
            description=(
                "```\n"
                "╔═══════════════════════════════════════════════════════╗\n"
                "║           DATABASE QUERY SUCCESSFUL                   ║\n"
                "╠══════���════════════════════════════════════════════════╣\n"
                f"║   CNIC         : {cnic}                    ║\n"
                f"║   Records      : {len(results)} found                              ║\n"
                "║   Method       : Browser Automation                   ║\n"
                "║   Status       : ✅ Complete                          ║\n"
                "║                                                       ║\n"
                "╚═══════════════════════════════════════════════════════╝\n"
                "```"
            ),
            color=0x00FF00,
            timestamp=discord.utils.utcnow()
        )
        
        success_embed.set_thumbnail(url="https://flagcdn.com/w320/pk.png")
        await ctx.send(embed=success_embed)
        
        for i, result in enumerate(results[:10], 1):
            result_embed = discord.Embed(
                title=f"📋 Record #{i}",
                color=0x00D9FF
            )
            
            result_embed.add_field(
                name="👤 Full Name",
                value=f"```{result.get('name', 'N/A')}```",
                inline=False
            )
            
            result_embed.add_field(
                name="🆔 CNIC",
                value=f"```{result.get('cnic', 'N/A')}```",
                inline=True
            )
            
            result_embed.add_field(
                name="📱 Mobile",
                value=f"```{result.get('number', 'N/A')}```",
                inline=True
            )
            
            result_embed.add_field(
                name="📍 Address",
                value=f"```{result.get('address', 'N/A')[:200]}```",
                inline=False
            )
            
            result_embed.set_footer(text=f"Record {i} of {len(results)}")
            
            await ctx.send(embed=result_embed)
        
        if len(results) > 10:
            await ctx.send(f"```\nℹ️ Showing 10 of {len(results)} results.\n```")
        
        disclaimer_embed = discord.Embed(
            title="⚠️ Important Notice",
            description=(
                "```diff\n"
                "- Educational purposes only\n"
                "+ Use responsibly and legally\n"
                "+ Respect privacy laws\n"
                "```\n\n"
                "**📊 Source:** Pakistan Database\n"
                f"**⏰ Retrieved:** {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            ),
            color=0xFF6B35
        )
        
        await ctx.send(embed=disclaimer_embed)


async def setup(bot):
    await bot.add_cog(CNICLookupSelenium(bot))