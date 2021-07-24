import aiocron
from pytz import utc


class Cron:
    def __init__(self, bot):
        self.channel = bot.Vege.get_channel(852735821647052830)
        self.mention = bot.Vege.get_role(852730229448769536).mention

        self.lunch().start()
        self.mail().start()
        self.night().start()
        self.before_reset().start()

    def lunch(self):
        @aiocron.crontab("0 2 * * *", start=False, tz=utc)
        async def wrapper():
            await self.channel.send(f"{self.mention} Lunch Arena has started! "
                                    f"Also don't forget to check your "
                                    f"mail for 50 stamina!")

        return wrapper

    def mail(self):
        @aiocron.crontab("0 9 * * *", start=False, tz=utc)
        async def wrapper():
            await self.channel.send(f"{self.mention} Mail has arrived! "
                                    f"Claim your free gems and stamina!")

        return wrapper

    def night(self):
        @aiocron.crontab("0 11 * * *", start=False, tz=utc)
        async def wrapper():
            await self.channel.send(f"{self.mention} Night Arena has started!")

        return wrapper

    def before_reset(self):
        @aiocron.crontab("50 13 * * *", start=False, tz=utc)
        async def wrapper():
            await self.channel.send(f"{self.mention} 10 minutes before reset! "
                                    f"Check that you have done your raid and "
                                    f"daily quests!")

        return wrapper