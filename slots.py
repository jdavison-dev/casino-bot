import random
import asyncio

async def play_slots(ctx, bet, load_data, save_data):
    # Validate bet
    if bet <= 0:
        await ctx.respond("❌ Your bet must be greater than 0!", ephemeral=True)
        return

    user_id = str(ctx.author.id)
    data = load_data()
    user_data = data.get(user_id, {"coins": 0, "last_daily": "2000-01-01"})

    if user_data["coins"] < bet:
        await ctx.respond("❌ You don't have enough coins to make that bet!", ephemeral=True)
        return

    # Defer the response to avoid timeout
    await ctx.defer()

    symbols = ["🍒", "🍋", "🔔", "💎", "7️⃣"]

    # Send initial spinning message as a followup (after defer, ctx.respond is already "deferred")
    spinning_message = await ctx.followup.send("🎰    Spinning...    🎰")

    for _ in range(3):
        spin_symbols = [random.choice(symbols) for _ in range(3)]
        await spinning_message.edit(content="🎰    " + " | ".join(spin_symbols) + "    🎰")
        await asyncio.sleep(0.5)

    # Determine winnings
    result = [random.choice(symbols) for _ in range(3)]
    slot_display = " | ".join(result)

    if result[0] == result[1] == result[2]:
        winnings = bet * 5
        user_data["coins"] += winnings
        message = f"🎰    {slot_display}    🎰\nJACKPOT! {ctx.author.mention} won {winnings} coins!"
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        winnings = int(bet * 1.5)
        user_data["coins"] += winnings
        message = f"🎰    {slot_display}    🎰\n{ctx.author.mention} won {winnings} coins!"
    else:
        user_data["coins"] -= bet
        message = f"🎰    {slot_display}    🎰\nNo match. {ctx.author.mention} lost {bet} coins!"

    data[user_id] = user_data
    save_data(data)

    await spinning_message.edit(content=message)