import discord
from discord.ext import commands


class InfoCommand(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(name="info", description="Get information about the bot.")
    async def info(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="EzRoles Bot",
            description="EzRoles.xyz is a free Discord bot that helps you manage your server's roles easily.",
            color=discord.Color.greyple()
        )
        embed.set_footer(text="Made by EzRoles.xyz")
        button = discord.ui.Button(label="Website", url="https://ezroles.xyz/")
        button2 = discord.ui.Button(label="Support Server", url="https://discord.gg/7tDv9aAQJj")
        button3 = discord.ui.Button(label="Add Bot", url="https://discord.com/oauth2/authorize?client_id=1358600279528046602&permissions=268748992&integration_type=0&scope=applications.commands+bot")
        view = discord.ui.View()
        view.add_item(button)
        view.add_item(button2)
        view.add_item(button3)
        await ctx.respond(embed=embed, view=view, ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(InfoCommand(bot))