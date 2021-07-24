import csv

import requests
from discord.ext import commands


class WeatherCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def weather(self, ctx, *, city):
        with open('worldcities.csv') as cityrf:
            cityrr = csv.reader(cityrf)
            iso = None
            for row in cityrr:
                if city.lower() == row[0].lower():
                    city, iso, _ = row
                    break
            if not iso:
                await ctx.send("City not found!")
                return

            req = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?"
                f"q={city},{iso}&"
                f"appid=fbf244c17e012be8ed3c43c8f7177c92").json()

            await ctx.send(f"The weather in {city}, {iso} is "
                           f"{req['weather'][0]['description']}, with a "
                           f"minimum of {req['main']['temp_min'] - 273.15:.2f}"
                           f" and a maximum of "
                           f"{req['main']['temp_max'] - 273.15:.2f}.")
