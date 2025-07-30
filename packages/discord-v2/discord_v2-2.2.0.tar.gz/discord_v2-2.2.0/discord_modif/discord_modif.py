import discord, os, json, threading, asyncio
from discord import utils
from datetime import timedelta
from datetime import datetime

class DiscordModifClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(intents=intents)
        self._ready_event = threading.Event()

    async def on_ready(self):
        print(f"[dm] ✅ Connecté en tant que {self.user}")
        self._ready_event.set()

    async def list_guild(self, guild_id):
        guild = discord.utils.get(self.guilds, id=guild_id)
        if not guild:
            print("[dm] ❌ Serveur introuvable.")
            return
        print(f"[dm] 📋 Salons dans {guild.name} :")
        for c in guild.channels:
            print(f" - {c.name} ({c.type})")

client = DiscordModifClient()
_bot_thread = None


def _start_bot(token):
    asyncio.run(client.start(token))

def start(token_path="modified_python/token.txt"):
    global _bot_thread
    try:
        with open(token_path, "r") as f:
            token = f.read().strip()
    except FileNotFoundError:
        print(f"[dm] ❌ Token introuvable dans {token_path}")
        return

    _bot_thread = threading.Thread(target=_start_bot, args=(token,))
    _bot_thread.start()

    print("[dm] 🕓 Démarrage du bot...")
    client._ready_event.wait()  # Attend que le bot soit prêt
    print("[dm] 🚀 Bot prêt !")



def list(guild_id: int):
    if guild_id is None:
        guild_id = _current_guild_id
    if guild_id is None:
        print("[dm] Aucun serveur spécifié.")
        return
    if not client.is_ready():
        print("[dm] ❌ Le bot n'est pas encore prêt.")
        return

    future = asyncio.run_coroutine_threadsafe(client.list_guild(guild_id), client.loop)
    try:
        future.result()  # Attend que la tâche se termine
    except Exception as e:
        print(f"[dm] ❌ Erreur dans dm.list : {e}")


async def _create_category(guild_id: int, name: str, visibility: str):
    guild = discord.utils.get(client.guilds, id=guild_id)
    if not guild:
        print(f"[dm] ❌ Serveur introuvable : {guild_id}")
        return

    overwrites = {}

    if visibility.lower() == "private":
        overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
    elif visibility.lower() == "public":
        overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=True)
    else:
        print(f"[dm] ❌ Visibilité invalide : {visibility} (utilise 'Public' ou 'Private')")
        return

    try:
        await guild.create_category(name=name, overwrites=overwrites)
        print(f"[dm] ✅ Catégorie '{name}' créée avec visibilité '{visibility}'")
    except Exception as e:
        print(f"[dm] ❌ Erreur lors de la création de la catégorie : {e}")

def CreateCategory(guild_id: int , name: str, visibility: str = "Public"):
    if guild_id is None:
        guild_id = _current_guild_id
    if guild_id is None:
        print("[dm] Aucun serveur spécifié.")
        return
    future = asyncio.run_coroutine_threadsafe(
        _create_category(guild_id, name, visibility),
        client.loop
    )
    try:
        future.result()
    except Exception as e:
        print(f"[dm] ❌ Erreur CreateCategory: {e}")

async def _create_text_channel(guild_id: int, name: str, category_name: str = None, visibility: str = "Public"):
    guild = discord.utils.get(client.guilds, id=guild_id)
    if not guild:
        print(f"[dm] Serveur introuvable : {guild_id}")
        return

    overwrites = {}
    if visibility.lower() == "private":
        overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
    else:
        overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=True)

    category = None
    if category_name:
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            print(f"[dm] Catégorie '{category_name}' introuvable, création d'une catégorie par défaut")
            category = await guild.create_category(category_name, overwrites=overwrites)

    await guild.create_text_channel(name, overwrites=overwrites, category=category)
    print(f"[dm] Salon texte '{name}' créé dans la catégorie '{category_name}' avec visibilité '{visibility}'")

def CreateTextChannel(guild_id: int, name: str, category_name: str = None, visibility: str = "Public"):
    if guild_id is None:
        guild_id = _current_guild_id
    if guild_id is None:
        print("[dm] Aucun serveur spécifié.")
        return
    if not client.is_ready():
        print("[dm] Le bot n'est pas prêt.")
        return
    future = asyncio.run_coroutine_threadsafe(
        _create_text_channel(guild_id, name, category_name, visibility),
        client.loop
    )
    try:
        future.result()
    except Exception as e:
        print(f"[dm] Erreur CreateTextChannel: {e}")


async def _create_vocal_channel(guild_id: int, name: str, category_name: str = None, visibility: str = "Public"):
    guild = discord.utils.get(client.guilds, id=guild_id)
    if not guild:
        print(f"[dm] Serveur introuvable : {guild_id}")
        return

    overwrites = {}
    if visibility.lower() == "private":
        overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
    else:
        overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=True)

    category = None
    if category_name:
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            print(f"[dm] Catégorie '{category_name}' introuvable, création d'une catégorie par défaut")
            category = await guild.create_category(category_name, overwrites=overwrites)

    await guild.create_voice_channel(name, overwrites=overwrites, category=category)
    print(f"[dm] Salon vocal '{name}' créé dans la catégorie '{category_name}' avec visibilité '{visibility}'")

def CreateVocalChannel(guild_id: int, name: str, category_name: str = None, visibility: str = "Public"):
    if guild_id is None:
        guild_id = _current_guild_id
    if guild_id is None:
        print("[dm] Aucun serveur spécifié.")
        return
    if not client.is_ready():
        print("[dm] Le bot n'est pas prêt.")
        return
    future = asyncio.run_coroutine_threadsafe(
        _create_vocal_channel(guild_id, name, category_name, visibility),
        client.loop
    )
    try:
        future.result()
    except Exception as e:
        print(f"[dm] Erreur CreateVocalChannel: {e}")

async def _rename_channel(guild_id: int, old_name: str, new_name: str):
    guild = discord.utils.get(client.guilds, id=guild_id)
    if not guild:
        print(f"[dm] Serveur introuvable : {guild_id}")
        return

    channel = discord.utils.get(guild.channels, name=old_name)
    if not channel:
        print(f"[dm] Salon '{old_name}' introuvable dans le serveur {guild.name}")
        return

    # Détection du type de channel
    if isinstance(channel, discord.TextChannel):
        channel_type = "salon textuel"
    elif isinstance(channel, discord.VoiceChannel):
        channel_type = "salon vocal"
    elif isinstance(channel, discord.CategoryChannel):
        channel_type = "catégorie"
    else:
        channel_type = "type inconnu"

    try:
        await channel.edit(name=new_name)
        print(f"[dm] {channel_type} '{old_name}' renommé en '{new_name}'")
    except Exception as e:
        print(f"[dm] Erreur lors du renommage : {e}")


def RenameChannel(guild_id: int, old_name: str, new_name: str):
    if guild_id is None:
        guild_id = _current_guild_id
    if guild_id is None:
        print("[dm] Aucun serveur spécifié.")
        return
    if not client.is_ready():
        print("[dm] Le bot n'est pas prêt.")
        return
    future = asyncio.run_coroutine_threadsafe(
        _rename_channel(guild_id, old_name, new_name),
        client.loop
    )
    try:
        future.result()
    except Exception as e:
        print(f"[dm] Erreur RenameChannel: {e}")

# delete un ou plusieurs salons/catégories
async def _delete(guild_id: int, names):
    guild = client.get_guild(guild_id)
    if not guild:
        print(f"[dm] ❌ Serveur introuvable avec l'ID {guild_id}")
        return

    if isinstance(names, str):
        names = [names]  # convertir en liste si un seul nom

    found = False
    for channel in guild.channels:
        if channel.name in names:
            await channel.delete()
            print(f"[dm] 🗑️ Supprimé : {channel.name} ({type(channel).__name__})")
            found = True
    for role in guild.roles:
        if role.name == names and not role.is_default():
            try:
                await role.delete()
                print(f"[dm] 🗑️ Rôle supprimé : {role.name}")
                found = True
            except Exception as e:
                print(f"[dm] ❌ Erreur suppression rôle : {e}")

    if not found:
        print(f"[dm] ❌ Aucun des éléments spécifiés n'a été trouvé : {names}")

def delete(guild_id: int, names):
    asyncio.run_coroutine_threadsafe(_delete(guild_id, names), client.loop)

async def _delete_all(guild_id: int):
    guild = client.get_guild(guild_id)
    if not guild:
        print(f"[dm] ❌ Serveur introuvable avec l'ID {guild_id}")
        return

    for channel in guild.channels:
        await channel.delete()
        print(f"[dm] 🗑️ Supprimé : {channel.name} ({type(channel).__name__})")
    for role in guild.roles:
        try:
            if role.is_default():  # Ne jamais supprimer @everyone
                continue
            await role.delete(reason="Suppression via DeleteAll")
            print(f"[dm] 🗑️ Rôle supprimé : {role.name}")
        except Exception as e:
            print(f"[dm] ❌ Impossible de supprimer le rôle {role.name} : {e}")

def delete_all(guild_id: int):
    asyncio.run_coroutine_threadsafe(_delete_all(guild_id), client.loop)

def RenameServer(guild_id, new_name):
    async def _rename():
        guild = client.get_guild(guild_id)
        if not guild:
            print(f"[RenameServer] ❌ Serveur introuvable avec ID : {guild_id}")
            return

        try:
            await guild.edit(name=new_name)
            print(f"[RenameServer] ✅ Serveur renommé en : {new_name}")
        except Exception as e:
            print(f"[RenameServer] ❌ Erreur lors du renommage : {e}")

    asyncio.run_coroutine_threadsafe(_rename(), client.loop)


async def _check(guild_id, log=True):
    guild = client.get_guild(guild_id)
    if guild is None:
        print("[dm] ❌ Serveur introuvable.")
        return

    suspects = []
    for member in guild.members:
        if member.bot:
            continue
        conditions = [
            member.default_avatar == member.avatar,
            (member.joined_at and (discord.utils.utcnow() - member.joined_at).days < 3),
            member.public_flags.value == 0,
            not member.activity
        ]
        if sum(conditions) >= 3:
            suspects.append({
                "username": f"{member.name}#{member.discriminator}",
                "id": member.id,
                "joined_at": str(member.joined_at),
                "avatar_url": str(member.avatar.url if member.avatar else "Aucun"),
                "reason": "Compte suspect (inactif / récent / sans photo de profil / sans bio)"
            })
            try:
                await member.send("⚠️ Votre compte semble suspect (inactif, récent ou sans profil). Vous êtes désormais surveillé par l'équipe de modération.")
            except Exception:
                print(f"[dm] ❌ DM échoué à {member.name}#{member.discriminator}")

    print(f"[dm] 🚨 Comptes suspects détectés: {len(suspects)}")

    if log:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = f"suspects_{guild.id}_{timestamp}.json"
        os.makedirs("logs", exist_ok=True)
        with open(os.path.join("logs", log_file), "w", encoding="utf-8") as f:
            json.dump(suspects, f, indent=4, ensure_ascii=False)
        print(f"[dm] 📝 Suspects enregistrés dans logs/{log_file}")

def check(guild_id, log=True):
    asyncio.run_coroutine_threadsafe(_check(guild_id, log), client.loop)


async def _warn(guild_id, member_id, reason="Vous avez été averti pour comportement inapproprié."):
    guild = client.get_guild(guild_id)
    member = guild.get_member(member_id)
    if member:
        try:
            await member.send(f"⚠️ Avertissement sur **{guild.name}** : {reason}")
            print(f"[dm] ⚠️ Avertissement envoyé à {member}")
        except:
            print(f"[dm] ❌ Impossible d'envoyer un avertissement à {member}")
    else:
        print("[dm] ❌ Membre introuvable")

def warn(guild_id, member_id, reason="Comportement inapproprié."):
    asyncio.run_coroutine_threadsafe(_warn(guild_id, member_id, reason), client.loop)

async def _ban(guild_id, member_id, reason="Violation du règlement."):
    guild = client.get_guild(guild_id)
    member = guild.get_member(member_id)
    if member:
        try:
            await guild.ban(member, reason=reason, delete_message_days=1)
            print(f"[dm] 🔨 {member} banni.")
        except:
            print(f"[dm] ❌ Échec du bannissement de {member}")
    else:
        print("[dm] ❌ Membre introuvable")

def ban(guild_id, member_id, reason="Violation du règlement."):
    asyncio.run_coroutine_threadsafe(_ban(guild_id, member_id, reason), client.loop)

async def _kick(guild_id, member_id, reason="Comportement inacceptable."):
    guild = client.get_guild(guild_id)
    member = guild.get_member(member_id)
    if member:
        try:
            await guild.kick(member, reason=reason)
            print(f"[dm] 👢 {member} expulsé.")
        except:
            print(f"[dm] ❌ Échec de l'expulsion de {member}")
    else:
        print("[dm] ❌ Membre introuvable")

def kick(guild_id, member_id, reason="Comportement inacceptable."):
    asyncio.run_coroutine_threadsafe(_kick(guild_id, member_id, reason), client.loop)

async def _mute(guild_id, member_id, reason="Silence temporaire", duration=None):
    guild = client.get_guild(guild_id)
    member = guild.get_member(member_id)

    if not member:
        print("[dm] ❌ Membre introuvable")
        return

    muted_role = utils.get(guild.roles, name="Muted")
    if not muted_role:
        muted_role = await guild.create_role(name="Muted", reason="Création auto pour mute")
        for channel in guild.channels:
            try:
                await channel.set_permissions(muted_role, speak=False, send_messages=False, add_reactions=False)
            except:
                pass

    try:
        await member.add_roles(muted_role, reason=reason)
        await member.send(f"🔇 Vous avez été réduit au silence sur **{guild.name}**. Raison : {reason}")
        print(f"[dm] 🔇 {member} a été mute.")
    except:
        print(f"[dm] ❌ Impossible de mute {member}")

    if duration:
        await asyncio.sleep(duration)
        try:
            await member.remove_roles(muted_role)
            print(f"[dm] 🔈 {member} a été automatiquement unmute après {duration} secondes.")
        except:
            pass

def mute(guild_id, member_id, reason="Silence temporaire", duration=None):
    asyncio.run_coroutine_threadsafe(_mute(guild_id, member_id, reason, duration), client.loop)


async def _prepare_community(guild_id):
    guild = client.get_guild(guild_id)

    try:
        rules = await guild.create_text_channel("📜-règles")
        welcome = await guild.create_text_channel("👋-bienvenue")
        news = await guild.create_text_channel("📢-annonces")

        await guild.edit(
            verification_level=discord.VerificationLevel.high,
            default_notifications=discord.NotificationLevel.only_mentions
        )

        print(f"[dm] ✅ Canaux créés et paramètres ajustés.")
        for member in guild.members:
            try:
                await member.send(
                    f"📢 Le serveur **{guild.name}** se prépare à devenir une communauté officielle ! 🎉"
                )
            except:
                pass

        print(f"[dm] ✅ Préparation communautaire effectuée.")
    except Exception as e:
        print(f"[dm] ❌ Erreur lors de la configuration communautaire : {e}")

def PrepareCommunity(guild_id):
    asyncio.run_coroutine_threadsafe(_prepare_community(guild_id), client.loop)


async def _create_role(guild_id: int, name: str, color: str = "default", separate: bool = False,
                       admin: bool = False, ban: bool = False, kick: bool = False, mute: bool = False):
    guild = client.get_guild(guild_id)
    if not guild:
        print(f"[dm] ❌ Serveur introuvable ({guild_id})")
        return

    permissions = discord.Permissions.none()

    if admin:
        permissions.administrator = True
    else:
        permissions.ban_members = ban
        permissions.kick_members = kick
        permissions.mute_members = mute
        permissions.send_messages = True
        permissions.read_messages = True

    try:
        role_color = discord.Color.default()
        if hasattr(discord.Color, color.lower()):
            role_color = getattr(discord.Color, color.lower())()

        await guild.create_role(
            name=name,
            permissions=permissions,
            color=role_color,
            hoist=separate,
            reason="Création via dm.CreateRole()"
        )
        print(f"[dm] ✅ Rôle '{name}' créé avec succès.")

    except Exception as e:
        print(f"[dm] ❌ Erreur lors de la création du rôle : {e}")


def CreateRole(guild_id: int, name: str, color: str = "default", separate: bool = False,
               admin: bool = False, ban: bool = False, kick: bool = False, mute: bool = False):
    asyncio.run_coroutine_threadsafe(
        _create_role(guild_id, name, color, separate, admin, ban, kick, mute),
        client.loop
    )

async def _send(guild_id: int, channel_name: str, message: str):
    guild = client.get_guild(guild_id)
    if not guild:
        print(f"[dm] ❌ Serveur introuvable avec l'ID {guild_id}")
        return

    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not channel:
        print(f"[dm] ❌ Salon texte '{channel_name}' introuvable dans le serveur {guild.name}")
        return

    try:
        await channel.send(message)
        print(f"[dm] ✉️ Message envoyé dans #{channel_name} ({guild.name})")
    except Exception as e:
        print(f"[dm] ❌ Impossible d'envoyer le message : {e}")

def send(guild_id: int, channel_name: str, message: str):
    asyncio.run_coroutine_threadsafe(_send(guild_id, channel_name, message), client.loop)

def leave():
    async def _leave():
        print("[dm] Le client a bien été arrété 🛑")
        await client.close()

    asyncio.run_coroutine_threadsafe(_leave(), client.loop)


async def _quit_server(server_id: int):
    guild = client.get_guild(server_id)
    if not guild:
        print(f"[dm] ❌ Serveur introuvable ({server_id})")
        return
    try:
        await guild.leave()
        print(f"[dm] ✅ Le bot a quitté le serveur : {guild.name} ({server_id})")
    except Exception as e:
        print(f"[dm] ❌ Erreur lors du départ du serveur : {e}")

def QuitServer(server_id: int):
    asyncio.run_coroutine_threadsafe(_quit_server(server_id), client.loop)

def _get_role(guild, role_name):
    return discord.utils.get(guild.roles, name=role_name)

def _get_guild(guild_id):
    return client.get_guild(guild_id)

# ----
# Pour chaque permission, une fonction dédiée !
# ----

def SetPermAdministrator(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.administrator = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Administrator {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermViewAuditLog(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.view_audit_log = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ View Audit Log {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermViewGuildInsights(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.view_guild_insights = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ View Guild Insights {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermManageGuild(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.manage_guild = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Manage Guild {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermManageRoles(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.manage_roles = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Manage Roles {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermManageChannels(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.manage_channels = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Manage Channels {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermManageWebhooks(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.manage_webhooks = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Manage Webhooks {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermManageEmojisAndStickers(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.manage_emojis_and_stickers = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Manage Emojis And Stickers {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermManageEvents(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.manage_events = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Manage Events {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermManageThreads(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.manage_threads = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Manage Threads {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermManageMessages(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.manage_messages = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Manage Messages {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermManageNicknames(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.manage_nicknames = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Manage Nicknames {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermKickMembers(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.kick_members = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Kick Members {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermBanMembers(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.ban_members = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Ban Members {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermModerateMembers(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.moderate_members = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Moderate Members {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermMoveMembers(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.move_members = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Move Members {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermMuteMembers(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.mute_members = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Mute Members {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermDeafenMembers(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.deafen_members = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Deafen Members {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermPrioritySpeaker(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.priority_speaker = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Priority Speaker {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermStream(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.stream = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Stream {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermCreateInstantInvite(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.create_instant_invite = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Create Instant Invite {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermChangeNickname(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.change_nickname = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Change Nickname {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermSendMessages(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.send_messages = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Send Messages {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermSendTTSMessages(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.send_tts_messages = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Send TTS Messages {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermSendMessagesInThreads(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.send_messages_in_threads = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Send Messages In Threads {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermSendScheduledMessages(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.send_scheduled_messages = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Send Scheduled Messages {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermUseApplicationCommands(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.use_application_commands = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Use Application Commands {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermViewChannel(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.view_channel = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ View Channel {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermReadMessageHistory(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.read_message_history = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Read Message History {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermAddReactions(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.add_reactions = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Add Reactions {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermAttachFiles(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.attach_files = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Attach Files {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermEmbedLinks(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.embed_links = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Embed Links {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermMentionEveryone(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.mention_everyone = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Mention Everyone {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermUseExternalEmojis(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.use_external_emojis = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Use External Emojis {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermUseExternalStickers(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.use_external_stickers = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Use External Stickers {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermConnect(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.connect = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Connect (Vocal) {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)

def SetPermSpeak(guild_id: int, role_name: str, value: bool):
    async def _set():
        guild = _get_guild(guild_id)
        role = _get_role(guild, role_name)
        if not role:
            print(f"[dm] ❌ Rôle introuvable : {role_name}")
            return
        perms = role.permissions
        perms.speak = value
        try:
            await role.edit(permissions=perms)
            print(f"[dm] ✅ Speak (Vocal) {'activé' if value else 'désactivé'} pour {role_name}")
        except Exception as e:
            print(f"[dm] ❌ Erreur : {e}")
    asyncio.run_coroutine_threadsafe(_set(), client.loop)


import asyncio

async def _generate_webhook(guild_id, channel_name, name="ModWebhook"):
    guild = client.get_guild(guild_id)
    if not guild:
        print(f"[webhook] ❌ Serveur introuvable (ID : {guild_id})")
        return

    # Cherche le salon texte correspondant au nom
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel:
        try:
            webhook = await channel.create_webhook(name=name)
            print(f"[webhook] ✅ Webhook créé dans #{channel.name} : {webhook.url}")
        except Exception as e:
            print(f"[webhook] ❌ Échec de la création du webhook dans #{channel.name} : {e}")
    else:
        print(f"[webhook] ❌ Salon texte '{channel_name}' introuvable dans {guild.name}")
    return webhook

def GenerateWebhook(guild_id, channel_name, name="ModWebhook"):
    asyncio.run_coroutine_threadsafe(_generate_webhook(guild_id, channel_name, name), client.loop)

import asyncio

async def _delete_webhook(guild_id, channel_name, name=None):
    guild = client.get_guild(guild_id)
    if not guild:
        print(f"[webhook] ❌ Serveur introuvable (ID : {guild_id})")
        return

    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not channel:
        print(f"[webhook] ❌ Salon texte '{channel_name}' introuvable dans {guild.name}")
        return

    try:
        webhooks = await channel.webhooks()
        if not webhooks:
            print(f"[webhook] ❌ Aucun webhook trouvé dans #{channel.name}")
            return

        deleted = 0
        for webhook in webhooks:
            if name is None or webhook.name == name:
                await webhook.delete()
                print(f"[webhook] 🗑️ Supprimé : {webhook.name}")
                deleted += 1

        if deleted == 0:
            print(f"[webhook] ❌ Aucun webhook nommé '{name}' trouvé dans #{channel.name}")

    except Exception as e:
        print(f"[webhook] ❌ Erreur lors de la suppression : {e}")

def DeleteWebhook(guild_id, channel_name, name=None):
    asyncio.run_coroutine_threadsafe(_delete_webhook(guild_id, channel_name, name), client.loop)

async def _create_invite_link(guild_id, channel_name, reason="Invitation automatique"):
    guild = client.get_guild(guild_id)
    if not guild:
        print(f"[invite] ❌ Serveur introuvable (ID : {guild_id})")
        return

    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not channel:
        print(f"[invite] ❌ Salon texte '{channel_name}' introuvable dans {guild.name}")
        return

    try:
        invite = await channel.create_invite(reason=reason, max_age=0, max_uses=0)
        print(f"[invite] ✅ Lien d'invitation créé : {invite.url}")
    except Exception as e:
        print(f"[invite] ❌ Erreur lors de la création de l'invitation : {e}")

def CreateInviteLink(guild_id, channel_name, reason="Invitation automatique"):
    asyncio.run_coroutine_threadsafe(_create_invite_link(guild_id, channel_name, reason), client.loop)

async def _delete_invite_link(guild_id, channel_name, created_by=None):
    guild = client.get_guild(guild_id)
    if not guild:
        print(f"[invite] ❌ Serveur introuvable (ID : {guild_id})")
        return

    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not channel:
        print(f"[invite] ❌ Salon texte '{channel_name}' introuvable dans {guild.name}")
        return

    try:
        invites = await guild.invites()
        deleted = 0
        for invite in invites:
            if invite.channel.id == channel.id:
                if created_by is None or (invite.inviter and invite.inviter.name == created_by):
                    await invite.delete()
                    print(f"[invite] 🗑️ Invitation supprimée : {invite.url}")
                    deleted += 1
        if deleted == 0:
            print(f"[invite] ❌ Aucune invitation trouvée à supprimer dans #{channel.name}")
    except Exception as e:
        print(f"[invite] ❌ Erreur lors de la suppression : {e}")

def DeleteInviteLink(guild_id, channel_name, created_by=None):
    asyncio.run_coroutine_threadsafe(_delete_invite_link(guild_id, channel_name, created_by), client.loop)


