import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import datetime
from utils.logger import get_logger

load_dotenv()

class ServerLogger(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.logger = get_logger("ServerLogger")

    async def send_notification(self, guild: discord.Guild, is_join: bool):
        try:
            channel_id = os.getenv("JOIN_CHANNEL_ID")
            if not channel_id:
                self.logger.error("JOIN_CHANNEL_ID not found in the .env file!")
                return
            
            try:
                channel = await self.bot.fetch_channel(int(channel_id))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException, ValueError) as e:
                self.logger.error(f"Error while fetching the channel: {e}")
                return
            
            if is_join:
                title = "EzRoles - Bot Joined"
                description = f"{guild.name} has added the EzRoles Bot!"
                color = discord.Color.green()
                log_message = f"Join notification sent for {guild.name} (ID: {guild.id})"
            else:
                title = "EzRoles - Bot Left"
                description = f"{guild.name} has removed the EzRoles Bot!"
                color = discord.Color.red()
                log_message = f"Leave notification sent for {guild.name} (ID: {guild.id})"
            
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Made by EzRoles.xyz - Server Count: {len(self.bot.guilds)}")
            
            embed.add_field(name="Server ID", value=guild.id, inline=True)
            
            if is_join:
                owner = str(guild.owner) if guild.owner else "Unknown"
                embed.add_field(name="Owner", value=owner, inline=True)
                embed.add_field(name="Members", value=str(guild.member_count), inline=True)
            
            await channel.send(embed=embed)
            self.logger.info(log_message)
            
        except Exception as e:
            self.logger.error(f"Unexpected error while processing server notification: {e}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.send_notification(guild, is_join=True)
        
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.send_notification(guild, is_join=False)

def setup(bot: discord.Bot):
    bot.add_cog(ServerLogger(bot))
