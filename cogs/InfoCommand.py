import discord
from discord.ext import commands


class InfoCommand(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(name="info", description="Get information about the bot.")
    async def info(self, ctx: discord.ApplicationContext):
        total_users = sum(guild.member_count for guild in self.bot.guilds)
        
        embed = discord.Embed(
            title="📌 EzRoles Bot – General Info",
            description=(
                f"EzRoles.xyz is a free open-source Discord bot that helps you manage your server's roles easily.\n\n"
                f"**Current Stats:**\n"
                f"• Users: {total_users:,} members across all servers\n\n"
                f"**Current Features:**\n"
                f"• AutoRoles - Automatically assign roles to new members\n"
                f"• StickyRoles - Restore roles when users rejoin\n"
                f"• RoleBackup - Backup and restore your server's role setup\n"
                f"• StatusRoles - Assign roles based on user status text\n\n"
                f"⚠️ **Note:** This bot is still under active development. More features will be added soon!\n"
                f"🔹 **Open Source:** You can contribute on [GitHub](https://github.com/irgendein-mensch/EzRoles)"
            ),
            color=discord.Color.greyple()
        )
        embed.add_field(
            name="</info:1358620828563931339>",
            value="🔹 *Shows this information panel with all bot features and commands.*", inline=False)

        view = CategoryChoice()
        await ctx.respond(embed=embed, view=view, ephemeral=True)


class CategoryChoice(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(discord.ui.Button(label="Website", url="https://ezroles.xyz/"))
        self.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/soulshine"))
        self.add_item(discord.ui.Button(label="Add Bot", url="https://discord.com/oauth2/authorize?client_id=1358600279528046602&permissions=268748992&integration_type=0&scope=applications.commands+bot"))
        self.add_item(CategorySelect())


class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="EzRoles", description="General informations", value="category_0"),
            discord.SelectOption(label="AutoRoles", description="Automatically assign roles", value="category_1"),
            discord.SelectOption(label="StickyRoles", description="Reassign roles when users rejoin", value="category_2"),
            discord.SelectOption(label="RoleBackup", description="Backup and restore roles", value="category_3"),
            discord.SelectOption(label="StatusRoles", description="Assign roles based on status text", value="category_4")
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options, custom_id="category_select")

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]

        if value == "category_0":
            total_users = sum(guild.member_count for guild in interaction.client.guilds)
            
            embed = discord.Embed(
                title="📌 EzRoles – General Info",
                description=(
                    f"EzRoles.xyz is a free open-source Discord bot that helps you manage your server's roles easily.\n\n"
                    f"**Current Stats:**\n"
                    f"• Users: {total_users:,} members across all servers\n\n"
                    f"**Current Features:**\n"
                    f"• AutoRoles - Automatically assign roles to new members\n"
                    f"• StickyRoles - Restore roles when users rejoin\n"
                    f"• RoleBackup - Backup and restore your server's role setup\n"
                    f"• StatusRoles - Assign roles based on user status text\n\n"
                    f"⚠️ **Note:** This bot is still under active development. More features will be added soon!\n"
                    f"🔹 **Open Source:** You can contribute on [GitHub](https://github.com/irgendein-mensch/EzRoles)"
                ),
                color=discord.Color.greyple()
            )
            embed.add_field(
                name="</info:1358620828563931339>",
                value="🔹 *Shows this information panel with all bot features and commands.*", inline=False)

        elif value == "category_1":
            embed = discord.Embed(
                title="🎯 AutoRoles",
                description="Automatically assign roles to new members when they join your server.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="</autorole add:1358891606752760104>",
                value="🔹 *Adds a role to be automatically assigned to new members. The bot must have permission to manage this role.*", inline=False)
            embed.add_field(
                name="</autorole remove:1358891606752760104>",
                value="🔹 *Removes a role from the auto-role list so it won't be assigned to new members anymore.*", inline=False)
            embed.add_field(
                name="</autorole list:1358891606752760104>",
                value="🔹 *Lists all roles that are currently set to be automatically assigned to new members.*", inline=False)
            embed.add_field(
                name="</autorole clear:1358891606752760104>",
                value="🔹 *Clears all auto-role settings for this server (requires administrator permissions).*", inline=False)

        elif value == "category_2":
            embed = discord.Embed(
                title="📌 StickyRoles",
                description="Automatically restore roles when users rejoin your server.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="</stickyroles manage:1358950226072834271>",
                value="🔹 *Enable or disable the StickyRoles feature for this server (requires administrator permissions).*", inline=False)
            embed.add_field(
                name="</stickyroles status:1358950226072834271>",
                value="🔹 *Check if StickyRoles are currently enabled for this server.*", inline=False)
            embed.add_field(
                name="</stickyroles clear:1358950226072834271>",
                value="🔹 *Clear all stored sticky roles data for this server (requires administrator permissions).*", inline=False)

        elif value == "category_3":
            embed = discord.Embed(
                title="💾 RoleBackup",
                description="Backup and restore your server's complete role setup including permissions, colors and hierarchy.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="</backup create:1359678345230418071>",
                value="🔹 *Create a new backup of all current server roles (excluding @everyone).*", inline=False)
            embed.add_field(
                name="</backup restore:1359678345230418071>",
                value="🔹 *Restore roles from a previously created backup. Will recreate missing roles and update existing ones.*", inline=False)
            embed.add_field(
                name="</backup delete:1359678345230418071>",
                value="🔹 *Delete the stored backup for this server.*", inline=False)
            embed.add_field(
                name="</backup show:1359678345230418071>",
                value="🔹 *Show details about the current backup including creation date and included roles.*", inline=False)
            embed.add_field(
                name="⚠️ Important Note",
                value="The bot can only restore roles that are **below its highest role** in the hierarchy and for which it has **manage roles permission**.", 
                inline=False)

        elif value == "category_4":
            embed = discord.Embed(
                title="🔍 StatusRoles",
                description="Automatically assign roles to members based on text in their custom status.",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="</statusrole add:1359678345230418071>",
                value="🔹 *Add a role to be assigned when a specific text appears in users' status.*", inline=False)
            embed.add_field(
                name="</statusrole remove:1359678345230418071>",
                value="🔹 *Remove a status role mapping (either specific text or all mappings for a role).*", inline=False)
            embed.add_field(
                name="</statusrole list:1359678345230418071>",
                value="🔹 *List all configured status role mappings for this server.*", inline=False)
            embed.add_field(
                name="</statusrole clear:1359678345230418071>",
                value="🔹 *Remove all status role mappings for this server (admin only).*", inline=False)
            embed.add_field(
                name="ℹ️ How it works",
                value="The bot checks members' custom status every 10 minutes and when their status changes. If the status contains the configured text (case insensitive), the role will be assigned.", 
                inline=False)

        embed.set_footer(text="Made by EzRoles.xyz")
        await interaction.response.edit_message(embed=embed, view=self.view)


def setup(bot: discord.Bot):
    bot.add_cog(InfoCommand(bot))