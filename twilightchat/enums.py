# Sticker Format Types (for demonstration purposes)
class StickerFormatType:
    PNG = 1
    APNG = 2
    LOTTIE = 3

# Sticker Types (for demonstration purposes)
class StickerType:
    STANDARD = 1
    GUILD = 2

# Message Types (for demonstration purposes)
class MessageType:
    DEFAULT = 0
    REPLY = 19

class UserPremiumType:
    Nitro = 2
    NitroClassic = 1

class UserFlags:
    STAFF = 1
    PARTNER = 2
    HYPESQUAD = 4
    BUG_HUNTER_LEVEL_1 = 8
    HYPESQUAD_ONLINE_HOUSE_1 = 64
    HYPESQUAD_ONLINE_HOUSE_2 = 128
    HYPESQUAD_ONLINE_HOUSE_3 = 256
    PREMIUM_EARLY_SUPPORTER = 512
    BOT_HTTP_INTERACTIONS = 524288
    VERIFIED_BOT = 65536
    VERIFIED_DEVELOPER = 131072
    CERTIFIED_MODERATOR = 262144
    BUG_HUNTER_LEVEL_2 = 16384

    FLAG_NAMES = {
        STAFF: "Discord Employee",
        PARTNER: "Partnered Server Owner",
        HYPESQUAD: "HypeSquad Events Coordinator",
        BUG_HUNTER_LEVEL_1: "Bug Hunter Level 1",
        HYPESQUAD_ONLINE_HOUSE_1: "House Bravery Member",
        HYPESQUAD_ONLINE_HOUSE_2: "House Brilliance Member",
        HYPESQUAD_ONLINE_HOUSE_3: "House Balance Member",
        PREMIUM_EARLY_SUPPORTER: "Early Nitro Supporter",
        BOT_HTTP_INTERACTIONS: "Bot uses only HTTP interactions",
        VERIFIED_BOT: "Verified Bot",
        VERIFIED_DEVELOPER: "Early Verified Bot Developer",
        CERTIFIED_MODERATOR: "Discord Certified Moderator",
        BUG_HUNTER_LEVEL_2: "Bug Hunter Level 2",
    }

    @classmethod
    def has_flag(cls, flags, flag):
        return (flags & flag) == flag

    @classmethod
    def get_flag_names(cls, flags):
        return [name for value, name in cls.FLAG_NAMES.items() if cls.has_flag(flags, value)]
