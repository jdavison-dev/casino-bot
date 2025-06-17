import random
import asyncio

async def play_roulette(ctx, bet, choice, load_data, save_data):
  if bet <= 0:
      await ctx.respond("❌ Your bet must be greater than 0!", ephemeral=True)
      return

  valid_choices = ["red", "black", "green"]
  if choice.lower() not in valid_choices:
      await ctx.respond(f"❌ Invalid choice! Please choose from {', '.join(valid_choices)}.", ephemeral=True)
      return

  user_id = str(ctx.author.id)
  data = load_data()
  user_data = data.get(user_id, {"coins": 0, "last_daily": "2000-01-01"})

  if user_data["coins"] < bet:
      await ctx.respond("❌ You don't have enough coins to make that bet!", ephemeral=True)
      return

  await ctx.defer()

  # Create an alternating red/black wheel with one green
  wheel = []
  for i in range(36):
      wheel.append("🔴" if i % 2 == 0 else "⚫")
  green_index = random.randint(0, len(wheel))
  wheel.insert(green_index, "🟢")  # Add one green spot

  spin_message = await ctx.followup.send("🎡 Spinning the wheel...")

  # Simulate a spinning animation with slowing speed
  final_window = []
  for i in range(20):
      window = wheel[:9]
      display_line = " ".join(window)
      arrow_line = "ㅤㅤ" * 4 + "⬇️"
      await spin_message.edit(content=f"{arrow_line}\n🎡 {display_line} 🎡")
      await asyncio.sleep(0.05 + i * 0.03)
      wheel = wheel[1:] + [wheel[0]]
      final_window = window  # Save this BEFORE the final rotation
    

  await asyncio.sleep(0.3)

  # Final result: middle symbol
  final_emoji = final_window[4]
  if final_emoji == "🔴":
      color = "red"
  elif final_emoji == "⚫":
      color = "black"
  else:
      color = "green"

  number = random.randint(0, 36 if color != "green" else 0)
  result_message = f"🎯 The ball landed on **{number} ({color})** {final_emoji}\n"

  if choice.lower() == color:
      winnings = bet * 14 if color == "green" else bet * 2
      user_data["coins"] += winnings
      result_message += f"🎉 {ctx.author.mention} won **{winnings} coins**!"
  else:
      user_data["coins"] -= bet
      result_message += f"😔 {ctx.author.mention} lost **{bet} coins**."

  data[user_id] = user_data
  save_data(data)

  await spin_message.edit(content=result_message)
  
