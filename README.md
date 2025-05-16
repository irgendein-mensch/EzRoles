# 🎯 EzRoles - Ultimate Discord Role Management

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Discord](https://img.shields.io/discord/1320723057664589925?label=Support%20Server)](https://discord.gg/soulshine)
[![Website](https://img.shields.io/badge/Website-EzRoles.xyz-blue)](https://ezroles.xyz/)

**The smartest way to manage roles on Discord** - Automate role assignments, backup configurations, and enhance your server management with powerful features.


## ✨ Features

| Feature | Description | Status |
|---------|------------|--------|
| **🤖 AutoRoles** | Automatically assign roles to new members | ✅ Live |
| **📌 StickyRoles** | Restore roles when users rejoin your server | ✅ Live |
| **💾 RoleBackup** | Backup & restore complete role configurations | ✅ Live |
| **🔍 StatusRoles** | Assign roles based on user status text | ✅ Live |

### 🔜 Coming Soon
| Feature | Description | Progress |
|---------|------------|----------|
| **🛡️ PingBlocker** | Block pings for specific roles/users | 45% |
| **🎨 RolesTemplate** | Pre-designed role templates | Planned |

## 🚀 Quick Start

1. [Invite the Bot](https://discord.com/oauth2/authorize?client_id=1358600279528046602&permissions=268748992&scope=bot%20applications.commands)
2. Use `/info` in your server
3. Explore the powerful features!

## 📊 Bot Stats

```yaml
Servers: Growing daily!
Users: 5000+ and counting!
Uptime: 99.9%
```

## 🛠️ Commands Overview

### AutoRoles (/autorole)
- `add` - Add auto-assignable roles
- `remove` - Remove from auto-role list
- `list` - Show current auto-roles
- `clear` - Reset all auto-roles

### StickyRoles (/stickyroles)
- `manage` - Enable/disable feature
- `status` - Check current settings
- `clear` - Wipe stored data

### RoleBackup (/backup)
- `create` - Backup current role setup
- `restore` - Restore from backup
- `delete` - Remove backup
- `show` - View backup details

### StatusRoles (/statusrole)
- `add` - Create status→role mapping
- `remove` - Delete mappings
- `list` - Show active mappings
- `clear` - Reset all mappings

## 🤝 Contributing
We're open source! Contribute on [GitHub](https://github.com/irgendein-mensch/EzRoles)

```bash
git clone https://github.com/irgendein-mensch/EzRoles.git
cd EzRoles
pip install -r requirements.txt
```

## 📜 License
MIT © [irgendein-mensch](https://github.com/irgendein-mensch)

---

> 💡 **Pro Tip:** The bot works best when its role is placed **above** all roles it should manage in your server's role hierarchy!