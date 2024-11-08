from datetime import datetime
import random
import struct
import bcrypt
from typing import List, Optional

# Emoji Class
class Emoji:
    def __init__(self, id, name, animated=False, available=True, managed=False, require_colons=False, roles=None, user=None):
        self.id = id
        self.name = name
        self.animated = animated
        self.available = available
        self.managed = managed
        self.require_colons = require_colons
        self.roles = roles if roles is not None else []
        self.user = user

# Invite Class
class Invite:
    def __init__(self, code, channel, guild=None, inviter=None, target_user=None, expires_at=None, approximate_member_count=None, approximate_presence_count=None):
        self.code = code
        self.channel = channel
        self.guild = guild
        self.inviter = inviter
        self.target_user = target_user
        self.expires_at = expires_at
        self.approximate_member_count = approximate_member_count
        self.approximate_presence_count = approximate_presence_count

# Message Class
class Message:
    def __init__(self, id, channel_id, author, content, timestamp, tts=False, pinned=False, mention_everyone=False, mentions=None, embeds=None, attachments=None, stickers=None):
        self.id = id
        self.channel_id = channel_id
        self.author = author
        self.content = content
        self.timestamp = timestamp
        self.tts = tts
        self.pinned = pinned
        self.mention_everyone = mention_everyone
        self.mentions = mentions if mentions is not None else []
        self.embeds = embeds if embeds is not None else []
        self.attachments = attachments if attachments is not None else []
        self.stickers = stickers if stickers is not None else []
        
    def to_dict(self):
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "author": self.author,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tts": self.tts,
            "pinned": self.pinned,
            "mention_everyone": self.mention_everyone,
            "mentions": self.mentions,
            "embeds": self.embeds,
            "attachments": self.attachments,
            "stickers": self.stickers
        }
class Discriminator:
    @staticmethod
    def generate():
        discrim = random.randint(1, 9999)
        return f"{discrim:04}"

class Snowflake:
    def __init__(self, id, datacenter_id, worker_id, increment):
        if not self.is_valid_snowflake(id):
            raise ValueError("Not a snowflake")
        self.id = id
        self.datacenter_id = datacenter_id
        self.worker_id = worker_id
        self.increment = increment

    @staticmethod
    def is_valid_snowflake(id):
        return id.isdigit() and len(id) <= 19

    @classmethod
    def generate(cls, datacenter_id, worker_id):
        timestamp = int(datetime.now().timestamp())
        increment = random.randint(0x0, 0xFF)
        epoch = 1420070400
        snowflake = (timestamp - epoch << 22) | (datacenter_id << 17) | (worker_id << 22) | increment
        return snowflake

    def __str__(self):
        return self.id

    def __repr__(self):
        return f"Snowflake(id={self.id}, datacenter_id={self.datacenter_id}, worker_id={self.worker_id}, increment={self.increment})"

class RoleTags:
    def __init__(self, bot_id, integration_id, premium_subscriber=None):
        self.bot_id = bot_id
        self.integration_id = integration_id
        self.premium_subscriber = premium_subscriber

class Role:
    def __init__(self, id, color, hoist, managed, mentionable, name, permissions, position, tags, unicode_emoji=None, icon=None):
        self.color = color
        self.hoist = hoist
        self.icon = icon
        self.id = id
        self.managed = managed
        self.mentionable = mentionable
        self.name = name
        self.permissions = permissions
        self.position = position
        self.tags = tags
        self.unicode_emoji = unicode_emoji

    def to_dict(self):
        return {
            "color": self.color,
            "hoist": self.hoist,
            "id": self.id,
            "managed": self.managed,
            "mentionable": self.mentionable,
            "name": self.name,
            "permissions": self.permissions,
            "position": self.position,
            "tags": vars(self.tags),
            "unicode_emoji": self.unicode_emoji,
            "icon": self.icon
        }

class Channel:
    def __init__(self, id, type, name=None, nsfw=None,
                 parent_id=None, permission_overwrites=None,
                 position=0, guild_id=None):
        self.id = id
        self.type = type
        self.name = name
        self.nsfw = nsfw
        self.parent_id = parent_id
        self.permission_overwrites = permission_overwrites if permission_overwrites is not None else []
        self.position = position
        self.guild_id = guild_id

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "nsfw": self.nsfw,
            "parent_id": self.parent_id,
            "permission_overwrites": self.permission_overwrites,
            "position": self.position,
            "guild_id": self.guild_id
        }

class User:
    def __init__(self, id, username, discriminator, avatar=None, 
                 banner=None, accent_color=None, bot=False, 
                 email=None, token=None, locale=None, mfa_enabled=False, 
                 premium_type=None, public_flags=0, flags=0, 
                 verified=False, system=False, password=None):
        self.id = id
        self.username = username
        self.password = self.hash_password(password)
        self.discriminator = discriminator
        self.avatar = avatar
        self.banner = banner
        self.accent_color = accent_color
        self.bot = bot
        self.email = email
        self.token = token
        self.locale = locale
        self.mfa_enabled = mfa_enabled
        self.premium_type = premium_type
        self.public_flags = public_flags
        self.flags = flags
        self.verified = verified
        self.system = system
        
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "discriminator": self.discriminator,
            "avatar": self.avatar,
            "banner": self.banner,
            "accent_color": self.accent_color,
            "bot": self.bot,
            "email": self.email,
            "token": self.token,
            "locale": self.locale,
            "mfa_enabled": self.mfa_enabled,
            "premium_type": self.premium_type,
            "public_flags": self.public_flags,
            "flags": self.flags,
            "verified": self.verified,
            "system": self.system
        }
        
    def hash_password(self, password):
        if password:
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return None

    def get_flags(self):
        return UserFlags.get_flag_names(self.flags)

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

class Guild:
    def __init__(self, id, name, owner_id, application_id, description=None, 
                 verification_level=0, nsfw_level=0, explicit_content_filter=0,
                 afk_channel_id=None, afk_timeout=300, banner=None,
                 channels=None, emojis=None, features=None,
                 roles=None, system_channel_id=None, public_updates_channel_id=None,
                 widget_enabled=False, widget_channel_id=None, region='us-west',
                 max_members=500000, premium_tier=0, premium_subscription_count=0,
                 preferred_locale='en-US', member_count=0, approximate_member_count=None,
                 approximate_presence_count=None, max_presences=None, mfa_level=0,
                 joined_at=None, large=False, max_video_channel_users=None,
                 discovery_splash=None, stickers=None, rules_channel_id=None,
                 stage_instances=None, welcome_screen=None,
                 voice_states=None, unavailable=False):
        everyoneRole = Role(
            id=Snowflake.generate(random.randint(0, 31), random.randint(0, 31)),
            name="@everyone",
            permissions="2248473465835073",
            position=0,
            color=0,
            hoist=False,
            managed=False,
            mentionable=False,
            tags=RoleTags('', '')
        )
        self.id = id
        self.name = name
        if name == "":
            print("Guild name should not be empty")
            return
        self.owner_id = owner_id
        self.application_id = application_id
        self.description = description
        self.verification_level = verification_level
        self.nsfw_level = nsfw_level
        self.explicit_content_filter = explicit_content_filter
        self.afk_channel_id = afk_channel_id
        self.afk_timeout = afk_timeout
        self.banner = banner
        self.channels = channels if channels is not None else []
        self.emojis = emojis if emojis is not None else []
        self.features = features if features is not None else []
        self.roles = [everyoneRole.to_dict()]
        if roles is not None:
            self.roles += roles
        self.system_channel_id = system_channel_id
        self.public_updates_channel_id = public_updates_channel_id
        self.widget_enabled = widget_enabled
        self.widget_channel_id = widget_channel_id
        self.region = region
        self.max_members = max_members
        self.premium_tier = premium_tier
        self.premium_subscription_count = premium_subscription_count
        self.preferred_locale = preferred_locale
        self.member_count = member_count
        self.approximate_member_count = approximate_member_count
        self.approximate_presence_count = approximate_presence_count
        self.max_presences = max_presences
        self.mfa_level = mfa_level
        self.joined_at = joined_at
        self.large = large
        self.max_video_channel_users = max_video_channel_users
        self.discovery_splash = discovery_splash
        self.stickers = stickers if stickers is not None else []
        self.rules_channel_id = rules_channel_id
        self.stage_instances = stage_instances if stage_instances is not None else []
        self.welcome_screen = welcome_screen
        self.voice_states = voice_states if voice_states is not None else []
        self.unavailable = unavailable
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "application_id": self.application_id,
            "description": self.description,
            "verification_level": self.verification_level,
            "nsfw_level": self.nsfw_level,
            "explicit_content_filter": self.explicit_content_filter,
            "afk_channel_id": self.afk_channel_id,
            "afk_timeout": self.afk_timeout,
            "banner": self.banner,
            "channels": self.channels,
            "emojis": self.emojis,
            "features": self.features,
            "roles": self.roles,
            "system_channel_id": self.system_channel_id,
            "public_updates_channel_id": self.public_updates_channel_id,
            "widget_enabled": self.widget_enabled,
            "widget_channel_id": self.widget_channel_id,
            "region": self.region,
            "max_members": self.max_members,
            "premium_tier": self.premium_tier,
            "premium_subscription_count": self.premium_subscription_count,
            "preferred_locale": self.preferred_locale,
            "member_count": self.member_count,
            "approximate_member_count": self.approximate_member_count,
            "approximate_presence_count": self.approximate_presence_count,
            "max_presences": self.max_presences,
            "mfa_level": self.mfa_level,
            "joined_at": self.joined_at,
            "large": self.large,
            "max_video_channel_users": self.max_video_channel_users,
            "discovery_splash": self.discovery_splash,
            "stickers": self.stickers,
            "rules_channel_id": self.rules_channel_id,
            "stage_instances": self.stage_instances,
            "welcome_screen": self.welcome_screen,
            "voice_states": self.voice_states,
            "unavailable": self.unavailable
        }
        
    def remove_role(self, role):
        if role.name is not '@everyone':
            self.roles.remove(role)
            return self.roles
        else:
            return None
        
class GuildMember:
    def __init__(self, avatar: str, deaf: bool, joined_at: str, mute: bool, pending: bool, 
                 roles: list(), user: User, communication_disabled_until: str = None, 
                 nick: str = None, premium_since: str = None):
        self.avatar = avatar
        self.communication_disabled_until = communication_disabled_until
        self.deaf = deaf
        self.joined_at = joined_at
        self.mute = mute
        self.nick = nick
        self.pending = pending
        self.premium_since = premium_since
        self.roles = roles
        self.user = user
        
# Sticker Class
class Sticker:
    def __init__(self, id, name, description, format_type, type, guild_id=None, pack_id=None, sort_value=None, available=True, tags=""):
        self.id = id
        self.name = name
        self.description = description
        self.format_type = format_type
        self.type = type
        self.guild_id = guild_id
        self.pack_id = pack_id
        self.sort_value = sort_value
        self.available = available
        self.tags = tags
        self.asset = ""  # Previously the sticker asset hash
