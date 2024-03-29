import redis

import discord
from discord.ext import commands

from lucid_bot import config
from lucid_bot.utils import Utils, LucidCommandResult
from lucid_bot.lucid_embed import lucid_embed


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = config.config
        self.utils = Utils
        self.redis = redis.Redis(
            host=self.config["redis"]["hostname"],
            port=self.config["redis"]["port"],
            db=self.config["redis"]["db"],
            decode_responses=True,
        )

    @commands.Cog.listener()
    async def on_connect(self) -> None:
        time = self.utils.time()
        print(f"\n{time}Bot connected to Discord.")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        botName = self.config["botName"]
        time = self.utils.time()
        print(f"\n{time}{botName} Bot ready.")
        print("-----------------------------")

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        time = self.utils.time()
        print("-----------------------------")
        print(f"\n{time}Bot disconnected.")

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        time = self.utils.time()
        print(
            f"{time}{ctx.author}::{ctx.author.id} did `{ctx.message.content}`"
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        repost_active = self.redis.hget(message.guild.id, "repostActive")

        if repost_active == "True":
            target_user = self.redis.hget(
                message.guild.id, "repostTargetUser"
            )

            channel_id = self.redis.hget(
                message.guild.id, "repostTargetChannel"
            )

            if (
                target_user is not None
                and channel_id is not None
                and int(target_user) == message.author.id
            ):

                await message.delete()

                channel = self.bot.get_channel(int(channel_id))
                await channel.send(message.content)

    @commands.Cog.listener()
    async def on_message_edit(
        self, before: discord.Message, after: discord.Message
    ) -> None:
        if self.redis.hget(before.guild.id, "editLogActive") == "True":
            embed = (
                lucid_embed()
                .set_author(
                    name=f"{before.author} edited their message",
                    url=before.jump_url,
                    icon_url=before.author.avatar_url,
                )
                .add_field(name="Before:", value=before.content)
                .add_field(name="After:", value=after.content, inline=False)
            )
            send_channel = self.redis.hget(before.guild.id, "logChannel")

            if send_channel is not None:
                channel = self.bot.get_channel(int(send_channel))
                await channel.send(embed=embed)

            else:
                await before.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if self.redis.hget(message.guild.id, "deleteLogActive") == "True":
            embed = (
                lucid_embed()
                .set_author(
                    name=f"{message.author} deleted their message",
                    url=message.jump_url,
                    icon_url=message.author.avatar_url,
                )
                .add_field(name="Message:", value=message.content)
            )
            send_channel = self.redis.hget(message.guild.id, "logChannel")

            if send_channel is not None:
                channel: discord.abc.GuildChannel = self.bot.get_channel(
                    int(send_channel)
                )
                await channel.send(embed=embed)

            else:
                await message.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if self.redis.hget(member.guild.id, "joinLeaveLogActive") == "True":
            log_channel = self.redis.hget(member.guild.id, "logChannel")

            if log_channel is not None:
                log_channel: discord.abc.GuildChannel = (
                    self.bot.get_channel(int(log_channel))
                )

                embed = lucid_embed(
                    description=f"{member.mention} joined."
                ).set_author(
                    name=f"Member #{len(member.guild.members) + 1}",
                    icon_url=member.avatar_url,
                )
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if self.redis.hget(member.guild.id, "joinLeaveLogActive") == "True":
            log_channel = self.redis.hget(member.guild.id, "logChannel")

            if log_channel is not None:
                log_channel: discord.abc.GuildChannel = (
                    self.bot.get_channel(int(log_channel))
                )

                embed = lucid_embed(
                    description=f"{member.mention} left."
                ).set_author(
                    name=f"Member #{len(member.guild.members) + 1}",
                    icon_url=member.avatar_url,
                )
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:

        if isinstance(error, commands.CommandNotFound):
            await ctx.message.add_reaction("❓")

        elif isinstance(error, commands.NotOwner):
            await self.utils.command_result(
                ctx, result=LucidCommandResult.FAIL
            )

        elif isinstance(error, commands.CheckFailure):
            await self.utils.command_result(
                ctx, result=LucidCommandResult.FAIL
            )

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.message.add_reaction("🕐")

        elif isinstance(error, commands.BadArgument):
            embed = lucid_embed(fail=True).set_author(
                name="Invalid argument(s)"
            )

            await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = lucid_embed(
                fail=True,
            ).set_author(name=f"Missing argument: {error.param}")

            await ctx.send(embed=embed)

        else:
            raise error


def setup(bot):
    bot.add_cog(Events(bot))
