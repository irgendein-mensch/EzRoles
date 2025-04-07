import discord
import os
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger("EzRoles")

load_dotenv()

bot = discord.Bot(
    intents=discord.Intents.all(),
    activity=discord.CustomActivity("/info | EzRoles.xyz")
)

@bot.event
async def on_ready():
    logger.info(f"Bot is ready. Logged in as {bot.user.name} (ID: {bot.user.id})")
    print(f"""
------------------ Bot started ------------------
Name         : {bot.user.name}
ID           : {bot.user.id}
Servers      : {len(bot.guilds)}
Cogs loaded  : {len(os.listdir('cogs'))}
-------------------------------------------------
""")

if __name__ == "__main__":
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            try:
                bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info(f"Cog loaded: {filename}")
            except Exception as e:
                logger.error(f"Error when loading Cog {filename}: {e}")

    try:
        bot.run(os.getenv("TOKEN"))
    except Exception as e:
        logger.critical(f"Error starting the bot: {e}")
