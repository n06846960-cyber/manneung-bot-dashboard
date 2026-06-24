"""만능 봇 공통 유틸 함수"""

import discord

from config import BOT_COLOR


def create_embed(title: str, description: str, color: int = BOT_COLOR, bot=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if bot and getattr(bot, "user", None):
        embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text="⭐ 만능 봇 | 친목 서버 관리 봇")
    return embed


def _strip_ephemeral_for_channel(kwargs: dict):
    clean = dict(kwargs)
    clean.pop("ephemeral", None)
    clean.pop("thinking", None)
    return clean


async def safe_interaction_send(interaction: discord.Interaction, *args, **kwargs):
    if interaction is None:
        return None
    try:
        if interaction.response.is_done():
            return await interaction.followup.send(*args, **kwargs)
        return await interaction.response.send_message(*args, **kwargs)
    except discord.HTTPException as e:
        code = getattr(e, "code", None)
        if code == 40060:
            try:
                return await interaction.followup.send(*args, **kwargs)
            except (discord.NotFound, discord.HTTPException):
                return None
        if code == 10062:
            if not kwargs.get("ephemeral") and getattr(interaction, "channel", None):
                try:
                    return await interaction.channel.send(*args, **_strip_ephemeral_for_channel(kwargs))
                except Exception:
                    return None
            return None
        raise
    except discord.NotFound:
        return None


async def safe_interaction_defer(interaction: discord.Interaction, *args, **kwargs):
    if interaction is None:
        return False
    try:
        if interaction.response.is_done():
            return False
        await interaction.response.defer(*args, **kwargs)
        return True
    except discord.HTTPException as e:
        if getattr(e, "code", None) in (40060, 10062):
            return False
        raise
    except discord.NotFound:
        return False


async def safe_interaction_edit(interaction: discord.Interaction, *args, **kwargs):
    if interaction is None:
        return None
    try:
        if interaction.response.is_done():
            try:
                return await interaction.edit_original_response(*args, **kwargs)
            except Exception:
                if getattr(interaction, "message", None):
                    return await interaction.message.edit(*args, **kwargs)
                return None
        return await interaction.response.edit_message(*args, **kwargs)
    except discord.HTTPException as e:
        if getattr(e, "code", None) in (40060, 10062):
            try:
                if getattr(interaction, "message", None):
                    return await interaction.message.edit(*args, **kwargs)
            except Exception:
                return None
            return None
        raise
    except discord.NotFound:
        return None
