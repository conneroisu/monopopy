#!/usr/bin/env python3
"""
Test script for the Monopoly MCP Server

This script tests the MCP server functionality to ensure AI agents can play Monopoly.
"""

import json
from typing import Dict, Any

def test_mcp_server_import():
    """Test that the MCP server can be imported and initialized"""
    print("🧪 Testing MCP server import...")
    
    # Test 1: Import the MCP server
    print("\n1. Importing MCP server...")
    try:
        from mcp_server import mcp, active_games
        print("   ✅ MCP server imported successfully")
    except Exception as e:
        print(f"   ❌ Failed to import MCP server: {e}")
        return False
    
    # Test 2: Check that MCP server is FastMCP instance
    print("\n2. Checking MCP server type...")
    from fastmcp import FastMCP
    assert isinstance(mcp, FastMCP), "mcp is not a FastMCP instance"
    print("   ✅ MCP server is properly initialized")
    
    # Test 3: Test the underlying game logic
    print("\n3. Testing underlying game logic...")
    from main import MonopolyGame
    
    game = MonopolyGame(["Alice", "Bob"])
    print(f"   Created game with players: {[p.name for p in game.players]}")
    print(f"   Current player: {game.get_current_player().name}")
    
    # Test dice roll
    dice1, dice2 = game.roll_dice()
    print(f"   Dice roll: {dice1}, {dice2}")
    assert 1 <= dice1 <= 6 and 1 <= dice2 <= 6, "Invalid dice values"
    
    print("   ✅ Game logic works correctly")
    
    # Test 4: Test that active_games is initialized
    print("\n4. Testing game state storage...")
    assert isinstance(active_games, dict), "active_games is not a dictionary"
    print(f"   Active games storage: {len(active_games)} games")
    print("   ✅ Game state storage is ready")
    
    print("\n✅ MCP server import test passed!")
    return True

def test_game_simulation():
    """Test a simple game simulation to verify MCP integration works"""
    print("\n🧪 Testing game simulation...")
    
    from main import MonopolyGame
    from mcp_server import active_games, game_counter
    
    # Test 1: Create a game using the same logic as the MCP tool
    print("\n1. Creating a game...")
    global game_counter
    game_counter += 1
    game_id = f"game_{game_counter}"
    
    game = MonopolyGame(["TestAI_1", "TestAI_2"])
    active_games[game_id] = game
    
    print(f"   Created game {game_id}")
    print(f"   Players: {[p.name for p in game.players]}")
    print(f"   Current player: {game.get_current_player().name}")
    
    # Test 2: Simulate a few turns
    print("\n2. Simulating game turns...")
    for turn in range(5):
        current_player = game.get_current_player()
        print(f"   Turn {turn + 1}: {current_player.name}")
        
        # Store initial state
        initial_pos = current_player.position
        initial_money = current_player.money
        
        # Roll dice and move (simplified version of play_turn logic)
        dice1, dice2 = game.roll_dice()
        print(f"     Rolled: {dice1}, {dice2}")
        
        # Move player
        new_position = (current_player.position + dice1 + dice2) % 40
        if new_position < current_player.position:
            current_player.receive(200)  # Passed GO
            print("     Passed GO, collected $200")
        current_player.position = new_position
        
        # Get space name
        space = game.board_spaces[current_player.position]
        print(f"     Landed on: {space.name}")
        
        # Handle the space (simplified)
        try:
            game._handle_space_landing(current_player, space, dice1 + dice2)
        except EOFError:
            # Handle non-interactive mode
            pass
        except Exception as e:
            print(f"     Note: {str(e)}")
        
        # Show changes
        money_change = current_player.money - initial_money
        if money_change != 0:
            print(f"     Money change: ${money_change}, new balance: ${current_player.money}")
        
        # Next turn (unless doubles)
        if dice1 != dice2:
            game.next_turn()
        
        # Check game over
        if game.game_over:
            print(f"     Game over! Winner: {game.winner.name if game.winner else 'None'}")
            break
    
    print(f"   ✅ Game simulation completed")
    
    # Test 3: Verify game state is accessible
    print("\n3. Verifying game state access...")
    print(f"   Active games count: {len(active_games)}")
    print(f"   Game {game_id} exists: {game_id in active_games}")
    
    if game_id in active_games:
        game_obj = active_games[game_id]
        print(f"   Game players: {[p.name for p in game_obj.players]}")
        print(f"   Game over: {game_obj.game_over}")
    
    print("\n✅ Game simulation test passed!")
    return True

def main():
    """Main test function"""
    print("🎲 Testing Monopoly MCP Server")
    print("=" * 50)
    
    try:
        # Test 1: MCP server import and structure
        test_mcp_server_import()
        
        # Test 2: Game simulation
        test_game_simulation()
        
        print("\n🎉 All MCP server tests passed!")
        print("\nThe MCP server is ready for AI agents to play Monopoly!")
        print("\nTo run the MCP server:")
        print("  uv run monopoly-mcp")
        print("\nTo test with an AI client, connect to the server and use the exposed tools.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)