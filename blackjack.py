import random
import discord
import asyncio

class Card:
  SUIT_EMOJIS = {
    "Hearts": "♥️",
    "Diamonds": "♦️",
    "Clubs": "♣️",
    "Spades": "♠️"
  }
  
  def __init__(self, rank, suit):
    self.rank = rank # 2-10, J, Q, K, A
    self.suit = suit

  def __str__(self):
    return f"{self.rank}{Card.SUIT_EMOJIS[self.suit]}"

class Deck:
  def __init__(self):
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    self.cards = [Card(rank, suit) for suit in suits for rank in ranks] # list of Card objects
    random.shuffle(self.cards)

  def deal_card(self):
    return self.cards.pop() # removes and returns the last card in the list


def calculate_score(hand):
  values = {
      "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
      "7": 7, "8": 8, "9": 9, "10": 10,
      "J": 10, "Q": 10, "K": 10, "A": 11  # Start counting Ace as 11 initially
  }

  score = 0
  ace_count = 0

  for card in hand:
      # Extract rank: the part before the last character (the suit)
    rank = card.rank
    score += values[rank]
    if rank == "A":
        ace_count += 1
  # Adjust for Aces if score is over 21
  while score > 21 and ace_count > 0:
      score -= 10  # Count one Ace as 1 instead of 11
      ace_count -= 1

  return score

# Helper function to format hand as string
def hand_str(hand, hide_first_card=False):
    if hide_first_card:
        return "`??` " + " ".join(str(card) for card in hand[1:])
    return " ".join(str(card) for card in hand)

    
# --- GAME LOGIC ---
async def play_blackjack(ctx, bet, bot, load_data, save_data):
    user_id = str(ctx.author.id)
    data = load_data()
    user_data = data.get(user_id, {"coins": 1000, "last_daily": "2000-01-01"})

    # Validate bet amount
    if bet <= 0:
        # Use ctx.respond here because we haven't deferred yet
        await ctx.respond("❌ Your bet must be greater than 0!", ephemeral=True)
        return
    if user_data["coins"] < bet:
        await ctx.respond("❌ You don't have enough coins to make that bet!", ephemeral=True)
        return

    # Defer interaction to acknowledge it and avoid 3-second timeout
    await ctx.defer()

    #Initialize game
    deck = Deck()
    player_hand = [deck.deal_card(), deck.deal_card()]
    dealer_hand = [deck.deal_card(), deck.deal_card()]

    player_score = calculate_score(player_hand)

    # Prepare initial game embed showing player's and dealer's cards (dealer's first card hidden)
    embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.gold())
    embed.add_field(name="Your Hand", value=f"{hand_str(player_hand)}\n**Score:** {player_score}", inline=False)
    embed.add_field(name="Dealer's Hand", value=hand_str(dealer_hand, hide_first_card=True), inline=False)

    # Send initial game state as a followup message (after defer)
    message = await ctx.followup.send(embed=embed)

    # --- Check for immediate blackjack ---
    if player_score == 21:
        await ctx.followup.send("Blackjack! Let's see what the dealer has...")
        await asyncio.sleep(1.5)
        dealer_score = calculate_score(dealer_hand)

        final_embed = discord.Embed(title="♠️ Final Results", color=discord.Color.gold())
        final_embed.add_field(name="Your Hand", value=f"{hand_str(player_hand)}\n**Score:** {player_score}", inline=False)
        final_embed.add_field(name="Dealer’s Hand", value=f"{hand_str(dealer_hand)}\n**Score:** {dealer_score}", inline=False)

        # Determine outcome if dealer also has blackjack
        if dealer_score == 21:
            result = "🤝 It's a tie! Both got blackjack."
        else:
            result = "🎉 Blackjack! You win!"
            user_data["coins"] += bet
        final_embed.add_field(name="Result", value=result, inline=False)

        await ctx.followup.send(embed=final_embed)
        data[user_id] = user_data
        save_data(data)
        return

    # --- Player's turn loop ---
    while True:
        # Prompt player to hit or stand
        await ctx.followup.send("✋ Type `hit` to draw or `stand` to hold.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["hit", "stand"]

        try:
            # Wait for player's message response for up to 30 seconds
            msg = await bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            # Timeout if no response
            await ctx.followup.send("⏰ Timeout! Game ended.")
            return

        if msg.content.lower() == "hit":
            # Player draws a card
            player_hand.append(deck.deal_card())
            player_score = calculate_score(player_hand)

            embed = discord.Embed(title="🃏 Blackjack - You Hit!", color=discord.Color.blue())
            embed.add_field(name="You Drew", value=str(player_hand[-1]), inline=False)
            embed.add_field(name="Your Hand", value=f"{hand_str(player_hand)}\n**Score:** {player_score}", inline=False)

            if player_score > 21:
                # Player busts
                embed.color = discord.Color.red()
                embed.add_field(name="💥 Bust!", value=f"You exceeded 21 and lost **{bet} coins**.", inline=False)
                await ctx.followup.send(embed=embed)
                user_data["coins"] -= bet
                data[user_id] = user_data
                save_data(data)
                return
            elif player_score == 21:
                # Player hits 21 exactly
                embed.color = discord.Color.green()
                embed.add_field(name="🎯 Blackjack!", value="You hit 21! Now it's the dealer's turn.", inline=False)
                await ctx.followup.send(embed=embed)
                break
            else:
                # Continue game, show current hand
                await ctx.followup.send(embed=embed)
        else:
            # Player stands, end turn loop
            break

    # --- Dealer's turn ---
    dealer_score = calculate_score(dealer_hand)
    dealer_embed = discord.Embed(
        title="🃏 Dealer's Turn",
        description=f"{hand_str(dealer_hand)}\n**Score**: {dealer_score}",
        color=discord.Color.red()
    )
    await ctx.followup.send(embed=dealer_embed)

    # Dealer hits while under 17
    while dealer_score < 17:
        await asyncio.sleep(1.5)
        new_card = deck.deal_card()
        dealer_hand.append(new_card)
        dealer_score = calculate_score(dealer_hand)

        hit_embed = discord.Embed(title="💥 Dealer Hits!", color=discord.Color.orange())
        hit_embed.add_field(name="New Card", value=str(new_card), inline=False)
        hit_embed.add_field(name="Dealer's Hand", value=hand_str(dealer_hand), inline=False)
        hit_embed.add_field(name="Score", value=str(dealer_score), inline=False)

        await ctx.followup.send(embed=hit_embed)

    # --- Determine winner and update coins ---
    if dealer_score > 21:
        await ctx.followup.send(f"Dealer busts with {dealer_score}! You win {bet} coins! 💰")
        user_data["coins"] += bet
    elif dealer_score > player_score:
        await ctx.followup.send(f"Dealer wins with {dealer_score} against your {player_score}. You lose {bet} coins.")
        user_data["coins"] -= bet
    elif dealer_score < player_score:
        await ctx.followup.send(f"You win with {player_score} against dealer's {dealer_score}! You gain {bet} coins! 💰")
        user_data["coins"] += bet
    else:
        await ctx.followup.send(f"It's a tie at {player_score}! Your bet is returned.")

    # Save updated user coin data
    data[user_id] = user_data
    save_data(data)