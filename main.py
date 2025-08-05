#!/usr/bin/env python3
"""
Monopoly TUI Game - Complete implementation with rich interface

A complete Monopoly game implementation following Tiger Style principles:
- Safety: Explicit bounds, clear error handling, predictable control flow
- Performance: Efficient data structures, minimal allocations
- Developer Experience: Clear naming, logical organization, documentation
"""

import random
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table


class PropertyColor(Enum):
    BROWN = auto()
    LIGHT_BLUE = auto()
    PINK = auto()
    ORANGE = auto()
    RED = auto()
    YELLOW = auto()
    GREEN = auto()
    DARK_BLUE = auto()
    RAILROAD = auto()
    UTILITY = auto()


class SpaceType(Enum):
    PROPERTY = auto()
    RAILROAD = auto()
    UTILITY = auto()
    TAX = auto()
    CHANCE = auto()
    COMMUNITY_CHEST = auto()
    GO = auto()
    JAIL = auto()
    GO_TO_JAIL = auto()
    FREE_PARKING = auto()


@dataclass
class Property:
    name: str
    color: PropertyColor
    price: int
    rent_base: int
    rent_with_set: int
    house_cost: int
    rent_1_house: int
    rent_2_house: int
    rent_3_house: int
    rent_4_house: int
    rent_hotel: int
    mortgage_value: int
    houses: int = 0
    is_mortgaged: bool = False
    owner: Optional["Player"] = None

    def get_rent_amount(self, dice_sum: int = 0) -> int:
        if self.is_mortgaged or self.owner is None:
            return 0

        if self.color == PropertyColor.UTILITY:
            multiplier = 10 if dice_sum > 0 else 4
            utilities_owned_count = sum(
                1
                for prop in self.owner.properties
                if prop.color == PropertyColor.UTILITY
            )
            return dice_sum * multiplier if utilities_owned_count == 2 else dice_sum * 4

        if self.color == PropertyColor.RAILROAD:
            railroads_owned_count = sum(
                1
                for prop in self.owner.properties
                if prop.color == PropertyColor.RAILROAD
            )
            return 25 * (2 ** (railroads_owned_count - 1))

        owns_monopoly = self.owner.owns_monopoly(self.color)

        if self.houses == 0:
            return self.rent_with_set if owns_monopoly else self.rent_base
        elif self.houses == 1:
            return self.rent_1_house
        elif self.houses == 2:
            return self.rent_2_house
        elif self.houses == 3:
            return self.rent_3_house
        elif self.houses == 4:
            return self.rent_4_house
        elif self.houses == 5:  # Hotel
            return self.rent_hotel

        return self.rent_base


@dataclass
class BoardSpace:
    position: int
    name: str
    space_type: SpaceType
    property: Optional[Property] = None
    tax_amount: int = 0


@dataclass
class Player:
    name: str
    position: int = 0
    money: int = 1500
    properties: List[Property] = field(default_factory=list)
    jail_turns: int = 0
    get_out_of_jail_free_cards: int = 0
    is_bankrupt: bool = False

    def owns_monopoly(self, color: PropertyColor) -> bool:
        color_properties = [
            p for p in self.properties if p.color == color and not p.is_mortgaged
        ]

        if color == PropertyColor.BROWN or color == PropertyColor.DARK_BLUE:
            return len(color_properties) == 2
        elif color == PropertyColor.RAILROAD:
            return len(color_properties) == 4
        elif color == PropertyColor.UTILITY:
            return len(color_properties) == 2
        else:
            return len(color_properties) == 3

    def can_afford(self, amount: int) -> bool:
        return self.money >= amount

    def pay(self, amount: int) -> bool:
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    def receive(self, amount: int):
        self.money += amount

    def total_wealth(self) -> int:
        property_value = sum(
            prop.price + (prop.houses * prop.house_cost) for prop in self.properties
        )
        return self.money + property_value


class MonopolyGame:
    def __init__(self, player_names: List[str]):
        assert 2 <= len(player_names) <= 8, "Must have 2-8 players"

        self.console = Console()
        self.players = [Player(name) for name in player_names]
        self.current_player_index = 0
        self.houses_remaining = 32
        self.hotels_remaining = 12
        self.game_over = False
        self.winner: Optional[Player] = None

        self._setup_board()
        self._setup_cards()

    def _setup_board(self):
        """Initialize the Monopoly board with all spaces"""
        self.board_spaces: List[BoardSpace] = []

        # Position 0: GO
        self.board_spaces.append(BoardSpace(0, "GO", SpaceType.GO))

        # Properties and other spaces
        properties_data = self._get_properties_data()

        for i, data in enumerate(properties_data):
            if data["type"] == "property":
                prop = Property(
                    name=data["name"],
                    color=data["color"],
                    price=data["price"],
                    rent_base=data["rent"][0],
                    rent_with_set=data["rent"][1],
                    house_cost=data["house_cost"],
                    rent_1_house=data["rent"][2],
                    rent_2_house=data["rent"][3],
                    rent_3_house=data["rent"][4],
                    rent_4_house=data["rent"][5],
                    rent_hotel=data["rent"][6],
                    mortgage_value=data["price"] // 2,
                )
                space = BoardSpace(i + 1, data["name"], SpaceType.PROPERTY, prop)
            elif data["type"] == "railroad":
                prop = Property(
                    name=data["name"],
                    color=PropertyColor.RAILROAD,
                    price=200,
                    rent_base=25,
                    rent_with_set=0,
                    house_cost=0,
                    rent_1_house=0,
                    rent_2_house=0,
                    rent_3_house=0,
                    rent_4_house=0,
                    rent_hotel=0,
                    mortgage_value=100,
                )
                space = BoardSpace(i + 1, data["name"], SpaceType.RAILROAD, prop)
            elif data["type"] == "utility":
                prop = Property(
                    name=data["name"],
                    color=PropertyColor.UTILITY,
                    price=150,
                    rent_base=0,
                    rent_with_set=0,
                    house_cost=0,
                    rent_1_house=0,
                    rent_2_house=0,
                    rent_3_house=0,
                    rent_4_house=0,
                    rent_hotel=0,
                    mortgage_value=75,
                )
                space = BoardSpace(i + 1, data["name"], SpaceType.UTILITY, prop)
            else:
                space = BoardSpace(
                    i + 1,
                    data["name"],
                    SpaceType[data["type"].upper()],
                    tax_amount=data.get("amount", 0),
                )

            self.board_spaces.append(space)

    def _get_properties_data(self) -> List[Dict]:
        """Return the complete Monopoly board data with USA property names"""
        return [
            {
                "name": "Mediterranean Avenue",
                "type": "property",
                "color": PropertyColor.BROWN,
                "price": 60,
                "rent": [2, 4, 10, 30, 90, 160, 250],
                "house_cost": 50,
            },
            {"name": "Community Chest", "type": "community_chest"},
            {
                "name": "Baltic Avenue",
                "type": "property",
                "color": PropertyColor.BROWN,
                "price": 60,
                "rent": [4, 8, 20, 60, 180, 320, 450],
                "house_cost": 50,
            },
            {"name": "Income Tax", "type": "tax", "amount": 200},
            {"name": "Reading Railroad", "type": "railroad"},
            {
                "name": "Oriental Avenue",
                "type": "property",
                "color": PropertyColor.LIGHT_BLUE,
                "price": 100,
                "rent": [6, 12, 30, 90, 270, 400, 550],
                "house_cost": 50,
            },
            {"name": "Chance", "type": "chance"},
            {
                "name": "Vermont Avenue",
                "type": "property",
                "color": PropertyColor.LIGHT_BLUE,
                "price": 100,
                "rent": [6, 12, 30, 90, 270, 400, 550],
                "house_cost": 50,
            },
            {
                "name": "Connecticut Avenue",
                "type": "property",
                "color": PropertyColor.LIGHT_BLUE,
                "price": 120,
                "rent": [8, 16, 40, 100, 300, 450, 600],
                "house_cost": 50,
            },
            {"name": "Jail", "type": "jail"},
            {
                "name": "St. Charles Place",
                "type": "property",
                "color": PropertyColor.PINK,
                "price": 140,
                "rent": [10, 20, 50, 150, 450, 625, 750],
                "house_cost": 100,
            },
            {"name": "Electric Company", "type": "utility"},
            {
                "name": "States Avenue",
                "type": "property",
                "color": PropertyColor.PINK,
                "price": 140,
                "rent": [10, 20, 50, 150, 450, 625, 750],
                "house_cost": 100,
            },
            {
                "name": "Virginia Avenue",
                "type": "property",
                "color": PropertyColor.PINK,
                "price": 160,
                "rent": [12, 24, 60, 180, 500, 700, 900],
                "house_cost": 100,
            },
            {"name": "Pennsylvania Railroad", "type": "railroad"},
            {
                "name": "St. James Place",
                "type": "property",
                "color": PropertyColor.ORANGE,
                "price": 180,
                "rent": [14, 28, 70, 200, 550, 750, 950],
                "house_cost": 100,
            },
            {"name": "Community Chest", "type": "community_chest"},
            {
                "name": "Tennessee Avenue",
                "type": "property",
                "color": PropertyColor.ORANGE,
                "price": 180,
                "rent": [14, 28, 70, 200, 550, 750, 950],
                "house_cost": 100,
            },
            {
                "name": "New York Avenue",
                "type": "property",
                "color": PropertyColor.ORANGE,
                "price": 200,
                "rent": [16, 32, 80, 220, 600, 800, 1000],
                "house_cost": 100,
            },
            {"name": "Free Parking", "type": "free_parking"},
            {
                "name": "Kentucky Avenue",
                "type": "property",
                "color": PropertyColor.RED,
                "price": 220,
                "rent": [18, 36, 90, 250, 700, 875, 1050],
                "house_cost": 150,
            },
            {"name": "Chance", "type": "chance"},
            {
                "name": "Indiana Avenue",
                "type": "property",
                "color": PropertyColor.RED,
                "price": 220,
                "rent": [18, 36, 90, 250, 700, 875, 1050],
                "house_cost": 150,
            },
            {
                "name": "Illinois Avenue",
                "type": "property",
                "color": PropertyColor.RED,
                "price": 240,
                "rent": [20, 40, 100, 300, 750, 925, 1100],
                "house_cost": 150,
            },
            {"name": "B. & O. Railroad", "type": "railroad"},
            {
                "name": "Atlantic Avenue",
                "type": "property",
                "color": PropertyColor.YELLOW,
                "price": 260,
                "rent": [22, 44, 110, 330, 800, 975, 1150],
                "house_cost": 150,
            },
            {
                "name": "Ventnor Avenue",
                "type": "property",
                "color": PropertyColor.YELLOW,
                "price": 260,
                "rent": [22, 44, 110, 330, 800, 975, 1150],
                "house_cost": 150,
            },
            {"name": "Water Works", "type": "utility"},
            {
                "name": "Marvin Gardens",
                "type": "property",
                "color": PropertyColor.YELLOW,
                "price": 280,
                "rent": [24, 48, 120, 360, 850, 1025, 1200],
                "house_cost": 150,
            },
            {"name": "Go to Jail", "type": "go_to_jail"},
            {
                "name": "Pacific Avenue",
                "type": "property",
                "color": PropertyColor.GREEN,
                "price": 300,
                "rent": [26, 52, 130, 390, 900, 1100, 1275],
                "house_cost": 200,
            },
            {
                "name": "North Carolina Avenue",
                "type": "property",
                "color": PropertyColor.GREEN,
                "price": 300,
                "rent": [26, 52, 130, 390, 900, 1100, 1275],
                "house_cost": 200,
            },
            {"name": "Community Chest", "type": "community_chest"},
            {
                "name": "Pennsylvania Avenue",
                "type": "property",
                "color": PropertyColor.GREEN,
                "price": 320,
                "rent": [28, 56, 150, 450, 1000, 1200, 1400],
                "house_cost": 200,
            },
            {"name": "Short Line", "type": "railroad"},
            {"name": "Chance", "type": "chance"},
            {
                "name": "Park Place",
                "type": "property",
                "color": PropertyColor.DARK_BLUE,
                "price": 350,
                "rent": [35, 70, 175, 500, 1100, 1300, 1500],
                "house_cost": 200,
            },
            {"name": "Luxury Tax", "type": "tax", "amount": 100},
            {
                "name": "Boardwalk",
                "type": "property",
                "color": PropertyColor.DARK_BLUE,
                "price": 400,
                "rent": [50, 100, 200, 600, 1400, 1700, 2000],
                "house_cost": 200,
            },
        ]

    def _setup_cards(self):
        """Initialize Chance and Community Chest cards"""
        self.chance_cards = [
            "Advance to Boardwalk",
            "Advance to Go (Collect $200)",
            "Advance to Illinois Avenue. If you pass Go, collect $200",
            "Advance to St. Charles Place. If you pass Go, collect $200",
            "Advance to the nearest Railroad. If unowned, you may buy it from the Bank. If owned, pay owner twice the rental to which they are otherwise entitled",
            "Advance to the nearest Railroad. If unowned, you may buy it from the Bank. If owned, pay owner twice the rental to which they are otherwise entitled",
            "Advance token to nearest Utility. If unowned, you may buy it from the Bank. If owned, throw dice and pay owner a total ten times amount thrown",
            "Bank pays you dividend of $50",
            "Get Out of Jail Free",
            "Go Back 3 Spaces",
            "Go to Jail. Go directly to Jail, do not pass Go, do not collect $200",
            "Make general repairs on all your property. For each house pay $25. For each hotel pay $100",
            "Speeding fine $15",
            "Take a trip to Reading Railroad. If you pass Go, collect $200",
            "You have been elected Chairman of the Board. Pay each player $50",
            "Your building loan matures. Collect $150",
        ]

        self.community_chest_cards = [
            "Advance to Go (Collect $200)",
            "Bank error in your favor. Collect $200",
            "Doctor's fee. Pay $50",
            "From sale of stock you get $50",
            "Get Out of Jail Free",
            "Go to Jail. Go directly to jail, do not pass Go, do not collect $200",
            "Holiday fund matures. Receive $100",
            "Income tax refund. Collect $20",
            "It is your birthday. Collect $10 from every player",
            "Life insurance matures. Collect $100",
            "Pay hospital fees of $100",
            "Pay school fees of $50",
            "Receive $25 consultancy fee",
            "You are assessed for street repair. $40 per house. $115 per hotel",
            "You have won second prize in a beauty contest. Collect $10",
            "You inherit $100",
        ]

        random.shuffle(self.chance_cards)
        random.shuffle(self.community_chest_cards)

    def get_current_player(self) -> Player:
        return self.players[self.current_player_index]

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def roll_dice(self) -> Tuple[int, int]:
        return random.randint(1, 6), random.randint(1, 6)

    def run_game(self):
        """Main game loop"""
        self.console.print("[bold green]Welcome to Monopoly![/bold green]")
        self.console.print(f"Players: {', '.join(p.name for p in self.players)}")
        self.console.print()

        while not self.game_over:
            self._display_game_state()
            current_player = self.get_current_player()

            if current_player.is_bankrupt:
                self.next_turn()
                continue

            self._play_turn(current_player)
            self._check_game_over()

            if not self.game_over:
                self.next_turn()

        if self.winner:
            self.console.print(
                f"[bold yellow]🎉 {self.winner.name} wins with ${self.winner.total_wealth()}! 🎉[/bold yellow]"
            )

    def _display_game_state(self):
        """Display current game state with board and player info"""
        self.console.print("\n" + "=" * 80)

        # Display player summary
        table = Table(title="Player Status")
        table.add_column("Player", style="cyan", no_wrap=True)
        table.add_column("Position", style="magenta")
        table.add_column("Cash", style="green")
        table.add_column("Properties", style="yellow")
        table.add_column("Net Worth", style="red")

        for i, player in enumerate(self.players):
            current_marker = "→" if i == self.current_player_index else " "
            position_name = self.board_spaces[player.position].name
            net_worth = player.total_wealth()

            status = ""
            if player.jail_turns > 0:
                status = f" 🔒({player.jail_turns})"
            if player.get_out_of_jail_free_cards > 0:
                status += f" 🃏({player.get_out_of_jail_free_cards})"

            table.add_row(
                f"{current_marker} {player.name}{status}",
                f"{player.position}: {position_name}",
                f"${player.money}",
                str(len(player.properties)),
                f"${net_worth}",
            )

        self.console.print(table)

        # Display board positions with players
        self._display_board_summary()

    def _display_board_summary(self):
        """Display a summary of key board positions"""
        # Show properties owned by each player
        for player in self.players:
            if player.properties:
                props_by_color = {}
                for prop in player.properties:
                    color_name = prop.color.name.replace("_", " ").title()
                    if color_name not in props_by_color:
                        props_by_color[color_name] = []
                    props_by_color[color_name].append(prop.name)

                prop_summary = []
                for color, props in props_by_color.items():
                    monopoly_marker = (
                        "🏠"
                        if len(props)
                        >= self._get_monopoly_size(player.properties[0].color)
                        else ""
                    )
                    prop_summary.append(
                        f"{color}: {', '.join(props)} {monopoly_marker}"
                    )

                self.console.print(
                    f"[bold]{player.name}'s Properties:[/bold] {' | '.join(prop_summary)}"
                )

    def _get_monopoly_size(self, color: PropertyColor) -> int:
        """Get the number of properties needed for a monopoly of this color"""
        if color in [PropertyColor.BROWN, PropertyColor.DARK_BLUE]:
            return 2
        elif color == PropertyColor.RAILROAD:
            return 4
        elif color == PropertyColor.UTILITY:
            return 2
        else:
            return 3

    def _show_property_management_menu(self, player: Player):
        """Show property management options"""
        if not player.properties:
            self.console.print("You don't own any properties.")
            return

        self.console.print(f"\n[bold]{player.name}'s Property Management[/bold]")

        # Show property details
        table = Table()
        table.add_column("Property", style="cyan")
        table.add_column("Color", style="magenta")
        table.add_column("Houses", style="yellow")
        table.add_column("Rent", style="green")
        table.add_column("Mortgage", style="red")

        for prop in player.properties:
            color_name = prop.color.name.replace("_", " ").title()
            houses = "🏨" if prop.houses == 5 else "🏠" * prop.houses
            rent = f"${prop.get_rent_amount()}"
            mortgage_status = "🔒" if prop.is_mortgaged else f"${prop.mortgage_value}"

            table.add_row(prop.name, color_name, houses, rent, mortgage_status)

        self.console.print(table)

        # Property management actions
        choices = ["1", "2", "3", "4"]
        menu = "1. Build houses/hotels\n2. Mortgage/Unmortgage properties\n3. Trade properties\n4. Continue game"

        self.console.print(menu)
        action = Prompt.ask("Choose action", choices=choices, default="4")

        if action == "1":
            self._handle_building(player)
        elif action == "2":
            self._handle_mortgaging(player)
        elif action == "3":
            self._handle_trading(player)

    def _handle_building(self, player: Player):
        """Handle building houses and hotels"""
        buildable_props = []
        for prop in player.properties:
            if (
                prop.color not in [PropertyColor.RAILROAD, PropertyColor.UTILITY]
                and player.owns_monopoly(prop.color)
                and not prop.is_mortgaged
                and prop.houses < 5
            ):
                buildable_props.append(prop)

        if not buildable_props:
            self.console.print("No properties available for building.")
            return

        self.console.print("Properties available for building:")
        for i, prop in enumerate(buildable_props):
            house_text = "hotel" if prop.houses == 4 else "house"
            self.console.print(
                f"{i + 1}. {prop.name} - Build {house_text} for ${prop.house_cost}"
            )

        try:
            choice = int(
                Prompt.ask("Choose property to build on (0 to cancel)", default="0")
            )
            if choice == 0:
                return

            prop = buildable_props[choice - 1]
            if player.can_afford(prop.house_cost) and self.houses_remaining > 0:
                player.pay(prop.house_cost)
                prop.houses += 1
                if prop.houses < 5:
                    self.houses_remaining -= 1
                else:
                    self.hotels_remaining -= 1

                building_type = "hotel" if prop.houses == 5 else "house"
                self.console.print(f"Built {building_type} on {prop.name}!")
            else:
                self.console.print(
                    "Cannot build - insufficient funds or no buildings available."
                )
        except (ValueError, IndexError):
            self.console.print("Invalid choice.")
    
    def _show_monopoly_building_status(self, player: Player):
        """Show building status for player's monopolies"""
        monopolies = {}
        for prop in player.properties:
            if (prop.color not in [PropertyColor.RAILROAD, PropertyColor.UTILITY] and 
                player.owns_monopoly(prop.color)):
                if prop.color not in monopolies:
                    monopolies[prop.color] = []
                monopolies[prop.color].append(prop)
        
        if monopolies:
            self.console.print(f"\n[bold]{player.name}'s Monopoly Building Status:[/bold]")
            
            table = Table()
            table.add_column("Property", style="cyan")
            table.add_column("Houses", style="yellow")
            table.add_column("Rent", style="green")
            
            for color, props in monopolies.items():
                for prop in props:
                    houses_display = "🏨" if prop.houses == 5 else "🏠" * prop.houses
                    rent = f"${prop.get_rent_amount()}"
                    table.add_row(prop.name, houses_display, rent)
            
            self.console.print(table)

    def _handle_mortgaging(self, player: Player):
        """Handle mortgaging and unmortgaging properties"""
        if not player.properties:
            return

        self.console.print("Property mortgage management:")
        for i, prop in enumerate(player.properties):
            status = (
                "Mortgaged"
                if prop.is_mortgaged
                else f"Available (${prop.mortgage_value})"
            )
            self.console.print(f"{i + 1}. {prop.name} - {status}")

        try:
            choice = int(Prompt.ask("Choose property (0 to cancel)", default="0"))
            if choice == 0:
                return

            prop = player.properties[choice - 1]
            if prop.is_mortgaged:
                unmortgage_cost = int(prop.mortgage_value * 1.1)
                if player.can_afford(unmortgage_cost):
                    if (
                        Prompt.ask(
                            f"Unmortgage for ${unmortgage_cost}?", choices=["y", "n"]
                        )
                        == "y"
                    ):
                        player.pay(unmortgage_cost)
                        prop.is_mortgaged = False
                        self.console.print(f"Unmortgaged {prop.name}!")
                else:
                    self.console.print("Cannot afford to unmortgage.")
            else:
                if (
                    Prompt.ask(
                        f"Mortgage for ${prop.mortgage_value}?", choices=["y", "n"]
                    )
                    == "y"
                ):
                    player.receive(prop.mortgage_value)
                    prop.is_mortgaged = True
                    self.console.print(f"Mortgaged {prop.name}!")
        except (ValueError, IndexError):
            self.console.print("Invalid choice.")

    def _handle_trading(self, player: Player):
        """Handle property trading between players"""
        other_players = [
            p
            for p in self.players
            if p != player and not p.is_bankrupt and p.properties
        ]

        if not other_players:
            self.console.print("No other players have properties to trade.")
            return

        self.console.print(f"\n[bold]Property Trading - {player.name}[/bold]")

        # Select trading partner
        self.console.print("Choose trading partner:")
        for i, other_player in enumerate(other_players):
            prop_count = len(other_player.properties)
            cash = other_player.money
            self.console.print(
                f"{i + 1}. {other_player.name} ({prop_count} properties, ${cash})"
            )

        try:
            partner_choice = int(
                Prompt.ask("Choose partner (0 to cancel)", default="0")
            )
            if partner_choice == 0:
                return

            trading_partner = other_players[partner_choice - 1]
            self._conduct_trade(player, trading_partner)

        except (ValueError, IndexError):
            self.console.print("Invalid choice.")

    def _conduct_trade(self, player1: Player, player2: Player):
        """Conduct a trade between two players"""
        self.console.print(f"\n[bold]Trade: {player1.name} ↔ {player2.name}[/bold]")

        # Show both players' properties
        self._show_player_properties_for_trade(player1, "Your Properties")
        self._show_player_properties_for_trade(player2, f"{player2.name}'s Properties")

        # Build trade offer
        trade_offer = self._build_trade_offer(player1, player2)

        if not trade_offer:
            return

        # Present trade to other player
        if self._present_trade_offer(player1, player2, trade_offer):
            self._execute_trade(player1, player2, trade_offer)
        else:
            self.console.print(f"{player2.name} declined the trade.")

    def _show_player_properties_for_trade(self, player: Player, title: str):
        """Show a player's properties in trade format"""
        if not player.properties:
            self.console.print(f"{title}: None")
            return

        self.console.print(f"\n[bold]{title}:[/bold]")

        table = Table()
        table.add_column("#", style="dim")
        table.add_column("Property", style="cyan")
        table.add_column("Color", style="magenta")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")

        for i, prop in enumerate(player.properties):
            color_name = prop.color.name.replace("_", " ").title()
            value = f"${prop.price}"
            status = "Mortgaged" if prop.is_mortgaged else "Clear"
            if prop.houses > 0:
                status += f" ({prop.houses}🏠)" if prop.houses < 5 else " (🏨)"

            table.add_row(str(i + 1), prop.name, color_name, value, status)

        self.console.print(table)
        self.console.print(f"Cash: ${player.money}")

    def _build_trade_offer(self, player1: Player, player2: Player):
        """Build a trade offer from player1 to player2"""
        offer = {
            "player1_properties": [],
            "player1_cash": 0,
            "player2_properties": [],
            "player2_cash": 0,
        }

        self.console.print("\n[bold]Building Trade Offer[/bold]")
        self.console.print("What will you give?")

        # Player 1 offers properties
        if player1.properties:
            prop_choices = Prompt.ask(
                "Enter property numbers to give (comma-separated, or 'none')",
                default="none",
            )
            if prop_choices.lower() != "none":
                try:
                    prop_indices = [int(x.strip()) - 1 for x in prop_choices.split(",")]
                    for idx in prop_indices:
                        if 0 <= idx < len(player1.properties):
                            prop = player1.properties[idx]
                            if (
                                prop.houses == 0
                            ):  # Can't trade properties with buildings
                                offer["player1_properties"].append(prop)
                            else:
                                self.console.print(
                                    f"Cannot trade {prop.name} - has buildings"
                                )
                except ValueError:
                    self.console.print("Invalid property selection")

        # Player 1 offers cash
        try:
            cash_offer = int(
                Prompt.ask(f"Cash to give (0-{player1.money})", default="0")
            )
            if 0 <= cash_offer <= player1.money:
                offer["player1_cash"] = cash_offer
        except ValueError:
            pass

        self.console.print("\nWhat do you want in return?")

        # Player 1 wants properties
        if player2.properties:
            prop_choices = Prompt.ask(
                "Enter property numbers you want (comma-separated, or 'none')",
                default="none",
            )
            if prop_choices.lower() != "none":
                try:
                    prop_indices = [int(x.strip()) - 1 for x in prop_choices.split(",")]
                    for idx in prop_indices:
                        if 0 <= idx < len(player2.properties):
                            prop = player2.properties[idx]
                            if prop.houses == 0:
                                offer["player2_properties"].append(prop)
                            else:
                                self.console.print(
                                    f"Cannot request {prop.name} - has buildings"
                                )
                except ValueError:
                    self.console.print("Invalid property selection")

        # Player 1 wants cash
        try:
            cash_wanted = int(
                Prompt.ask(f"Cash you want (0-{player2.money})", default="0")
            )
            if 0 <= cash_wanted <= player2.money:
                offer["player2_cash"] = cash_wanted
        except ValueError:
            pass

        # Validate trade has something
        if (
            not offer["player1_properties"]
            and offer["player1_cash"] == 0
            and not offer["player2_properties"]
            and offer["player2_cash"] == 0
        ):
            self.console.print("No valid trade items selected.")
            return None

        return offer

    def _present_trade_offer(self, player1: Player, player2: Player, offer) -> bool:
        """Present trade offer to player2 for acceptance"""
        self.console.print(f"\n[bold]Trade Offer for {player2.name}[/bold]")

        # Show what player2 would give
        self.console.print("[red]You would give:[/red]")
        for prop in offer["player2_properties"]:
            self.console.print(f"  • {prop.name}")
        if offer["player2_cash"] > 0:
            self.console.print(f"  • ${offer['player2_cash']} cash")

        # Show what player2 would receive
        self.console.print("[green]You would receive:[/green]")
        for prop in offer["player1_properties"]:
            self.console.print(f"  • {prop.name}")
        if offer["player1_cash"] > 0:
            self.console.print(f"  • ${offer['player1_cash']} cash")

        accept = Prompt.ask("Accept this trade?", choices=["y", "n"], default="n")
        return accept.lower() == "y"

    def _execute_trade(self, player1: Player, player2: Player, offer):
        """Execute the agreed trade"""
        self.console.print(
            f"\n[green]Executing trade between {player1.name} and {player2.name}[/green]"
        )

        # Transfer properties from player1 to player2
        for prop in offer["player1_properties"]:
            player1.properties.remove(prop)
            player2.properties.append(prop)
            prop.owner = player2
            self.console.print(f"  {prop.name}: {player1.name} → {player2.name}")

        # Transfer properties from player2 to player1
        for prop in offer["player2_properties"]:
            player2.properties.remove(prop)
            player1.properties.append(prop)
            prop.owner = player1
            self.console.print(f"  {prop.name}: {player2.name} → {player1.name}")

        # Transfer cash
        if offer["player1_cash"] > 0:
            player1.pay(offer["player1_cash"])
            player2.receive(offer["player1_cash"])
            self.console.print(
                f"  ${offer['player1_cash']}: {player1.name} → {player2.name}"
            )

        if offer["player2_cash"] > 0:
            player2.pay(offer["player2_cash"])
            player1.receive(offer["player2_cash"])
            self.console.print(
                f"  ${offer['player2_cash']}: {player2.name} → {player1.name}"
            )

        self.console.print("[green]Trade completed successfully![/green]")

    def _auction_property(self, property: Property):
        """Conduct an auction for an unowned property"""
        self.console.print(
            f"\n[bold yellow]🔨 AUCTION: {property.name} 🔨[/bold yellow]"
        )
        self.console.print("Starting bid: $10")

        # Get eligible bidders (players with at least $10)
        eligible_bidders = [
            p for p in self.players if not p.is_bankrupt and p.money >= 10
        ]

        if len(eligible_bidders) < 2:
            self.console.print(
                "Not enough eligible bidders - property remains unowned."
            )
            return

        current_bid = 10
        current_winner = None
        active_bidders = eligible_bidders.copy()

        while len(active_bidders) > 1:
            self.console.print(f"\nCurrent bid: ${current_bid}")
            if current_winner:
                self.console.print(f"Leading bidder: {current_winner.name}")

            # Get bids from each active bidder
            new_active_bidders = []

            for bidder in active_bidders:
                if bidder.money <= current_bid:
                    self.console.print(f"{bidder.name} cannot afford to bid higher.")
                    continue

                max_bid = min(
                    bidder.money, current_bid + 1000
                )  # Reasonable bid increment limit

                try:
                    bid_input = Prompt.ask(
                        f"{bidder.name}, enter your bid (${current_bid + 1}-${max_bid}, or 'pass')",
                        default="pass",
                    )

                    if bid_input.lower() == "pass":
                        self.console.print(f"{bidder.name} passes.")
                        continue

                    bid_amount = int(bid_input)

                    if bid_amount <= current_bid:
                        self.console.print(
                            f"Bid must be higher than ${current_bid}. {bidder.name} passes."
                        )
                        continue

                    if bid_amount > bidder.money:
                        self.console.print(f"Insufficient funds. {bidder.name} passes.")
                        continue

                    # Valid bid
                    current_bid = bid_amount
                    current_winner = bidder
                    new_active_bidders.append(bidder)
                    self.console.print(f"✅ {bidder.name} bids ${bid_amount}")

                except ValueError:
                    self.console.print(f"Invalid bid. {bidder.name} passes.")
                    continue

            active_bidders = new_active_bidders

            # If only one person bid this round, give others one more chance
            if len(active_bidders) == 1 and current_winner:
                self.console.print(
                    f"\nFinal call! ${current_bid} going once, going twice..."
                )

                final_bidders = []
                for bidder in eligible_bidders:
                    if bidder != current_winner and bidder.money > current_bid:
                        try:
                            final_bid = Prompt.ask(
                                f"{bidder.name}, final chance to bid (higher than ${current_bid}, or 'pass')",
                                default="pass",
                            )

                            if final_bid.lower() != "pass":
                                bid_amount = int(final_bid)
                                if (
                                    bid_amount > current_bid
                                    and bid_amount <= bidder.money
                                ):
                                    current_bid = bid_amount
                                    current_winner = bidder
                                    final_bidders.append(bidder)
                                    self.console.print(
                                        f"✅ {bidder.name} bids ${bid_amount}"
                                    )
                        except ValueError:
                            continue

                if not final_bidders:
                    break

                active_bidders = final_bidders

        # Auction complete
        if current_winner and current_bid > 0:
            current_winner.pay(current_bid)
            property.owner = current_winner
            current_winner.properties.append(property)

            self.console.print("\n[bold green]🔨 SOLD! 🔨[/bold green]")
            self.console.print(
                f"{current_winner.name} wins {property.name} for ${current_bid}"
            )
        else:
            self.console.print(
                f"\n[yellow]No winning bids - {property.name} remains unowned.[/yellow]"
            )

    def _play_turn(self, player: Player):
        """Execute a single player's turn"""
        self.console.print(f"\n[bold]{player.name}'s Turn[/bold] (${player.money})")

        # Pre-roll property management
        if player.properties and not player.jail_turns:
            manage = Prompt.ask(
                "Manage properties before rolling?", choices=["y", "n"], default="n"
            )
            if manage == "y":
                self._show_property_management_menu(player)

        if player.jail_turns > 0:
            self._handle_jail_turn(player)
            return

        # Wait for player to roll
        Prompt.ask(f"{player.name}, press Enter to roll dice", default="")

        # Roll dice
        die1, die2 = self.roll_dice()
        dice_sum = die1 + die2
        is_doubles = die1 == die2

        self.console.print(f"🎲 Rolled: {die1} + {die2} = {dice_sum}")
        if is_doubles:
            self.console.print("🎲 Doubles! You get another turn after this one.")

        # Move player
        old_position = player.position
        player.position = (player.position + dice_sum) % 40

        # Check if passed GO
        if player.position < old_position:
            player.receive(200)
            self.console.print("💰 Passed GO! Collect $200")

        # Handle landing on space
        current_space = self.board_spaces[player.position]
        self.console.print(f"📍 Landed on: {current_space.name}")

        self._handle_space_landing(player, current_space, dice_sum)

        # Handle doubles
        if is_doubles and player.jail_turns == 0:
            self.console.print("🎲 Rolling again due to doubles!")
            self._play_turn(player)  # Recursive call for doubles

    def _handle_jail_turn(self, player: Player):
        """Handle a turn while in jail"""
        self.console.print(f"🔒 {player.name} is in jail (turn {player.jail_turns}/3)")

        choices = ["1", "2"]
        menu_text = "1. Roll dice (need doubles)\n2. Pay $50"

        if player.get_out_of_jail_free_cards > 0:
            choices.append("3")
            menu_text += "\n3. Use Get Out of Jail Free card"

        self.console.print(menu_text)
        action = Prompt.ask("Choose action", choices=choices)

        if action == "1":
            die1, die2 = self.roll_dice()
            if die1 == die2:
                self.console.print(
                    f"🎲 Rolled doubles: {die1}, {die2}! Released from jail!"
                )
                player.jail_turns = 0
                player.position = (player.position + die1 + die2) % 40
                current_space = self.board_spaces[player.position]
                self._handle_space_landing(player, current_space, die1 + die2)
            else:
                self.console.print(f"🎲 Rolled: {die1}, {die2} - Still in jail")
                player.jail_turns += 1
                if player.jail_turns > 3:
                    self.console.print("Must pay $50 to get out!")
                    player.pay(50)
                    player.jail_turns = 0
        elif action == "2":
            if player.pay(50):
                self.console.print("💸 Paid $50 - Released from jail!")
                player.jail_turns = 0
            else:
                self.console.print("❌ Not enough money!")
        elif action == "3" and player.get_out_of_jail_free_cards > 0:
            player.get_out_of_jail_free_cards -= 1
            player.jail_turns = 0
            self.console.print("🃏 Used Get Out of Jail Free card - Released!")

    def _handle_space_landing(self, player: Player, space: BoardSpace, dice_sum: int):
        """Handle what happens when a player lands on a space"""
        if space.space_type == SpaceType.PROPERTY:
            self._handle_property_landing(player, space.property, dice_sum)
        elif space.space_type == SpaceType.RAILROAD:
            self._handle_property_landing(player, space.property, dice_sum)
        elif space.space_type == SpaceType.UTILITY:
            self._handle_property_landing(player, space.property, dice_sum)
        elif space.space_type == SpaceType.TAX:
            self._handle_tax(player, space.tax_amount)
        elif space.space_type == SpaceType.CHANCE:
            self._handle_chance_card(player)
        elif space.space_type == SpaceType.COMMUNITY_CHEST:
            self._handle_community_chest_card(player)
        elif space.space_type == SpaceType.GO_TO_JAIL:
            self._send_to_jail(player)

    def _handle_property_landing(
        self, player: Player, property: Property, dice_sum: int
    ):
        """Handle landing on a property, railroad, or utility"""
        if property.owner is None:
            # Property is unowned - offer to buy
            self.console.print(f"💰 {property.name} is available for ${property.price}")

            if player.can_afford(property.price):
                buy = Prompt.ask(
                    f"Buy {property.name} for ${property.price}?", choices=["y", "n"]
                )
                if buy.lower() == "y":
                    player.pay(property.price)
                    property.owner = player
                    player.properties.append(property)
                    self.console.print(f"✅ {player.name} bought {property.name}!")
                else:
                    # Property goes to auction
                    self._auction_property(property)
            else:
                self.console.print("❌ Cannot afford this property")
                self._auction_property(property)

        elif property.owner != player:
            # Pay rent to owner
            rent = property.get_rent_amount(dice_sum)
            if rent > 0:
                self.console.print(f"💸 Pay ${rent} rent to {property.owner.name}")
                if player.pay(rent):
                    property.owner.receive(rent)
                else:
                    self.console.print("❌ Not enough money to pay rent!")
                    self._handle_bankruptcy(player, rent)

    def _handle_tax(self, player: Player, amount: int):
        """Handle landing on tax spaces"""
        self.console.print(f"💸 Pay ${amount} tax")
        if not player.pay(amount):
            self.console.print("❌ Not enough money to pay tax!")
            # TODO: Handle bankruptcy

    def _handle_chance_card(self, player: Player):
        """Handle drawing a Chance card"""
        if not self.chance_cards:
            self.chance_cards = [
                "Advance to Boardwalk",
                "Advance to Go (Collect $200)",
                "Advance to Illinois Avenue. If you pass Go, collect $200",
                "Advance to St. Charles Place. If you pass Go, collect $200",
                "Advance to the nearest Railroad. If unowned, you may buy it from the Bank. If owned, pay owner twice the rental to which they are otherwise entitled",
                "Advance to the nearest Railroad. If unowned, you may buy it from the Bank. If owned, pay owner twice the rental to which they are otherwise entitled",
                "Advance token to nearest Utility. If unowned, you may buy it from the Bank. If owned, throw dice and pay owner a total ten times amount thrown",
                "Bank pays you dividend of $50",
                "Get Out of Jail Free",
                "Go Back 3 Spaces",
                "Go to Jail. Go directly to Jail, do not pass Go, do not collect $200",
                "Make general repairs on all your property. For each house pay $25. For each hotel pay $100",
                "Speeding fine $15",
                "Take a trip to Reading Railroad. If you pass Go, collect $200",
                "You have been elected Chairman of the Board. Pay each player $50",
                "Your building loan matures. Collect $150",
            ]
            random.shuffle(self.chance_cards)

        card = self.chance_cards.pop()
        self.console.print(f"🃏 Chance: [italic]{card}[/italic]")

        # Enhanced card implementation
        if "Get Out of Jail Free" in card:
            player.get_out_of_jail_free_cards += 1
        elif "Advance to Go" in card:
            old_pos = player.position
            player.position = 0
            player.receive(200)
        elif "Advance to Boardwalk" in card:
            old_pos = player.position
            player.position = 39  # Boardwalk position
            space = self.board_spaces[player.position]
            self._handle_space_landing(player, space, 0)
        elif "Advance to Illinois Avenue" in card:
            old_pos = player.position
            player.position = 24  # Illinois Avenue
            if player.position < old_pos:
                player.receive(200)
            space = self.board_spaces[player.position]
            self._handle_space_landing(player, space, 0)
        elif "Advance to St. Charles Place" in card:
            old_pos = player.position
            player.position = 11  # St. Charles Place
            if player.position < old_pos:
                player.receive(200)
            space = self.board_spaces[player.position]
            self._handle_space_landing(player, space, 0)
        elif "nearest Railroad" in card:
            self._advance_to_nearest_railroad(player, double_rent=True)
        elif "nearest Utility" in card:
            self._advance_to_nearest_utility(player)
        elif "dividend of $50" in card:
            player.receive(50)
        elif "Go Back 3 Spaces" in card:
            player.position = (player.position - 3) % 40
            space = self.board_spaces[player.position]
            self.console.print(f"Moved back to: {space.name}")
            self._handle_space_landing(player, space, 0)
        elif "general repairs" in card:
            cost = sum(
                25 * prop.houses if prop.houses < 5 else 100
                for prop in player.properties
            )
            player.pay(cost)
            self.console.print(f"Paid ${cost} in repairs")
        elif "fine $15" in card:
            player.pay(15)
        elif "Chairman of the Board" in card:
            for other_player in self.players:
                if other_player != player:
                    other_player.pay(50)
                    player.receive(50)
        elif "building loan matures" in card:
            player.receive(150)
        elif "Reading Railroad" in card:
            old_pos = player.position
            player.position = 5  # Reading Railroad
            if player.position < old_pos:
                player.receive(200)
            space = self.board_spaces[player.position]
            self._handle_space_landing(player, space, 0)
        elif "Go to Jail" in card:
            self._send_to_jail(player)

    def _advance_to_nearest_railroad(self, player: Player, double_rent: bool = False):
        """Advance player to nearest railroad"""
        railroad_positions = [5, 15, 25, 35]  # Railroad positions
        current_pos = player.position

        # Find next railroad
        next_railroad = None
        for pos in railroad_positions:
            if pos > current_pos:
                next_railroad = pos
                break

        if next_railroad is None:
            next_railroad = railroad_positions[0]  # Wrap around to first railroad

        old_pos = player.position
        player.position = next_railroad

        if player.position < old_pos:
            player.receive(200)

        space = self.board_spaces[player.position]
        self.console.print(f"Advanced to: {space.name}")

        if (
            double_rent
            and space.property
            and space.property.owner
            and space.property.owner != player
        ):
            normal_rent = space.property.get_rent_amount()
            rent = normal_rent * 2
            self.console.print(f"💸 Pay double rent: ${rent}")
            if player.pay(rent):
                space.property.owner.receive(rent)
        else:
            self._handle_space_landing(player, space, 0)

    def _advance_to_nearest_utility(self, player: Player):
        """Advance player to nearest utility"""
        utility_positions = [12, 28]  # Electric Company, Water Works
        current_pos = player.position

        # Find next utility
        next_utility = None
        for pos in utility_positions:
            if pos > current_pos:
                next_utility = pos
                break

        if next_utility is None:
            next_utility = utility_positions[0]  # Wrap around

        old_pos = player.position
        player.position = next_utility

        if player.position < old_pos:
            player.receive(200)

        space = self.board_spaces[player.position]
        self.console.print(f"Advanced to: {space.name}")

        if space.property and space.property.owner and space.property.owner != player:
            dice_sum = self.roll_dice()[0] + self.roll_dice()[1]
            rent = dice_sum * 10
            self.console.print(f"🎲 Rolled {dice_sum} for utility rent")
            self.console.print(f"💸 Pay ${rent} rent")
            if player.pay(rent):
                space.property.owner.receive(rent)
        else:
            self._handle_space_landing(player, space, 0)

    def _handle_community_chest_card(self, player: Player):
        """Handle drawing a Community Chest card"""
        if not self.community_chest_cards:
            self.community_chest_cards = [
                "Advance to Go (Collect $200)",
                "Bank error in your favor. Collect $200",
                "Doctor's fee. Pay $50",
                "From sale of stock you get $50",
                "Get Out of Jail Free",
                "Go to Jail. Go directly to jail, do not pass Go, do not collect $200",
                "Holiday fund matures. Receive $100",
                "Income tax refund. Collect $20",
                "It is your birthday. Collect $10 from every player",
                "Life insurance matures. Collect $100",
                "Pay hospital fees of $100",
                "Pay school fees of $50",
                "Receive $25 consultancy fee",
                "You are assessed for street repair. $40 per house. $115 per hotel",
                "You have won second prize in a beauty contest. Collect $10",
                "You inherit $100",
            ]
            random.shuffle(self.community_chest_cards)

        card = self.community_chest_cards.pop()
        self.console.print(f"🏛️ Community Chest: [italic]{card}[/italic]")

        # Enhanced card implementation
        if "Get Out of Jail Free" in card:
            player.get_out_of_jail_free_cards += 1
        elif "Advance to Go" in card:
            player.position = 0
            player.receive(200)
        elif "Bank error in your favor" in card:
            player.receive(200)
        elif "Doctor's fee" in card:
            if not player.pay(50):
                self._handle_bankruptcy(player, 50)
        elif "From sale of stock" in card:
            player.receive(50)
        elif "Holiday fund matures" in card:
            player.receive(100)
        elif "Income tax refund" in card:
            player.receive(20)
        elif "It is your birthday" in card:
            collected = 0
            for other_player in self.players:
                if other_player != player and not other_player.is_bankrupt:
                    if other_player.pay(10):
                        collected += 10
            player.receive(collected)
            self.console.print(f"Collected ${collected} from other players!")
        elif "Life insurance matures" in card:
            player.receive(100)
        elif "Pay hospital fees" in card:
            if not player.pay(100):
                self._handle_bankruptcy(player, 100)
        elif "Pay school fees" in card:
            if not player.pay(50):
                self._handle_bankruptcy(player, 50)
        elif "consultancy fee" in card:
            player.receive(25)
        elif "street repair" in card:
            cost = sum(
                40 * prop.houses if prop.houses < 5 else 115
                for prop in player.properties
            )
            if not player.pay(cost):
                self._handle_bankruptcy(player, cost)
            else:
                self.console.print(f"Paid ${cost} for street repairs")
        elif "beauty contest" in card:
            player.receive(10)
        elif "inherit $100" in card:
            player.receive(100)
        elif "Go to Jail" in card:
            self._send_to_jail(player)

    def _handle_bankruptcy(self, player: Player, debt_amount: int):
        """Handle player bankruptcy"""
        self.console.print(f"[red]{player.name} cannot pay ${debt_amount}![/red]")

        # Try to raise money by mortgaging properties
        available_mortgage_value = sum(
            prop.mortgage_value for prop in player.properties if not prop.is_mortgaged
        )

        if available_mortgage_value + player.money >= debt_amount:
            self.console.print("You can mortgage properties to pay this debt.")
            self._show_property_management_menu(player)

            if player.money >= debt_amount:
                player.pay(debt_amount)
                self.console.print(f"Debt of ${debt_amount} paid!")
                return

        # Player is bankrupt
        self.console.print(f"[red]{player.name} is bankrupt![/red]")
        player.is_bankrupt = True

        # Return properties to bank
        for prop in player.properties:
            prop.owner = None
            prop.houses = 0
            prop.is_mortgaged = False

        player.properties.clear()
        player.money = 0

    def _send_to_jail(self, player: Player):
        """Send player to jail"""
        self.console.print("🚔 Go to Jail!")
        player.position = 10  # Jail position
        player.jail_turns = 1

    def _check_game_over(self):
        """Check if the game should end"""
        active_players = [p for p in self.players if not p.is_bankrupt]

        if len(active_players) <= 1:
            self.game_over = True
            if active_players:
                self.winner = active_players[0]


def main():
    """Entry point for the Monopoly game"""
    console = Console()

    try:
        # Display welcome screen
        console.print(
            Panel.fit(
                "[bold green]🎩 MONOPOLY 🎩[/bold green]\n"
                "[italic]The classic property trading game[/italic]\n\n"
                "Complete TUI implementation with:\n"
                "• Full USA board with all properties\n"
                "• Chance & Community Chest cards\n"
                "• Property management (buy, sell, mortgage)\n"
                "• House & hotel building\n"
                "• Jail mechanics\n"
                "• Bankruptcy handling",
                title="Welcome to Monopoly!",
                border_style="green",
            )
        )

        # Game mode selection
        console.print("\nGame Modes:")
        console.print("1. Quick Demo (2 players, limited turns)")
        console.print("2. Full Game (2-4 players)")
        console.print("3. Test Mode (run automated tests)")

        try:
            mode = Prompt.ask("Choose mode", choices=["1", "2", "3"], default="2")
        except EOFError:
            # Handle non-interactive environments
            console.print("Running in non-interactive mode - starting demo...")
            mode = "1"

        if mode == "3":
            from test_game import run_all_tests

            run_all_tests()
            return

        # Get player setup
        if mode == "1":
            player_names = ["Alice", "Bob"]  # Quick demo
            console.print("Quick Demo: Alice vs Bob")
        else:
            try:
                num_players = int(
                    Prompt.ask(
                        "How many players?", choices=["2", "3", "4"], default="2"
                    )
                )

                player_names = []
                for i in range(num_players):
                    try:
                        name = Prompt.ask(
                            f"Enter name for player {i + 1}", default=f"Player {i + 1}"
                        )
                    except EOFError:
                        name = f"Player {i + 1}"
                    player_names.append(name)
            except EOFError:
                # Handle non-interactive environments
                player_names = ["Player 1", "Player 2"]
                console.print("Using default player names: Player 1, Player 2")

        # Start game
        console.print(f"\nStarting game with: {', '.join(player_names)}")
        console.print("Press Ctrl+C at any time to quit.\n")

        game = MonopolyGame(player_names)

        if mode == "1":
            # Quick demo mode with limited turns
            demo_turns = 10
            console.print(
                f"[yellow]Demo mode: Playing {demo_turns} turns only[/yellow]\n"
            )

            for turn in range(demo_turns):
                if game.game_over:
                    break

                game._display_game_state()
                current_player = game.get_current_player()

                if current_player.is_bankrupt:
                    game.next_turn()
                    continue

                console.print(f"\n[bold]Turn {turn + 1}: {current_player.name}[/bold]")

                # Simulate automated turn for demo
                die1, die2 = game.roll_dice()
                dice_sum = die1 + die2

                console.print(f"🎲 Rolled: {die1} + {die2} = {dice_sum}")

                # Move player
                old_position = current_player.position
                current_player.position = (current_player.position + dice_sum) % 40

                # Check if passed GO
                if current_player.position < old_position:
                    current_player.receive(200)
                    console.print("💰 Passed GO! Collect $200")

                current_space = game.board_spaces[current_player.position]
                console.print(f"📍 Landed on: {current_space.name}")

                # Simplified property handling for demo
                if (
                    current_space.property
                    and current_space.property.owner is None
                    and current_player.can_afford(current_space.property.price)
                    and current_space.property.price <= 200
                ):  # Auto-buy cheaper properties
                    current_player.pay(current_space.property.price)
                    current_space.property.owner = current_player
                    current_player.properties.append(current_space.property)
                    console.print(f"✅ Auto-bought {current_space.property.name}!")

                elif (
                    current_space.property
                    and current_space.property.owner
                    and current_space.property.owner != current_player
                ):
                    rent = current_space.property.get_rent_amount(dice_sum)
                    if rent > 0:
                        console.print(
                            f"💸 Paid ${rent} rent to {current_space.property.owner.name}"
                        )
                        current_player.pay(rent)
                        current_space.property.owner.receive(rent)

                game.next_turn()

                # Pause for readability in demo
                import time

                time.sleep(1)

            console.print("\n[yellow]Demo completed![/yellow]")

            # Show final status
            console.print("\nFinal Status:")
            for player in game.players:
                wealth = player.total_wealth()
                props = len(player.properties)
                console.print(
                    f"{player.name}: ${player.money} cash, {props} properties, ${wealth} total"
                )

        else:
            # Full interactive game
            game.run_game()

    except KeyboardInterrupt:
        console.print(
            "\n[yellow]Game interrupted. Thanks for playing Monopoly![/yellow]"
        )
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        console.print(
            "[dim]This shouldn't happen. The game may be in an invalid state.[/dim]"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
