import math
import os
from datetime import datetime as dt
from datetime import timedelta

import discord
import pandas as pd
from discord.ext import commands

from .checks import *
from .members import match_member
from .utils import convert_args


class RaidCommands(commands.Cog):
    DATE_FORMAT = "%Y-%m-%d"

    def __init__(self, bot):
        self.bot = bot

    def get_file(self, latest: dt) -> str:
        """Gets the latest file before <latest>."""
        latest_file, latest_day = None, dt.min

        for file in os.listdir("./raids/"):
            name, ext = os.path.splitext(file)
            if ext != '.csv':
                continue

            day = dt.strptime(name, self.DATE_FORMAT)
            if latest >= day > latest_day:
                latest_file, latest_day = file, day

        if not latest_file:
            raise Exception("No valid season record found!")

        return './raids/' + latest_file

    def get_scores(self, day: dt) -> dict:
        """Gets the score for one particular day."""
        file = self.get_file(day)

        df = pd.read_csv(file, index_col='day', parse_dates=True)

        print(day, file, df.loc[day.strftime(self.DATE_FORMAT)])

        return df.loc[day.strftime(self.DATE_FORMAT)].to_dict()

    def get_diff(self, end: dt, start: dt = None) -> dict:
        """Gets the difference in scores between two days."""
        last = self.get_scores(end)
        if start:
            first = self.get_scores(start)
            keys = set(last.keys()) & set(first.keys())
            diff = {k: last[k] - first[k] for k in keys}
        else:
            diff = last

        diff = sorted(diff.items(), key=lambda x: float(x[1]), reverse=True)
        return {k: v for k, v in diff}

    def set_score(self, day: dt, name: str, score: float) -> None:
        """Sets the score for one cell."""
        file = self.get_file(day)

        df = pd.read_csv(file, index_col='day', parse_dates=True)
        daytime = day.strftime(self.DATE_FORMAT)

        if not (df.index == daytime).any():
            row = df.iloc[-1].copy()
            row.name = day.strftime(self.DATE_FORMAT)
            df = df.append(row)

        df.at[daytime, name] = score

        df.to_csv(file, date_format=self.DATE_FORMAT)

    async def get_dates(self, ctx, args):
        start, end = None, None
        if len(args) == 2:
            # Manually input 2 dates
            start, end = args

            try:
                start = dt.strptime(start, self.DATE_FORMAT)
            except ValueError:
                await ctx.send("Start date is invalid!")
                return
            try:
                end = dt.strptime(end, self.DATE_FORMAT)
            except ValueError:
                await ctx.send("End date is invalid!")
                return
        elif len(args) == 1:
            arg = args[0].lower()
            if arg in ['season', 's']:
                end = dt.utcnow() + timedelta(hours=10) - timedelta(hours=12)
                start = None
            elif arg in ['daily', 'day', 'd']:
                end = dt.utcnow() + timedelta(hours=10) - timedelta(hours=12)
                start = end - timedelta(days=1)
        return start, end

    @commands.command(aliases=['l'])
    @commands.check(check_channel(813005190767706161))
    async def log(self, ctx, *, args):
        name, score = '', None
        for arg in args.split():
            try:
                if arg.isdigit():
                    score = int(arg) / 100
                else:
                    score = float(arg)
                assert math.isfinite(score) and not math.isnan(score)
                break
            except (ValueError, AssertionError):
                name += arg
                score = None

        if name is None or score is None:
            await ctx.send("Invalid Syntax!")
            return

        names = match_member(name)
        if not names:
            await ctx.send("Member not found!")
            return

        if len(names) > 1:
            await ctx.send("Do something!")
            return

        name = names[0][0]

        daytime = dt.utcnow() + timedelta(hours=10)

        self.set_score(daytime, name, score)

        await ctx.message.add_reaction('✅')

    @commands.command()
    @commands.is_owner()
    async def new(self, ctx):
        with open("members.txt") as rf:
            mem = rf.read().split('\n')

        day = dt.now().strftime('%Y-%m-%d')
        with open(f"./raids/{day}.csv", "w") as wf:
            wf.write(','.join(mem) + '\n')
            wf.write(day + ',0' * len(mem))

        return

    @commands.command()
    @commands.is_owner()
    async def topm(self, ctx, *, args=''):
        args = args
        args = convert_args(args.split())
        start, end = await self.get_dates(ctx, args['_'][0] or 'd')

        if not end:
            await ctx.send('Invalid syntax!')
            return

        try:
            stats = self.get_diff(end, start)
        except Exception as e:
            await ctx.send(e.args[0])
            return

        if 'c' not in args:  # Comparison
            stat_str = '\n'.join(
                map(lambda t: f"{t[0] + 1:2}. "
                              f"{t[1][0]:<12} {float(t[1][1]):,.2f}M",
                    enumerate(stats.items())))

            await ctx.send(f"```\n{stat_str}\n```")
            return

        else:
            try:
                lastfile = self.get_file(end)
                lastday = dt.strptime(lastfile, "./raids/%Y-%m-%d.csv")
                diff = (dt.now() - lastday - timedelta(hours=12)).days

                statsc = self.get_diff(end - timedelta(days=21))
            except Exception as e:
                await ctx.send(e.args[0])
                return

            merged_stats = [(k, float(v), float(statsc[k]) / diff if
                            k in statsc else 0)
                            for k, v in stats.items()]
            print(stats, merged_stats)
            stat_str = '\n'.join(map(
                lambda t: f"{t[0] + 1:2}. "
                          f"{t[1][0]:<12} "
                          f"{t[1][1]:,.2f}M    "
                          f"{t[1][2]:,.2f}M    "
                          f"{100 * (t[1][1]/t[1][2]-1) if t[1][2] != 0 else 0:.0f}%",
                enumerate(merged_stats)))

            await ctx.send(f"```\n{stat_str}\n```")
            return

    @commands.command()
    @commands.check(check_channel(813005190767706161))
    async def top(self, ctx, *, args=''):
        args = args
        args = convert_args(args.split())
        start, end = await self.get_dates(ctx, args['_'][0] or 'd')

        if not end:
            await ctx.send('Invalid syntax!')
            return

        try:
            stats = self.get_diff(end, start)
        except Exception as e:
            await ctx.send(e.args[0])
            return

        names, scores = list(zip(*stats.items()))
        ranks = [f"{k + 1}. {v}" for k, v in enumerate(names)]
        scores = [f"{float(v):,.2f}M" for v in scores]

        embed = discord.Embed(title="Raid Leaderboard",
                              colour=0x23f9fc)

        embed.add_field(name="Rank", value='\n'.join(ranks))
        embed.add_field(name="Damage", value='\n'.join(scores))

        await ctx.send(embed=embed)
