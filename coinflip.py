import discord
import random
import asyncio

class OpenCoinFlipButtons(discord.ui.View):
    def __init__(self, challenger, bet, save_data, load_data):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.bet = bet
        self.accepted = False
        self.save_data = save_data
        self.load_data = load_data
        self.message = None # To set later

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass  # It was already deleted

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, button, interaction: discord.Interaction):
        if self.accepted:
            await interaction.response.send_message("⚠️ Someone already accepted this challenge!", ephemeral=True)
            return

        if interaction.user.id == self.challenger.id:
            await interaction.response.send_message("❌ You can't accept your own challenge!", ephemeral=True)
            return

        opponent = interaction.user

        # Lock in the first accepter
        self.accepted = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        # Coin flip animation
        # Assign heads/tails randomly
        sides = random.sample(["Heads", "Tails"], 2)
        assignments = {
            self.challenger: sides[0],
            opponent: sides[1]
        }

        # Announce who is heads/tails
        assignment_msg = (
            f"🪙 {self.challenger.mention} is **{assignments[self.challenger]}**\n"
            f"{opponent.mention} is **{assignments[opponent]}**\n\n"
            f"Flipping the coin..."
        )
        
        flip_message = await interaction.followup.send(assignment_msg, ephemeral=False)
        animation = ["🔃 Heads...", "🔃 Tails...", "🔃 Heads...", "🔃 Tails...", "🪙 Settling..."]
        for frame in animation:
            await asyncio.sleep(0.5)
            await flip_message.edit(content=f"{assignment_msg}\n{frame}")

        # Determine result of the flip
        flip_result = random.choice(["Heads", "Tails"])
        winner = next(player for player, side in assignments.items() if side == flip_result)
        loser = opponent if winner == self.challenger else self.challenger

        # Load and update balances
        data = self.load_data()
        for user in [self.challenger.id, opponent.id]:
            uid = str(user)
            if uid not in data:
                data[uid] = {"coins": 1000, "last_daily": "2000-01-01"}

        data[str(winner.id)]["coins"] += self.bet
        data[str(loser.id)]["coins"] -= self.bet
        self.save_data(data)

        await flip_message.edit(content=f"🪙 The coin lands... and **{winner.mention}** wins **{self.bet} coins**!")
        self.stop()

async def start_open_coinflip(ctx, bet: int, load_data, save_data):
    if bet <= 0:
        await ctx.respond("❌ Bet must be greater than 0.", ephemeral=True)
        return

    data = load_data()
    challenger_id = str(ctx.author.id)
    if challenger_id not in data:
        data[challenger_id] = {"coins": 1000, "last_daily": "2000-01-01"}

    if data[challenger_id]["coins"] < bet:
        await ctx.respond("❌ You don't have enough coins to place that bet.", ephemeral=True)
        return

    save_data(data)

    view = OpenCoinFlipButtons(ctx.author, bet, save_data, load_data)
    response = await ctx.respond(
        f"🪙 {ctx.author.mention} has created an open **{bet} coin** coin flip! First to accept joins the duel!",
        view=view
    )
    view.message = await response.original_response()