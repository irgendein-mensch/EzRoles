import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup
from utils.logger import get_logger
from utils.DatabaseManager import DatabaseManager


class RoleBackup(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.logger = get_logger("RoleBackup")
        self.db = DatabaseManager("database/rolebackup.db")

    backup = SlashCommandGroup("backup", "Manage role backup.", default_member_permissions=discord.Permissions(administrator=True))
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.db.setup()
    
    @backup.command(name="create", description="Create a backup of the current roles.")
    @discord.default_permissions(administrator=True)
    async def create_backup(self, ctx: discord.ApplicationContext):
        existing_backup = await self.db.get_role_backup(ctx.guild.id)
        
        if existing_backup:
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description="A backup already exists for this server. Would you like to overwrite it?",
                color=discord.Color.yellow()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            view = ConfirmButton()
            await ctx.respond(embed=embed, view=view, ephemeral=True)
            
            await view.wait()
            
            if view.value is None:
                await ctx.edit(embed=discord.Embed(
                    title="EzRoles - Role Backup",
                    description="Operation timed out.",
                    color=discord.Color.red()
                ), view=None)
                return
            elif not view.value:
                await ctx.edit(embed=discord.Embed(
                    title="EzRoles - Role Backup",
                    description="Operation cancelled.",
                    color=discord.Color.red()
                ), view=None)
                return
        
        roles_data = []
        for role in ctx.guild.roles:
            if role.is_default():
                continue
                
            role_data = {
                "id": role.id,
                "name": role.name,
                "color": role.color.value,
                "hoist": role.hoist,
                "position": role.position,
                "permissions": role.permissions.value,
                "mentionable": role.mentionable
            }
            roles_data.append(role_data)
        
        success = await self.db.save_role_backup(ctx.guild.id, ctx.author.id, roles_data)
        
        if success:
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description=f"Backup created successfully with {len(roles_data)} roles!",
                color=discord.Color.green()
            )
        else:
            self.logger.error(f"Failed to create role backup for guild {ctx.guild.id}")
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description="Failed to create backup.",
                color=discord.Color.red()
            )
            
        embed.set_footer(text="Made by EzRoles.xyz")
        if existing_backup:
            await ctx.edit(embed=embed, view=None)
        else:
            await ctx.respond(embed=embed, ephemeral=True)
    
    @backup.command(name="restore", description="Restore roles from a backup.")
    @discord.default_permissions(administrator=True)
    async def restore_backup(self, ctx: discord.ApplicationContext):
        backup_data = await self.db.get_role_backup(ctx.guild.id)
        
        if not backup_data:
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description="No backup found for this server.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="EzRoles - Role Backup",
            description=(
                f"Are you sure you want to restore {len(backup_data['roles'])} roles from the backup?\n"
                f"⚠️ The bot can only restore roles that are **below its highest role** and **within its permission scope**."
            ),
            color=discord.Color.yellow()
        )
        embed.set_footer(text="Made by EzRoles.xyz")
        view = ConfirmButton()
        await ctx.respond(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            await ctx.edit(embed=discord.Embed(
                title="EzRoles - Role Backup",
                description="Operation timed out.",
                color=discord.Color.red()
            ), view=None)
            return
        elif not view.value:
            await ctx.edit(embed=discord.Embed(
                title="EzRoles - Role Backup",
                description="Operation cancelled.",
                color=discord.Color.red()
            ), view=None)
            return
        
        await ctx.edit(embed=discord.Embed(
            title="EzRoles - Role Backup",
            description="Restoring roles... This may take some time.",
            color=discord.Color.blue()
        ), view=None)
        
        current_roles = {role.id: role for role in ctx.guild.roles}
        
        roles_restored = 0
        roles_updated = 0
        roles_failed = 0
        
        try:
            for role_data in backup_data['roles']:
                role_id = role_data['id']
                
                if role_id in current_roles:
                    try:
                        await current_roles[role_id].edit(
                            name=role_data['name'],
                            color=discord.Color(role_data['color']),
                            hoist=role_data['hoist'],
                            mentionable=role_data['mentionable'],
                            permissions=discord.Permissions(role_data['permissions'])
                        )
                        roles_updated += 1
                    except Exception as e:
                        self.logger.error(f"Error updating role {role_id}: {e}")
                        roles_failed += 1
                else:
                    try:
                        await ctx.guild.create_role(
                            name=role_data['name'],
                            color=discord.Color(role_data['color']),
                            hoist=role_data['hoist'],
                            mentionable=role_data['mentionable'],
                            permissions=discord.Permissions(role_data['permissions'])
                        )
                        roles_restored += 1
                    except Exception as e:
                        self.logger.error(f"Error creating role: {e}")
                        roles_failed += 1
            
            for role_data in sorted(backup_data['roles'], key=lambda r: r['position'], reverse=True):
                role_id = role_data['id']
                if role_id in current_roles:
                    try:
                        if current_roles[role_id].position != role_data['position']:
                            await current_roles[role_id].edit(position=role_data['position'])
                    except Exception as e:
                        self.logger.error(f"Error fixing role position {role_id}: {e}")
            
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description=(
                    f"Backup restored successfully!\n"
                    f"✅ {roles_restored} roles created\n"
                    f"🔄 {roles_updated} roles updated\n"
                    f"❌ {roles_failed} roles failed\n\n"
                    f"ℹ️ Note: The bot can only manage roles **below its highest role** and for which it has sufficient permissions."
                ),
                color=discord.Color.green()
            )
        except Exception as e:
            self.logger.error(f"Failed to restore role backup for guild {ctx.guild.id}: {e}")
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description=f"Error during restore: {str(e)}",
                color=discord.Color.red()
            )
        
        embed.set_footer(text="Made by EzRoles.xyz")
        await ctx.edit(embed=embed)
        
    @backup.command(name="delete", description="Delete a backup.")
    @discord.default_permissions(administrator=True)
    async def delete_backup(self, ctx: discord.ApplicationContext):
        backup_exists = await self.db.backup_exists(ctx.guild.id)
        
        if not backup_exists:
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description="No backup found for this server.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="EzRoles - Role Backup",
            description="Are you sure you want to delete the backup for this server? This action cannot be undone.",
            color=discord.Color.yellow()
        )
        embed.set_footer(text="Made by EzRoles.xyz")
        view = ConfirmButton()
        await ctx.respond(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            await ctx.edit(embed=discord.Embed(
                title="EzRoles - Role Backup",
                description="Operation timed out.",
                color=discord.Color.red()
            ), view=None)
            return
        elif not view.value:
            await ctx.edit(embed=discord.Embed(
                title="EzRoles - Role Backup",
                description="Operation cancelled.",
                color=discord.Color.red()
            ), view=None)
            return
        
        success = await self.db.delete_role_backup(ctx.guild.id)
        
        if success:
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description="Backup deleted successfully!",
                color=discord.Color.green()
            )
        else:
            self.logger.error(f"Failed to delete role backup for guild {ctx.guild.id}")
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description="Failed to delete backup.",
                color=discord.Color.red()
            )
            
        embed.set_footer(text="Made by EzRoles.xyz")
        await ctx.edit(embed=embed, view=None)
    
    @backup.command(name="show", description="Show all roles in my backup.")
    @discord.default_permissions(administrator=True)
    async def show_backups(self, ctx: discord.ApplicationContext):
        backup_data = await self.db.get_role_backup(ctx.guild.id)
        
        if not backup_data:
            embed = discord.Embed(
                title="EzRoles - Role Backup",
                description="No backup found for this server.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by EzRoles.xyz")
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        timestamp = backup_data['created_at']
        created_by = f"<@{backup_data['created_by']}>"
        roles = backup_data['roles']
        
        embed = discord.Embed(
            title="EzRoles - Role Backup",
            description=f"Backup information for {ctx.guild.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Created By", value=created_by, inline=True)
        embed.add_field(name="Created At", value=timestamp, inline=True)
        embed.add_field(name="Total Roles", value=str(len(roles)), inline=True)
        
        role_list = ""
        for i, role in enumerate(sorted(roles, key=lambda r: r['position'], reverse=True)):
            if i >= 25:
                role_list += f"... and {len(roles) - 25} more roles"
                break
            
            role_list += f"• {role['name']}\n"
        
        if role_list:
            embed.add_field(name="Roles", value=role_list, inline=False)
        
        embed.set_footer(text="Made by EzRoles.xyz")
        await ctx.respond(embed=embed, ephemeral=True)
    
            
def setup(bot: discord.Bot):
    bot.add_cog(RoleBackup(bot))
    
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