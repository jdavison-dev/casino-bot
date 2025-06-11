import random
import asyncio

async def play_roulette(ctx, bet, choice, load_data, save_data):
  if bet <= 0:
    await ctx.respond("❌ Your bet must be greater than 0!", ephemeral=True)
    return

  valid_choices = ["red", "black", "green"]
  if choice.lower not in valid_choices:
    await ctx.respond(f"❌ Invalid choice! Please choose from {', '.join(valid_choices)}.", ephemeral=True)
    return

  user_id = str(ctx.author.id)
  data = load_data()
  user_data = data.get(user_id, {"coins": 0, "last_daily": "2000-01-01"})

  if user_data["coins"] < bet:
    await ctx.respond("❌ You don't have enough coins to make that bet!", ephemeral=True)
    return

  await ctx.defer()

  # Simulate the spinning!
  spin_message = await ctx.followup.send("🎡 Spinning the wheel...")
  await asyncio.sleep(1.5)

  number = random.randint(0, 36)
  color = "green" if number == 0 else ("red" if number % 2 == 0 else "black")

  result_message = f"🎯 The ball landed on **{number} ({color})**.\n"

  if choice.lower() == color:
    if color == "green":
      winnings = bet * 14
    else:
      winnings = bet * 2
    user_data["coins"] += winnings
    result_message += f"🎉 Congratulations! {ctx.author.mention} won **{winnings} coins**!"
  else:
    user_data["coins"] -= bet
    result_message += f"😔 Sorry, {ctx.author.mention} lost **{bet} coins**. Better luck next time!"

  data[user_id] = user_data
  save_data(data)

  await spin_message.edit(content=result_message)
  
