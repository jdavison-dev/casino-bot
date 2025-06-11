import discord
import os
import json
import datetime
import random
import asyncio
from discord.ext import commands # We want to be able to use commands
from dotenv import load_dotenv
from slots import play_slots
from blackjack import play_blackjack
from roulette import play_roulette


# Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Create a bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

ECONOMY_FILE = "economy.json"

# ---------------------------- CLASS DEFINITIONS ----------------------------


# ---------------------------- HELPER FUNCTIONS ----------------------------

# Helper function to load and save user data
def load_data():
  if not os.path.exists(ECONOMY_FILE):
    return {}
  with open(ECONOMY_FILE, "r") as f:
    return json.load(f)

def save_data(data):
  with open(ECONOMY_FILE, "w") as f:
    json.dump(data, f, indent=4)


# Get or create user balance
def get_balance(user_id):
  data = load_data()
  user_id_str = str(user_id)
  if user_id_str not in data:
    data[user_id_str] = {"coins": 1000, "last_daily": "2000-01-01"} # Start with 1000 coins
    save_data(data)
  return data[user_id_str]["coins"]

# Update user balance
def update_balance(user_id, amount):
  data = load_data()
  user_id_str = str(user_id)
  if user_id_str not in data:
    data[user_id_str] = {"coins": 1000, "last_daily": "2000-01-01"} # Start with 1000 coins
  data[user_id_str]["coins"] = amount
  save_data(data)

# ---------------------------- GENERAL COMMANDS ----------------------------

# Command: !balance
@bot.command()
async def balance(ctx):
  bal = get_balance(ctx.author.id)
  await ctx.send(f"💰 {ctx.author.mention}, you have **{bal} coins**!")
  
#Command: !daily
@bot.command()
async def daily(ctx):
  user_id = str(ctx.author.id)
  data = load_data()

  today = datetime.date.today().isoformat()
  user_data = data.get(user_id, {"coins": 0, "last_daily": "2000-01-01"})

  if user_data["last_daily"] == today:
    await ctx.send(f"❌{ctx.author.mention}, you've already claimed your daily coins today!")
  else:
    user_data["coins"] += 100 # Daily reward
    user_data["last_daily"] = today
    data[user_id] = user_data
    save_data(data)
    await ctx.send(f"💰 {ctx.author.mention}, you've claimed your daily coins! You now have **{user_data['coins']} coins**!")

# Command: !leaderboard
@bot.command()
async def leaderboard(ctx):
  data = load_data()
  if not data:
    await ctx.send("❌ No data found yet!")
    return

# Convert to list of tuples, (user_id, coins)
  leaderboard_data = []
  for user_id, user_data in data.items():
    # Skip if user_data is an int 
    if isinstance(user_data, dict) and "coins" in user_data:
      leaderboard_data.append((user_id, user_data["coins"]))

  # Sort by coins descending
  leaderboard_data.sort(key=lambda x: x[1], reverse=True)

  # Limit to top 10
  top_10 = leaderboard_data[:10]

  # Format the message
  message = ["🏆 **Top Coin Holders** 🏆"]
  for i, (user_id, coins) in enumerate(top_10, start=1):
    user = await bot.fetch_user(int(user_id))
    name = user.name if user else f"User {user_id}"
    message.append(f"**#{i}** - {name}: **{coins} coins**")

  await ctx.send("\n".join(message))

# ---------------------------- GAME COMMANDS - See Respective .py Files ----------------------------

# ---------- Command: !slots <bet> ----------
@bot.slash_command(name="slots", description="Bet on slots!")
async def slots(
  ctx: discord.ApplicationContext,
  bet: int
):
  await play_slots(ctx, bet, load_data, save_data)
    
# ---------- END SLOTS COMMAND ----------


# ---------- Command: !blackjack <bet> ----------
@bot.slash_command(name="blackjack", description="Play blackjack!")
async def blackjack(ctx, bet: int):
  await play_blackjack(ctx, bet, bot, load_data, save_data)
  
# ---------- END BLACKJACK COMMAND ----------

# ---------- Command: !roulette <bet> <color choice> ----------
@bot.slash_command(name="roulette", description="Bet coins on red, black, or green.")
async def roulette(ctx, bet: int, choice: str):
  await play_roulette(ctx, bet, choice, load_data, save_data)

# ---------- END ROULETTE COMMAND ----------



# When bot is good to go
@bot.event
async def on_ready():
  print(f"{bot.user} is ready and online!")

# Run the bot
if not TOKEN:
  raise ValueError("DISCORD_TOKEN not found in .env file.")
  
bot.run(TOKEN)