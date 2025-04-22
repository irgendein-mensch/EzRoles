import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup
from utils.logger import get_logger
from utils.DatabaseManager import DatabaseManager

logger = get_logger("autorole")

class AutoRole(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.db = DatabaseManager("database/autorole.db")
        bot.loop.create_task(self.db.setup())

    def is_bot_managed_role(self, role: discord.Role) -> bool:
        return role.tags is not None and role.tags.is_bot_managed()

    async def check_role_hierarchy(self, ctx: discord.ApplicationContext, role: discord.Role) -> bool:
        if self.is_bot_managed_role(role):
            embed = discord.Embed(
                title="EzRoles - Error",
                description=f"I cannot manage {role.mention} because it belongs to a bot. Bot roles cannot be assigned to users.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
            return False

        if ctx.guild.me.top_role <= role:
            embed = discord.Embed(
                title="EzRoles - Error",
                description=f"I cannot manage {role.mention} because this role is higher or equal to my highest role.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
            return False

        if not ctx.guild.me.guild_permissions.manage_roles:
            embed = discord.Embed(
                title="EzRoles - Error",
                description="I do not have permission to manage roles. Please grant me the 'Manage Roles' permission.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
            return False

        return True

    async def add_autorole(self, ctx: discord.ApplicationContext, role: discord.Role):
        try:
            is_new = await self.db.add_autorole(ctx.guild.id, role.id, ctx.author.id)

            if not is_new:
                embed = discord.Embed(
                    title="EzRoles - Autorole",
                    description=f"{role.mention} is already in the autorole list.",
                    color=discord.Color.yellow()
                )
            else:
                embed = discord.Embed(
                    title="EzRoles - Autorole",
                    description=f"{role.mention} has been added to the autorole list.",
                    color=discord.Color.green()
                )

            embed.set_footer(text="Made by EzRoles.xyz")
            return embed

        except Exception as e:
            logger.error(f"Error adding role: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            return embed

    autorole = SlashCommandGroup("autorole", "Manage autoroles.", default_member_permissions=discord.Permissions(administrator=True))

    @autorole.command(name="add", description="Add a role to the autorole list.")
    @discord.default_permissions(manage_roles=True)
    async def add(self, ctx: discord.ApplicationContext, role: discord.Role):
        if not await self.check_role_hierarchy(ctx, role):
            return

        critical_permissions = [
            'administrator', 'ban_members', 'kick_members', 'manage_channels',
            'manage_guild', 'manage_messages', 'manage_roles', 'manage_webhooks',
            'moderate_members'
        ]
        
        has_critical_perms = any(getattr(role.permissions, perm) for perm in critical_permissions)
        
        if has_critical_perms:
            embed = discord.Embed(
                title="EzRoles - Warning",
                description=f"⚠️ {role.mention} has moderation or admin permissions. Are you sure you want to add it as an autorole? New members will automatically receive these permissions.",
                color=discord.Color.yellow()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            view = ConfirmButton()
            await ctx.respond(embed=embed, view=view, ephemeral=True)
            
            await view.wait()
            
            if view.value is None:
                await ctx.edit(embed=discord.Embed(
                    title="EzRoles - Autorole",
                    description="Operation timed out.",
                    color=discord.Color.red()
                ), view=None)
                return
            elif not view.value:
                await ctx.edit(embed=discord.Embed(
                    title="EzRoles - Autorole",
                    description="Operation cancelled.",
                    color=discord.Color.red()
                ), view=None)
                return
            
            response_message = await self.add_autorole(ctx, role)
            await ctx.edit(embed=response_message, view=None)
        else:
            response_message = await self.add_autorole(ctx, role)
            await ctx.respond(embed=response_message, ephemeral=True)

    @autorole.command(name="remove", description="Remove a role from the autorole list.")
    @discord.default_permissions(manage_roles=True)
    async def remove(self, ctx: discord.ApplicationContext, role: discord.Role):
        try:
            was_removed = await self.db.remove_autorole(ctx.guild.id, role.id)

            if not was_removed:
                embed = discord.Embed(
                    title="EzRoles - Autorole",
                    description=f"{role.mention} was not in the autorole list.",
                    color=discord.Color.yellow()
                )
            else:
                embed = discord.Embed(
                    title="EzRoles - Autorole",
                    description=f"{role.mention} has been removed from the autorole list.",
                    color=discord.Color.green()
                )

            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error removing role: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

    @autorole.command(name="list", description="List all autoroles.")
    @discord.default_permissions(manage_roles=True)
    async def list(self, ctx: discord.ApplicationContext):
        try:
            role_ids = await self.db.get_autoroles(ctx.guild.id)

            if not role_ids:
                description = "No autoroles are set."
            else:
                role_list = []
                valid_role_ids = []

                for role_id in role_ids:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        if self.is_bot_managed_role(role):
                            continue
                            
                        role_list.append(role.mention)
                        valid_role_ids.append(role_id)

                if len(valid_role_ids) < len(role_ids):
                    await self.db.remove_nonexisting_roles(ctx.guild.id, valid_role_ids)

                if not role_list:
                    description = "No valid autoroles were found. All outdated entries were removed."
                else:
                    description = "List of autoroles:\n" + "\n".join(role_list)

            embed = discord.Embed(
                title="EzRoles - Autorole",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error displaying roles: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

    @autorole.command(name="clear", description="Remove all autoroles for this server.")
    @discord.default_permissions(administrator=True)
    async def clear(self, ctx: discord.ApplicationContext):
        try:
            count = await self.db.clear_autoroles(ctx.guild.id)

            embed = discord.Embed(
                title="EzRoles - Autorole",
                description=f"All {count} autoroles have been deleted.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error deleting all roles: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        try:
            role_ids = await self.db.get_autoroles(member.guild.id)

            if not role_ids:
                return

            roles_to_add = []
            failed_roles = []
            valid_role_ids = []

            for role_id in role_ids:
                role = member.guild.get_role(role_id)

                if not role:
                    continue
                
                if self.is_bot_managed_role(role):
                    continue

                valid_role_ids.append(role_id)

                if member.guild.me.top_role > role and member.guild.me.guild_permissions.manage_roles:
                    roles_to_add.append(role)
                else:
                    failed_roles.append(role)

            if len(valid_role_ids) < len(role_ids):
                await self.db.remove_nonexisting_roles(member.guild.id, valid_role_ids)

            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason="AutoRole")
                except discord.Forbidden:
                    logger.error(f"No permission to add roles to {member.display_name}")
                except discord.HTTPException as e:
                    logger.error(f"HTTP error adding roles: {e}")

            if failed_roles:
                logger.warning(f"Could not add some roles to {member.display_name}: {', '.join([r.name for r in failed_roles])}")

        except Exception as e:
            logger.error(f"Error adding auto-roles: {e}")


class ConfirmButton(discord.ui.View):
    def __init__(self, timeout=60):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()


def setup(bot: discord.Bot):
    bot.add_cog(AutoRole(bot))