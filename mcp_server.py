#!/usr/bin/env python3
"""
Monopoly MCP Server - Model Context Protocol interface for LLM gameplay

Exposes the Monopoly game through MCP tools so that AI agents can play together.
"""

import json
import random
from typing import Dict, List, Optional, Any

from fastmcp import FastMCP
from main import MonopolyGame, Player, Property, PropertyColor, SpaceType

# Global game state (in a real deployment, this would be persistent storage)
active_games: Dict[str, MonopolyGame] = {}
game_counter = 0

# Initialize MCP server
mcp = FastMCP("Monopoly Game Server")

@mcp.tool()
def create_game(player_names: List[str]) -> Dict[str, Any]:
    """
    Create a new Monopoly game with the specified players.
    
    Args:
        player_names: List of player names (2-8 players)
        
    Returns:
        Dict with game_id and initial game state
    """
    global game_counter
    
    if not (2 <= len(player_names) <= 8):
        return {"error": "Must have 2-8 players"}
    
    game_counter += 1
    game_id = f"game_{game_counter}"
    
    try:
        game = MonopolyGame(player_names)
        active_games[game_id] = game
        
        return {
            "game_id": game_id,
            "players": [player.name for player in game.players],
            "current_player": game.get_current_player().name,
            "message": f"Created new Monopoly game with {len(player_names)} players"
        }
    
    except Exception as e:
        return {"error": f"Failed to create game: {str(e)}"}

@mcp.tool()
def get_game_state(game_id: str) -> Dict[str, Any]:
    """
    Get the current state of a Monopoly game.
    
    Args:
        game_id: The ID of the game to query
        
    Returns:
        Dict with complete game state information
    """
    if game_id not in active_games:
        return {"error": f"Game {game_id} not found"}
    
    game = active_games[game_id]
    
    # Build player information
    players_info = []
    for player in game.players:
        player_info = {
            "name": player.name,
            "money": player.money,
            "position": player.position,
            "in_jail": player.jail_turns > 0,
            "jail_turns": player.jail_turns,
            "get_out_of_jail_free_cards": player.get_out_of_jail_free_cards,
            "properties": [prop.name for prop in player.properties],
            "total_wealth": player.total_wealth()
        }
        players_info.append(player_info)
    
    # Get board space name for current player
    current_player = game.get_current_player()
    current_space = game.board_spaces[current_player.position]
    
    return {
        "game_id": game_id,
        "game_over": game.game_over,
        "winner": game.winner.name if game.winner else None,
        "current_player": current_player.name,
        "current_player_position": current_player.position,
        "current_space": current_space.name,
        "houses_remaining": game.houses_remaining,
        "hotels_remaining": game.hotels_remaining,
        "players": players_info
    }

@mcp.tool()
def play_turn(game_id: str, player_name: str, action: str = "roll") -> Dict[str, Any]:
    """
    Play a turn for a player in the Monopoly game.
    
    Args:
        game_id: The ID of the game
        player_name: Name of the player taking the turn
        action: Action to take ("roll", "pay_jail", "use_jail_card")
        
    Returns:
        Dict with turn results and updated game state
    """
    if game_id not in active_games:
        return {"error": f"Game {game_id} not found"}
    
    game = active_games[game_id]
    
    # Check if it's the correct player's turn
    current_player = game.get_current_player()
    if current_player.name != player_name:
        return {"error": f"It's not {player_name}'s turn. Current player: {current_player.name}"}
    
    if game.game_over:
        return {"error": "Game is already over"}
    
    # Store initial state for comparison
    initial_money = current_player.money
    initial_position = current_player.position
    
    result = {"player": player_name, "action": action}
    
    try:
        if action == "roll":
            if current_player.jail_turns > 0:
                # Handle jail turn
                dice1, dice2 = game.roll_dice()
                result["dice"] = [dice1, dice2]
                result["doubles"] = dice1 == dice2
                
                if dice1 == dice2:
                    current_player.jail_turns = 0
                    # Move player
                    new_position = (current_player.position + dice1 + dice2) % 40
                    if new_position < current_player.position:
                        current_player.receive(200)  # Passed GO
                        result["passed_go"] = True
                    current_player.position = new_position
                    
                    # Handle landing on space
                    space = game.board_spaces[current_player.position]
                    result["landed_on"] = space.name
                    try:
                        game._handle_space_landing(current_player, space, dice1 + dice2)
                    except EOFError:
                        # Handle non-interactive mode - just note what happened
                        result["note"] = "Space requires interaction - handled automatically"
                else:
                    current_player.jail_turns += 1
                    if current_player.jail_turns >= 3:
                        # Must pay to get out
                        if current_player.can_afford(50):
                            current_player.pay(50)
                            current_player.jail_turns = 0
                            result["forced_jail_payment"] = True
                        else:
                            result["error"] = "Cannot afford jail fee and no other options"
            else:
                # Normal turn
                dice1, dice2 = game.roll_dice()
                result["dice"] = [dice1, dice2]
                result["doubles"] = dice1 == dice2
                
                # Move player
                new_position = (current_player.position + dice1 + dice2) % 40
                if new_position < current_player.position:
                    current_player.receive(200)  # Passed GO
                    result["passed_go"] = True
                current_player.position = new_position
                
                # Handle landing on space
                space = game.board_spaces[current_player.position]
                result["landed_on"] = space.name
                try:
                    game._handle_space_landing(current_player, space, dice1 + dice2)
                except EOFError:
                    # Handle non-interactive mode - just note what happened
                    result["note"] = "Space requires interaction - handled automatically"
                
                # Check for doubles
                if dice1 == dice2 and current_player.jail_turns == 0:
                    result["extra_turn"] = True
                else:
                    game.next_turn()
        
        elif action == "pay_jail":
            if current_player.jail_turns == 0:
                return {"error": "Player is not in jail"}
            if not current_player.can_afford(50):
                return {"error": "Player cannot afford jail fee"}
            
            current_player.pay(50)
            current_player.jail_turns = 0
            result["paid_jail_fee"] = True
            
        elif action == "use_jail_card":
            if current_player.jail_turns == 0:
                return {"error": "Player is not in jail"}
            if current_player.get_out_of_jail_free_cards <= 0:
                return {"error": "Player has no Get Out of Jail Free cards"}
            
            current_player.get_out_of_jail_free_cards -= 1
            current_player.jail_turns = 0
            result["used_jail_card"] = True
        
        else:
            return {"error": f"Unknown action: {action}"}
        
        # Add financial changes to result
        money_change = current_player.money - initial_money
        if money_change != 0:
            result["money_change"] = money_change
            result["new_money"] = current_player.money
        
        position_change = current_player.position - initial_position
        if position_change != 0:
            result["position_change"] = position_change
            result["new_position"] = current_player.position
        
        # Check if game is over
        game._check_game_over()
        if game.game_over:
            result["game_over"] = True
            result["winner"] = game.winner.name if game.winner else None
        
        return result
        
    except Exception as e:
        return {"error": f"Turn failed: {str(e)}"}

@mcp.tool()
def buy_property(game_id: str, player_name: str, property_name: str) -> Dict[str, Any]:
    """
    Buy a property for a player.
    
    Args:
        game_id: The ID of the game
        player_name: Name of the player buying
        property_name: Name of the property to buy
        
    Returns:
        Dict with purchase results
    """
    if game_id not in active_games:
        return {"error": f"Game {game_id} not found"}
    
    game = active_games[game_id]
    
    # Find the player
    player = None
    for p in game.players:
        if p.name == player_name:
            player = p
            break
    
    if not player:
        return {"error": f"Player {player_name} not found"}
    
    # Find the property at player's current position
    current_space = game.board_spaces[player.position]
    if current_space.property is None:
        return {"error": "No property at current location"}
    
    property = current_space.property
    if property.name != property_name:
        return {"error": f"Player is not on {property_name}"}
    
    if property.owner is not None:
        return {"error": f"{property_name} is already owned by {property.owner.name}"}
    
    if not player.can_afford(property.price):
        return {"error": f"Player cannot afford {property_name} (costs ${property.price})"}
    
    # Complete the purchase
    player.pay(property.price)
    property.owner = player
    player.properties.append(property)
    
    return {
        "success": True,
        "player": player_name,
        "property": property_name,
        "price": property.price,
        "remaining_money": player.money
    }

@mcp.tool()
def decline_property(game_id: str, player_name: str) -> Dict[str, Any]:
    """
    Decline to buy a property, triggering an auction.
    
    Args:
        game_id: The ID of the game
        player_name: Name of the player declining
        
    Returns:
        Dict with auction results
    """
    if game_id not in active_games:
        return {"error": f"Game {game_id} not found"}
    
    game = active_games[game_id]
    
    # Find the player
    player = None
    for p in game.players:
        if p.name == player_name:
            player = p
            break
    
    if not player:
        return {"error": f"Player {player_name} not found"}
    
    # Find the property at player's current position
    current_space = game.board_spaces[player.position]
    if current_space.property is None:
        return {"error": "No property at current location"}
    
    property = current_space.property
    if property.owner is not None:
        return {"error": f"{property.name} is already owned"}
    
    # Trigger auction (simplified - just assign to random player for now)
    # In a real implementation, this would be more interactive
    eligible_players = [p for p in game.players if p.can_afford(1)]
    if eligible_players:
        winner = random.choice(eligible_players)
        auction_price = max(1, property.price // 2)  # Simple auction logic
        
        if winner.can_afford(auction_price):
            winner.pay(auction_price)
            property.owner = winner
            winner.properties.append(property)
            
            return {
                "auction_held": True,
                "winner": winner.name,
                "price": auction_price,
                "property": property.name
            }
    
    return {
        "auction_held": True,
        "winner": None,
        "message": f"No one could afford {property.name} in auction"
    }

@mcp.tool()
def get_player_properties(game_id: str, player_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a player's properties.
    
    Args:
        game_id: The ID of the game
        player_name: Name of the player
        
    Returns:
        Dict with property information
    """
    if game_id not in active_games:
        return {"error": f"Game {game_id} not found"}
    
    game = active_games[game_id]
    
    # Find the player
    player = None
    for p in game.players:
        if p.name == player_name:
            player = p
            break
    
    if not player:
        return {"error": f"Player {player_name} not found"}
    
    properties_info = []
    for prop in player.properties:
        prop_info = {
            "name": prop.name,
            "color": prop.color.name,
            "price": prop.price,
            "houses": prop.houses,
            "is_mortgaged": prop.is_mortgaged,
            "mortgage_value": prop.mortgage_value,
            "rent": prop.get_rent_amount()
        }
        
        # Check if player owns monopoly
        if prop.color not in [PropertyColor.RAILROAD, PropertyColor.UTILITY]:
            prop_info["owns_monopoly"] = player.owns_monopoly(prop.color)
        
        properties_info.append(prop_info)
    
    return {
        "player": player_name,
        "properties": properties_info,
        "total_properties": len(properties_info)
    }

@mcp.tool()
def list_active_games() -> Dict[str, Any]:
    """
    List all active Monopoly games.
    
    Returns:
        Dict with information about all active games
    """
    games_info = []
    for game_id, game in active_games.items():
        game_info = {
            "game_id": game_id,
            "players": [player.name for player in game.players],
            "current_player": game.get_current_player().name,
            "game_over": game.game_over,
            "winner": game.winner.name if game.winner else None
        }
        games_info.append(game_info)
    
    return {
        "active_games": games_info,
        "total_games": len(games_info)
    }

@mcp.tool()
def get_board_info() -> Dict[str, Any]:
    """
    Get information about the Monopoly board layout.
    
    Returns:
        Dict with board space information
    """
    # Create a temporary game to get board info
    temp_game = MonopolyGame(["temp1", "temp2"])
    
    board_info = []
    for i, space in enumerate(temp_game.board_spaces):
        space_info = {
            "position": i,
            "name": space.name,
            "type": space.space_type.name
        }
        
        if space.property:
            space_info["property"] = {
                "color": space.property.color.name,
                "price": space.property.price,
                "rent_base": space.property.rent_base,
                "house_cost": space.property.house_cost
            }
        
        board_info.append(space_info)
    
    return {
        "board_spaces": board_info,
        "total_spaces": len(board_info)
    }

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()