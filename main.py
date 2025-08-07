import discord
import os
import json
import datetime
import random
import asyncio
from flask import Flask
from threading import Thread
from discord.ext import commands # We want to be able to use commands
from dotenv import load_dotenv
from slots import play_slots
from blackjack import play_blackjack
from roulette import play_roulette
from coinflip import start_open_coinflip
from mines import play_mines
from crash import play_crash


# Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Create a bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

ECONOMY_FILE = "economy.json"

# Creating a flask server instance
app = Flask('') # using default name

# Define a route (web page) for the root URL
@app.route('/')
def home():
  return "I'm alive" # This shows up when you go to the web page

# Define a function to run the Flask app
def run():
  app.run(host='0.0.0.0', port=8080)

# Define a function to keep the Flask app alive
def keep_alive():
  # Create and start a thread to run the Flask app
  t = Thread(target=run)
  t.start()

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
@bot.slash_command(name="balance", description="Check your balance")
async def balance(ctx):
  bal = get_balance(ctx.author.id)
  await ctx.respond(f"💰 {ctx.author.mention}, you have **{bal} coins**!")
  
#Command: !daily
@bot.slash_command(name="daily", description="Claim your daily coins!")
async def daily(ctx):
    user_id = str(ctx.author.id)
    data = load_data()

    today = datetime.date.today().isoformat()
    user_data = data.get(user_id, {"coins": 1000, "last_daily": "2000-01-01"})

    if user_id not in data:
        data[user_id] = user_data  # save the initial 1000 coins
        save_data(data)

    if user_data["last_daily"] == today:
        await ctx.respond(f"❌ {ctx.author.mention}, you've already claimed your daily coins today!")
    else:
        user_data["coins"] += 100
        user_data["last_daily"] = today
        data[user_id] = user_data
        save_data(data)
        await ctx.respond(f"💰 {ctx.author.mention}, you've claimed your daily coins! You now have **{user_data['coins']} coins**!")

# Command: !leaderboard
@bot.slash_command(name="leaderboard", description="View the top coin holders!")
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

  await ctx.respond("\n".join(message))

# ---------------------------- GAME COMMANDS - See Respective .py Files ----------------------------

# ---------- Command: /slots <bet> ----------
@bot.slash_command(name="slots", description="Bet on slots!")
async def slots(
  ctx: discord.ApplicationContext,
  bet: int
):
  await play_slots(ctx, bet, load_data, save_data)
    
# ---------- END SLOTS COMMAND ----------


# ---------- Command: /blackjack <bet> ----------
@bot.slash_command(name="blackjack", description="Play blackjack!")
async def blackjack(ctx, bet: int):
  await play_blackjack(ctx, bet, bot, load_data, save_data)
  
# ---------- END BLACKJACK COMMAND ----------

# ---------- Command: /roulette <bet> <color choice> ----------
@bot.slash_command(name="roulette", description="Bet coins on red, black, or green.")
async def roulette(ctx, bet: int, choice: str):
  await play_roulette(ctx, bet, choice, load_data, save_data)

# ---------- END ROULETTE COMMAND ----------

# ---------- Command: /cf <bet> ----------
@bot.slash_command(name="cf", description="Open coin flip challenge!")
async def coinflip(ctx: discord.ApplicationContext, bet: int):
  await start_open_coinflip(ctx, bet, load_data, save_data)

# ---------- END COINFLIP COMMAND ----------

# ---------- Command: /mines <mines> <bet> ----------
@bot.slash_command(name="mines", description="Play a game of Mines!")
async def mines(ctx, bet: int, mines: int):
  await play_mines(ctx, bet, mines, load_data, save_data, bot)
# ---------- END MINES COMMAND ----------

# ---------- Command: /crash <bet> ----------
@bot.slash_command(name="crash", description="Play Crash!")
async def crash(ctx, bet: int):
  await play_crash(ctx, bet, load_data, save_data)
# ---------- END CRASH COMMAND ----------

# When bot is good to go
@bot.event
async def on_ready():
  print(f"{bot.user} is ready and online!")
  await bot.sync_commands()
  
# Run the bot
if not TOKEN:
  raise ValueError("DISCORD_TOKEN not found in .env file.")

keep_alive()
bot.run(TOKEN)