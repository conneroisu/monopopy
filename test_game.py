#!/usr/bin/env python3
"""Test script for Monopoly game functionality"""

import random
from main import MonopolyGame, PropertyColor


def test_basic_game_setup():
    """Test that the game initializes correctly"""
    print("Testing game setup...")

    game = MonopolyGame(["Alice", "Bob"])
    assert len(game.players) == 2
    assert game.players[0].name == "Alice"
    assert game.players[0].money == 1500
    assert game.players[0].position == 0

    # Test board setup
    assert len(game.board_spaces) == 40
    assert game.board_spaces[0].name == "GO"
    assert game.board_spaces[1].name == "Mediterranean Avenue"
    assert game.board_spaces[39].name == "Boardwalk"

    print("✅ Game setup tests passed!")


def test_property_rent_calculation():
    """Test rent calculation for different property types"""
    print("Testing rent calculations...")

    game = MonopolyGame(["Alice", "Bob"])
    alice, bob = game.players

    # Test basic property rent
    mediterranean = game.board_spaces[1].property  # Mediterranean Avenue
    mediterranean.owner = alice
    alice.properties.append(mediterranean)

    # Test base rent (no monopoly)
    rent = mediterranean.get_rent_amount()
    assert rent == 2  # Base rent for Mediterranean

    # Test monopoly rent (own both brown properties)
    baltic = game.board_spaces[3].property  # Baltic Avenue
    baltic.owner = alice
    alice.properties.append(baltic)

    rent = mediterranean.get_rent_amount()
    assert rent == 4  # Monopoly rent for Mediterranean

    # Test railroad rent
    reading_railroad = game.board_spaces[5].property
    reading_railroad.owner = alice
    alice.properties.append(reading_railroad)

    rent = reading_railroad.get_rent_amount()
    assert rent == 25  # One railroad

    print("✅ Rent calculation tests passed!")


def test_player_movement():
    """Test player movement around the board"""
    print("Testing player movement...")

    game = MonopolyGame(["Alice", "Bob"])
    alice = game.players[0]

    # Test normal movement
    alice.position = 35
    old_money = alice.money

    # Simulate moving 8 spaces (would pass GO)
    dice_sum = 8
    old_position = alice.position
    alice.position = (alice.position + dice_sum) % 40

    # Check if passed GO
    if alice.position < old_position:
        alice.receive(200)
        assert alice.money == old_money + 200

    assert alice.position == 3  # 35 + 8 = 43, 43 % 40 = 3

    print("✅ Player movement tests passed!")


def test_monopoly_detection():
    """Test monopoly ownership detection"""
    print("Testing monopoly detection...")

    game = MonopolyGame(["Alice", "Bob"])
    alice = game.players[0]

    # Test brown monopoly (2 properties)
    mediterranean = game.board_spaces[1].property
    baltic = game.board_spaces[3].property

    mediterranean.owner = alice
    alice.properties.append(mediterranean)
    assert not alice.owns_monopoly(PropertyColor.BROWN)

    baltic.owner = alice
    alice.properties.append(baltic)
    assert alice.owns_monopoly(PropertyColor.BROWN)

    print("✅ Monopoly detection tests passed!")


def test_chance_and_community_chest():
    """Test card deck functionality"""
    print("Testing card decks...")

    game = MonopolyGame(["Alice", "Bob"])

    # Check that cards are shuffled and available
    assert len(game.chance_cards) == 16
    assert len(game.community_chest_cards) == 16

    # Test drawing cards (just test the deck functionality, not the interactive parts)
    original_chance_count = len(game.chance_cards)

    # Test simple card drawing without triggering interactive prompts
    card = game.chance_cards.pop()
    assert len(game.chance_cards) == original_chance_count - 1
    assert isinstance(card, str)

    # Test that cards are properly initialized
    assert any("Get Out of Jail Free" in card for card in game.chance_cards + [card])
    assert any("Advance to Go" in card for card in game.community_chest_cards)

    print("✅ Card deck tests passed!")


def run_all_tests():
    """Run all test functions"""
    print("Running Monopoly game tests...\n")

    test_basic_game_setup()
    test_property_rent_calculation()
    test_player_movement()
    test_monopoly_detection()
    test_chance_and_community_chest()

    print(
        "\n🎉 All tests passed! The Monopoly game implementation is working correctly."
    )


def demo_game_turn():
    """Demonstrate a few turns of the game"""
    print("\n" + "=" * 50)
    print("DEMO: Sample Game Turn")
    print("=" * 50)

    # Set a fixed seed for reproducible demo
    random.seed(42)

    game = MonopolyGame(["Alice", "Bob"])
    alice, bob = game.players

    print(
        f"Starting game with {alice.name} (${alice.money}) and {bob.name} (${bob.money})"
    )

    # Simulate a few moves
    for turn in range(6):
        current_player = game.get_current_player()
        print(f"\nTurn {turn + 1}: {current_player.name}'s turn")
        print(f"Position: {current_player.position}, Money: ${current_player.money}")

        # Simulate dice roll
        die1, die2 = random.randint(1, 6), random.randint(1, 6)
        dice_sum = die1 + die2

        print(f"Rolled: {die1} + {die2} = {dice_sum}")

        # Move player
        old_position = current_player.position
        current_player.position = (current_player.position + dice_sum) % 40

        # Check if passed GO
        if current_player.position < old_position:
            current_player.receive(200)
            print("Passed GO! Collect $200")

        current_space = game.board_spaces[current_player.position]
        print(f"Landed on: {current_space.name}")

        # Simulate basic property purchase
        if (
            current_space.property
            and current_space.property.owner is None
            and current_player.can_afford(current_space.property.price)
        ):
            current_player.pay(current_space.property.price)
            current_space.property.owner = current_player
            current_player.properties.append(current_space.property)
            print(
                f"Bought {current_space.property.name} for ${current_space.property.price}"
            )

        game.next_turn()

    print("\nFinal status:")
    for player in game.players:
        props = len(player.properties)
        wealth = player.total_wealth()
        print(
            f"{player.name}: ${player.money} cash, {props} properties, ${wealth} total wealth"
        )


if __name__ == "__main__":
    run_all_tests()
    demo_game_turn()
