import redis

import discord
from discord.ext import commands

from lucid_bot import config
from lucid_bot.utils import Utils, LucidCommandResult
from lucid_bot.lucid_embed import lucid_embed


class Repost(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.utils = Utils
        self.config = config.config
        self.redis = redis.Redis(
            host=self.config["redis"]["hostname"],
            port=self.config["redis"]["port"],
            db=self.config["redis"]["db"],
            decode_responses=True,
        )

    @commands.group(name="repost", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def _repost(self, ctx: commands.Context) -> None:
        embed = (
            lucid_embed(ctx, title="Chat Reposter Status: ")
            .add_field(
                name="Active:",
                value=self.redis.hget(ctx.guild.id, "repostActive"),
            )
            .add_field(
                name="Target User:",
                value=self.redis.hget(ctx.guild.id, "repostTargetUser"),
                inline=False,
            )
            .add_field(
                name="Target Channel:",
                value=self.redis.hget(ctx.guild.id, "repostTargetChannel"),
                inline=False,
            )
        )
        await ctx.send(embed=embed)

    @_repost.command(name="activate")
    async def _repost_activate(self, ctx: commands.Context) -> None:
        self.redis.hmset(ctx.guild.id, {"repostActive": "True"})
        await self.utils.command_result(ctx, result=LucidCommandResult.SUCCESS)

    @_repost.command(name="deactivate")
    async def _repost_deactivate(self, ctx: commands.Context) -> None:
        self.redis.hmset(ctx.guild.id, {"repostActive": "False"})
        await self.utils.command_result(ctx, result=LucidCommandResult.SUCCESS)

    @_repost.command(name="user")
    async def _repost_user(self, ctx: commands.Context, user_id: int) -> None:
        try:
            await self.bot.fetch_user(user_id)

        except (discord.NotFound, discord.HTTPException):
            await ctx.send(f"User with ID {user_id} could not be found.")
            return

        self.redis.hmset(ctx.guild.id, {"repostTargetUser": int(user_id)})
        await self.utils.command_result(ctx, result=LucidCommandResult.SUCCESS)

    @_repost.command(name="channel")
    async def _repost_channel(self, ctx: commands.Context, channel_id: int) -> None:
        try:
            self.bot.get_channel(channel_id)

        except (discord.NotFound, discord.HTTPException):
            await ctx.send(f"Channel with ID {channel_id} could not be found.")
            return

        self.redis.hmset(ctx.guild.id, {"repostTargetChannel": int(channel_id)})
        await self.utils.command_result(ctx, result=LucidCommandResult.SUCCESS)


def setup(bot):
    bot.add_cog(Repost(bot))
