import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup, option
from utils.logger import get_logger
from utils.DatabaseManager import DatabaseManager

logger = get_logger("stickyroles")

class StickyRoles(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.db = DatabaseManager("database/stickyroles.db")
        bot.loop.create_task(self.db.setup())

    stickyroles = SlashCommandGroup("stickyroles", "Manage sticky roles.", default_member_permissions=discord.Permissions(administrator=True))
    
    @stickyroles.command(name="manage", description="Enable or disable the Sticky Roles feature for this server.")
    @discord.default_permissions(administrator=True)
    @option("mode", description="Select 'On' to enable or 'Off' to disable Sticky Roles.", choices=["On", "Off"])
    async def manage(self, ctx: discord.ApplicationContext, mode: str):
        try:
            enabled = mode == "On"
            
            result = await self.db.set_feature_status(ctx.guild.id, enabled)
            
            if result:
                embed = discord.Embed(
                    title="EzRoles - Sticky Roles",
                    description=f"Sticky roles have been {'enabled' if enabled else 'disabled'}.",
                    color=discord.Color.green() if enabled else discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="EzRoles - Sticky Roles",
                    description=f"Sticky roles were already {'enabled' if enabled else 'disabled'}.",
                    color=discord.Color.yellow()
                )
                
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting sticky roles status: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
    
    @stickyroles.command(name="status", description="Check if Sticky Roles are currently enabled.")
    @discord.default_permissions(manage_roles=True)
    async def status(self, ctx: discord.ApplicationContext):
        try:
            sticky_enabled = await self.db.get_feature_status(ctx.guild.id)

            color = discord.Color.green() if sticky_enabled else discord.Color.red()
            status_text = "enabled" if sticky_enabled else "disabled"

            embed = discord.Embed(
                title="EzRoles - Sticky Roles Status",
                description=f"Sticky roles are currently **{status_text}**.",
                color=color
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error checking sticky roles status: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        try:
            is_enabled = await self.db.get_feature_status(member.guild.id)
            if not is_enabled:
                return
                
            if member.bot:
                return
                
            role_ids = []
            for role in member.roles:
                if role.id != member.guild.default_role.id:
                    bot_role = False
                    for bot_member in member.guild.members:
                        if bot_member.bot and bot_member.id == role.tags.bot_id if role.tags and hasattr(role.tags, 'bot_id') else False:
                            bot_role = True
                            break
                    
                    if not bot_role:
                        role_ids.append(role.id)
            
            if not role_ids:
                return
                
            await self.db.save_member_roles(member.guild.id, member.id, role_ids)
            
        except Exception as e:
            logger.error(f"Error saving roles for leaving member: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        try:
            is_enabled = await self.db.get_feature_status(member.guild.id)
            if not is_enabled:
                return
                
            if member.bot:
                return
                
            role_ids = await self.db.get_member_roles(member.guild.id, member.id)
            
            if not role_ids:
                return
                
            roles_to_add = []
            failed_roles = []
            
            for role_id in role_ids:
                role = member.guild.get_role(role_id)
                
                if not role:
                    continue
                
                if role.tags and hasattr(role.tags, 'bot_id'):
                    continue
                    
                if member.guild.me.top_role > role and member.guild.me.guild_permissions.manage_roles:
                    roles_to_add.append(role)
                else:
                    failed_roles.append(role)
            
            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason="StickyRoles")
                except discord.Forbidden:
                    logger.error(f"No permission to add roles to {member.name}")
                except discord.HTTPException as e:
                    logger.error(f"HTTP error adding roles: {e}")
            
            if failed_roles:
                logger.warning(f"Could not restore some roles to {member.name}: {', '.join([r.name for r in failed_roles])}")
                
        except Exception as e:
            logger.error(f"Error restoring roles for joining member: {e}")
    
    @stickyroles.command(name="clear", description="Clear stored roles for all members in this server.")
    @discord.default_permissions(administrator=True)
    async def clear(self, ctx: discord.ApplicationContext):
        try:
            count = await self.db.clear_sticky_roles(ctx.guild.id)
            
            embed = discord.Embed(
                title="EzRoles - Sticky Roles",
                description=f"Cleared stored roles for {count} members.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error clearing sticky roles: {e}")
            embed = discord.Embed(
                title="EzRoles - Error",
                description="An error occurred. Please try again later.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)

def setup(bot: discord.Bot):
    bot.add_cog(StickyRoles(bot))