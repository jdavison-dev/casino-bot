import discord
import random
import asyncio

class CrashView(discord.ui.View):
    def __init__(self, player, bet, save_data):
        super().__init__(timeout=60)  # View timeout after 60 seconds
        self.player = player          # Player who started the game
        self.bet = bet                # Amount bet by the player
        self.save_data = save_data    # Function to save winnings
        self.multiplier = 1.0         # Starting multiplier
        self.crashed = False          # Flag if the game has crashed
        self.cashout = False          # Flag if player cashed out

        # Create a "Cash Out" button and add to the view
        self.cashout_button = discord.ui.Button(label="Cash Out", style=discord.ButtonStyle.green)
        self.cashout_button.callback = self.cashout_callback
        self.add_item(self.cashout_button)

    async def cashout_callback(self, interaction: discord.Interaction):
        # Only allow the original player to cash out and if game not ended
        if interaction.user != self.player or self.crashed or self.cashout:
            await interaction.response.defer()  # Ignore other users or late clicks gracefully
            return

        self.cashout = True  # Mark as cashed out

        # Calculate winnings based on current multiplier and bet
        winnings = int(self.bet * self.multiplier)

        # Save the winnings using provided save_data function
        self.save_data(winnings)

        # Disable the cashout button to prevent further clicks
        self.cashout_button.disabled = True

        # Update the message to show cashout info
        await interaction.response.edit_message(
            content=f"💰 {interaction.user.mention} cashed out at x{self.multiplier:.2f} for {winnings} coins!",
            view=self
        )

async def play_crash(ctx, bet, load_data, save_data):
    user_id = str(ctx.author.id)
    data = load_data()

    # Check if user has enough coins to bet
    if user_id not in data or data[user_id]["coins"] < bet:
        return await ctx.respond("You don't have enough coins!", ephemeral=True)
    
    # Deduct the bet from user's coins
    data[user_id]["coins"] -= bet
    save_data(data)

    # Create the Crash game UI view for this player and bet
    view = CrashView(ctx.author, bet, lambda winnings: update_balance(user_id, winnings, load_data, save_data))
    # Defer response to allow sending a followup message later
    await ctx.defer()

    # Send the initial game message with multiplier and buttons

    message = await ctx.followup.send(f"Crash game started! Multiplier: x1.00", view=view)
    await asyncio.sleep(0.7)

    # Randomly choose a crash multiplier between 1.02x and 20.0x
    crash_point = random.uniform(1.02, 20.0)

    # Main game loop: increment multiplier until crash or cashout
    while not view.crashed and not view.cashout:
        await asyncio.sleep(0.1)  # Wait 0.2 seconds between multiplier increases
        view.multiplier += 0.01    # Increase multiplier smoothly

        if view.multiplier >= crash_point:
            # Crash condition met — game ends with loss
            view.crashed = True
            view.cashout_button.disabled = True  # Disable cashout button
            await message.edit(
                content=f"💥 Crash! Multiplier reached x{crash_point:.2f}. You lost your bet.",
                view=view
            )
        else:
            # Update message with new multiplier while game ongoing
            await message.edit(
                content=f"# Multiplier: x{view.multiplier:.2f}",
                view=view
            )

def update_balance(user_id, winnings, load_data, save_data):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"coins": 1000, "last_daily": "2000-01-01"}
    data[user_id]["coins"] += winnings
    save_data(data)