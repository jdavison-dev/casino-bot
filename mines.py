import discord
import random
import asyncio

BOARD_SIZE = 5
TILE_COUNT = BOARD_SIZE * BOARD_SIZE

class MineTile(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(label="⬛", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y
        self.revealed = False

    async def callback(self, interaction: discord.Interaction):
        if self.view.game_over or self.revealed or interaction.user != self.view.player:
            return

        self.revealed = True
        index = self.y * BOARD_SIZE + self.x

        if index in self.view.bombs:
            self.style = discord.ButtonStyle.danger
            self.label = "💣"
            self.view.game_over = True
            self.view.reveal_mines()
            await interaction.response.edit_message(
                content=f"💥 You hit a mine! Game over, {interaction.user.mention}.", view=self.view
            )
        else:
            self.style = discord.ButtonStyle.success
            self.label = "✅"
            self.view.safe_reveals += 1
            self.view.multiplier = self.view.calculate_multiplier()
            await interaction.response.edit_message(content=f"{interaction.user.mention} - Type `cash out` to stop or keep playing!\n\t\t\t\t\t\t\t\t\t **Multiplier: x{self.view.multiplier}**", view=self.view)

class MinesView(discord.ui.View):
    def __init__(self, player, bet, mines, save_data):
        super().__init__(timeout=120)
        self.player = player
        self.bet = bet
        self.mines = mines
        self.game_over = False
        self.safe_reveals = 0
        self.multiplier = 1.0
        self.bombs = set(random.sample(range(TILE_COUNT), mines))
        self.save_data = lambda winnings: save_data(player.id, winnings)

        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                self.add_item(MineTile(x, y))

    def calculate_multiplier(self):
            total_tiles = TILE_COUNT
            safe_tiles_total = total_tiles - self.mines
            safe_left = safe_tiles_total - self.safe_reveals
            tiles_left = total_tiles - self.safe_reveals

            if safe_left <= 0 or tiles_left <= 0:
                return round(self.multiplier, 2) # No more
            
            # Probability of clicking a safe tile
            prob_safe = safe_left / tiles_left
            return round(self.multiplier * (1 / prob_safe), 2)
    
    # Function to reveal mines, will be used at the end of the game
    def reveal_mines(self):
        # Loop through each button
        for item in self.children:
            # If it is a mine tile, reveal it
            if isinstance(item, MineTile):
                index = item.y * BOARD_SIZE + item.x
                if index in self.bombs and not item.revealed:
                    item.style = discord.ButtonStyle.danger
                    item.label = "💣"
                    item.disabled = True
                elif not item.revealed:
                    item.disabled = True # Disable the rest of the tiles
    
async def play_mines(ctx, bet, mines, load_data, save_data, bot):
    user_id = str(ctx.author.id)
    data = load_data()
    if user_id not in data or data[user_id]["coins"] < bet:
        return await ctx.respond("You don't have enough coins!", ephemeral=True)

    data[user_id]["coins"] -= bet
    save_data(data)

    view = MinesView(ctx.author, bet, mines, lambda uid, winnings: update_balance(uid, winnings, load_data, save_data))

   # Respond to interaction and send actual message separately
    await ctx.defer()  # defer interaction response
    message = await ctx.followup.send(
        f"{ctx.author.mention} started a game of Mines! Click tiles or type `cash out` to stop.\n\t\t\t\t\t\t\t\t\t **Multiplier: x1.0**",
        view=view
    )

    # Wait for user messages with "cash out"
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "cash out"

    try:
        # Wait up to 120 seconds or until game is over
        while not view.game_over:
            msg = await bot.wait_for("message", check=check, timeout=120)
            if msg.content.lower() == "cash out" and not view.game_over:
                view.game_over = True
                view.reveal_mines()
                winnings = int(bet * view.multiplier)
                view.save_data(winnings)
                await msg.channel.send(f"🎉 {ctx.author.mention} cashed out for **{winnings} coins**! Thanks for playing!", delete_after=10)
                await message.edit(view=view)
    except asyncio.TimeoutError:
        if not view.game_over:
            view.game_over = True
            view.reveal_mines()
            await ctx.followup.send("⏰ Timeout! Game ended.")
            await message.edit(view=view)

# Update user balance
def update_balance(user_id, amount, load_data, save_data):
  data = load_data()
  user_id_str = str(user_id)
  if user_id_str not in data:
    data[user_id_str] = {"coins": 1000, "last_daily": "2000-01-01"} # Start with 1000 coins
  data[user_id_str]["coins"] = amount
  save_data(data)