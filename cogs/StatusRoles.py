import discord
from discord.ext import commands, tasks
from discord.commands import SlashCommandGroup
from utils.logger import get_logger
from utils.DatabaseManager import DatabaseManager

logger = get_logger("statusrole")

class StatusRole(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.db = DatabaseManager("database/statusrole.db")
        bot.loop.create_task(self.db.setup())
        self.status_check.start()
    
    def cog_unload(self):
        self.status_check.cancel()
    
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

    async def add_status_role_mapping(self, ctx: discord.ApplicationContext, role: discord.Role, status_text: str):
        try:
            existing_mappings = await self.db.get_statusroles(ctx.guild.id)
            if existing_mappings:
                await self.db.clear_statusroles(ctx.guild.id)
                
                old_role = ctx.guild.get_role(existing_mappings[0]['role_id'])
                old_text = existing_mappings[0]['status_text']
                
                embed = discord.Embed(
                    title="EzRoles - StatusRole",
                    description=f"Replaced previous status role mapping ({old_role.mention} for \"{old_text}\") with new mapping: {role.mention} for \"{status_text}\".",
                    color=discord.Color.green()
                )
            else:
                await self.db.add_statusrole(ctx.guild.id, role.id, status_text, ctx.author.id)
                
                embed = discord.Embed(
                    title="EzRoles - StatusRole",
                    description=f"{role.mention} will now be assigned to members with \"{status_text}\" in their custom status.",
                    color=discord.Color.green()
                )

            embed.set_footer(text="Made by EzRoles.xyz")
            return embed

        except Exception as e:
            logger.error(f"Error adding status role: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            return embed

    @tasks.loop(minutes=10)
    async def status_check(self):
        try:
            for guild in self.bot.guilds:
                status_roles = await self.db.get_statusroles(guild.id)
                
                if not status_roles:
                    continue
                
                mapping = status_roles[0]
                role_id, status_text = mapping['role_id'], mapping['status_text']
                role = guild.get_role(role_id)
                
                if not role or self.is_bot_managed_role(role):
                    await self.db.clear_statusroles(guild.id)
                    continue
                
                if guild.me.top_role <= role or not guild.me.guild_permissions.manage_roles:
                    continue
                
                for member in guild.members:
                    if member.bot:
                        continue
                    
                    has_status = any(
                        isinstance(activity, discord.CustomActivity) and 
                        activity.state and 
                        status_text.lower() in activity.state.lower()
                        for activity in member.activities
                    )
                    
                    if has_status and role not in member.roles:
                        try:
                            await member.add_roles(role, reason="StatusRole - Status matches criteria")
                        except discord.Forbidden:
                            logger.error(f"No permission to add role {role.name} to {member.display_name}")
                        except Exception as e:
                            logger.error(f"Error adding role {role.name} to {member.display_name}: {e}")
                    
                    elif not has_status and role in member.roles:
                        try:
                            await member.remove_roles(role, reason="StatusRole - Status no longer matches")
                        except discord.Forbidden:
                            logger.error(f"No permission to remove role {role.name} from {member.display_name}")
                        except Exception as e:
                            logger.error(f"Error removing role {role.name} from {member.display_name}: {e}")
        
        except Exception as e:
            logger.error(f"Error in status_check task: {e}")
    
    @status_check.before_loop
    async def before_status_check(self):
        await self.bot.wait_until_ready()
    
    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if before.activities == after.activities:
            return
        
        try:
            guild = after.guild
            status_roles = await self.db.get_statusroles(guild.id)
            
            if not status_roles:
                return
            
            mapping = status_roles[0]
            role_id, status_text = mapping['role_id'], mapping['status_text']
            role = guild.get_role(role_id)
            
            if not role or self.is_bot_managed_role(role):
                await self.db.clear_statusroles(guild.id)
                return
            
            if guild.me.top_role <= role or not guild.me.guild_permissions.manage_roles:
                return
            
            has_status = any(
                isinstance(activity, discord.CustomActivity) and 
                activity.state and 
                status_text.lower() in activity.state.lower()
                for activity in after.activities
            )
            
            if has_status and role not in after.roles:
                try:
                    await after.add_roles(role, reason="StatusRole - Status matches criteria")
                except Exception as e:
                    logger.error(f"Error adding role {role.name} to {after.display_name}: {e}")
            
            elif not has_status and role in after.roles:
                try:
                    await after.remove_roles(role, reason="StatusRole - Status no longer matches")
                except Exception as e:
                    logger.error(f"Error removing role {role.name} from {after.display_name}: {e}")
        
        except Exception as e:
            logger.error(f"Error in on_presence_update: {e}")

    statusrole = SlashCommandGroup("statusrole", "Manage status roles.", default_member_permissions=discord.Permissions(administrator=True))

    @statusrole.command(name="add", description="Add a role to be assigned when a specific text appears in users' status. (Replaces any existing mapping)")
    @discord.default_permissions(manage_roles=True)
    async def add(self, ctx: discord.ApplicationContext, role: discord.Role, status_text: str):
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
                description=f"⚠️ {role.mention} has moderation or admin permissions. Are you sure you want to add it as a status role? Users with \"{status_text}\" in their status will automatically receive these permissions.",
                color=discord.Color.yellow()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            view = ConfirmButton()
            await ctx.respond(embed=embed, view=view, ephemeral=True)
            
            await view.wait()
            
            if view.value is None:
                await ctx.edit(embed=discord.Embed(
                    title="EzRoles - StatusRole",
                    description="Operation timed out.",
                    color=discord.Color.red()
                ), view=None)
                return
            elif not view.value:
                await ctx.edit(embed=discord.Embed(
                    title="EzRoles - StatusRole",
                    description="Operation cancelled.",
                    color=discord.Color.red()
                ), view=None)
                return
            
            response_message = await self.add_status_role_mapping(ctx, role, status_text)
            await ctx.edit(embed=response_message, view=None)
        else:
            response_message = await self.add_status_role_mapping(ctx, role, status_text)
            await ctx.respond(embed=response_message, ephemeral=True)

    @statusrole.command(name="remove", description="Remove the current status role mapping.")
    @discord.default_permissions(manage_roles=True)
    async def remove(self, ctx: discord.ApplicationContext):
        try:
            status_roles = await self.db.get_statusroles(ctx.guild.id)
            
            if not status_roles:
                embed = discord.Embed(
                    title="EzRoles - StatusRole",
                    description="No status role mapping exists for this server.",
                    color=discord.Color.yellow()
                )
            else:
                count = await self.db.clear_statusroles(ctx.guild.id)
                role = ctx.guild.get_role(status_roles[0]['role_id'])
                status_text = status_roles[0]['status_text']
                
                embed = discord.Embed(
                    title="EzRoles - StatusRole",
                    description=f"Removed status role mapping: {role.mention} for \"{status_text}\".",
                    color=discord.Color.green()
                )

            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error removing status role: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

    @statusrole.command(name="view", description="View the current status role mapping.")
    @discord.default_permissions(manage_roles=True)
    async def view(self, ctx: discord.ApplicationContext):
        try:
            status_roles = await self.db.get_statusroles(ctx.guild.id)

            if not status_roles:
                description = "No status role is configured for this server."
            else:
                mapping = status_roles[0]
                role_id, status_text = mapping['role_id'], mapping['status_text']
                role = ctx.guild.get_role(role_id)
                
                if not role or self.is_bot_managed_role(role):
                    await self.db.clear_statusroles(ctx.guild.id)
                    description = "The configured status role was invalid and has been removed."
                else:
                    description = f"Current status role mapping:\n{role.mention}: \"{status_text}\""

            embed = discord.Embed(
                title="EzRoles - StatusRole",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error viewing status role: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)


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
    bot.add_cog(StatusRole(bot))