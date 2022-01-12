import random
from typing import List, Optional

from discord import ApplicationContext, Option

from ..bot import DiscordBot, SlashCommand


def format_result(word: str, correct_pos: List[bool], correct_letter: List[bool]):
    formatted = []
    for index, letter in enumerate(word):
        if correct_pos[index]:
            formatted.append(f"**{letter}**")
        elif correct_letter[index]:
            formatted.append(f"__{letter}__")
        else:
            formatted.append(letter)

    # join with zwsp
    return '\u200b'.join(formatted)


class WordGame:
    def __init__(self, channel_id: int, guesses: int):
        self.channel_id = channel_id

        self.guesses_remain = guesses

        with open("candidate-words.txt") as f:
            words = f.read().split('\n')
            self.target = random.choice(words)

    def guess(self, guess: str):
        # Check if word is in dict
        with open("words.txt") as f:
            words = f.read().split('\n')
            if guess not in words:
                return

        # Check for letters in correct positions
        correct_pos = [x == y for x, y in zip(guess, self.target)]

        # Check for letters in incorrect positions
        correct_letter = [False] * 5
        remaining_target = [x for b, x in zip(correct_pos, self.target) if not b]
        remaining_guess = [x for b, x in zip(correct_pos, enumerate(guess)) if not b]

        for index, letter in remaining_guess:
            if letter in remaining_target:
                correct_letter[index] = True
                remaining_target.remove(letter)

        self.guesses_remain -= 1

        if all(correct_pos):
            status = 1  # win
        elif self.guesses_remain == 0:
            status = -1  # loss
        else:
            status = 0

        return status, format_result(guess, correct_pos, correct_letter)


class WordGameCommand(SlashCommand, name="word"):
    def __init__(self, bot: DiscordBot, guild_ids: List[int]):
        super().__init__(bot, guild_ids)

        self.group = bot.bot.command_group(
            "word", "No Description", guild_ids=self.guild_ids
        )

        self.game: Optional[WordGame] = None

        self.group.command()(self.start)
        self.group.command()(self.guess)

    async def start(self, ctx: ApplicationContext,
                    guesses: Option(int, "how many guesses", required=False) = 6):
        """Starts a word game."""
        # if self.game is not None:
        #     await ctx.respond("Game in progress.")
        self.game = WordGame(ctx.channel_id, guesses)
        await ctx.respond("Game started. Good luck!")

    async def guess(self, ctx: ApplicationContext,
                    guess: Option(str, "guess a word")):
        """Makes a guess for the current ongoing word game"""
        # Just a bunch of error handling
        if not self.game:
            await ctx.respond("A word game does not exist! Use `/word start` to create one.")
            return

        if ctx.channel_id != self.game.channel_id:
            await ctx.respond("You must use this command in the same channel as where the game was created.")
            return

        if len(guess) != 5:
            await ctx.respond("You must guess a valid 5 letter word!")
            return

        if not (result := self.game.guess(guess)):
            await ctx.respond("Invalid Guess!")
            return
        else:
            status, guess = result
            if status == 1:  # win
                await ctx.respond(f"Congratulations, you found the word {guess}!")
                self.game = None
            elif status == 0:  # still playing
                await ctx.respond(f"{guess}    Remaining Guess(es): {self.game.guesses_remain}")
            elif status == -1:  # lost
                await ctx.respond(f"You ran out of guesses \\:( The word was {self.game.target}")
                self.game = None
