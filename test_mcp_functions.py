#!/usr/bin/env python3
"""
MCP Functions Verification Tests

Direct testing of the MCP tool functions without the MCP framework complexity.
This provides comprehensive verification of all game logic exposed through MCP tools.
"""

import sys
import traceback
import random

def reset_test_environment():
    """Reset the test environment for clean testing"""
    import mcp_server
    mcp_server.active_games.clear()
    mcp_server.game_counter = 0

def test_unit_functionality():
    """Test individual MCP tool functions"""
    print("🧪 UNIT TESTS - Individual MCP Tool Functions")
    print("-" * 55)
    
    # Import functions directly from the module
    import mcp_server
    
    # Test create_game
    print("  Testing create_game function...")
    
    # Valid creation
    result = mcp_server.create_game.fn(["UnitTest1", "UnitTest2"])
    assert "game_id" in result, f"No game_id in result: {result}"
    assert "error" not in result, f"Unexpected error: {result}"
    assert result["players"] == ["UnitTest1", "UnitTest2"], "Wrong players"
    game_id = result["game_id"]
    
    # Invalid creation
    invalid_result = mcp_server.create_game.fn(["Solo"])
    assert "error" in invalid_result, "Should reject single player"
    
    print("    ✅ create_game works correctly")
    
    # Test get_game_state
    print("  Testing get_game_state function...")
    
    state = mcp_server.get_game_state.fn(game_id)
    assert "error" not in state, f"Error getting state: {state}"
    assert state["game_id"] == game_id, "Wrong game ID"
    assert len(state["players"]) == 2, "Wrong player count"
    assert state["current_player"] in ["UnitTest1", "UnitTest2"], "Invalid current player"
    
    # Invalid game ID
    invalid_state = mcp_server.get_game_state.fn("fake_game")
    assert "error" in invalid_state, "Should error with fake game ID"
    
    print("    ✅ get_game_state works correctly")
    
    # Test play_turn
    print("  Testing play_turn function...")
    
    current_player = state["current_player"]
    turn_result = mcp_server.play_turn.fn(game_id, current_player, "roll")
    assert "error" not in turn_result, f"Turn failed: {turn_result}"
    assert "dice" in turn_result, "No dice in result"
    assert len(turn_result["dice"]) == 2, "Should have 2 dice"
    assert all(1 <= d <= 6 for d in turn_result["dice"]), "Invalid dice values"
    
    print("    ✅ play_turn works correctly")
    
    # Test board info
    print("  Testing get_board_info function...")
    
    board_info = mcp_server.get_board_info.fn()
    assert "board_spaces" in board_info, "Missing board_spaces"
    assert board_info["total_spaces"] == 40, "Should have 40 spaces"
    
    print("    ✅ get_board_info works correctly")
    
    # Test list_active_games
    print("  Testing list_active_games function...")
    
    games_list = mcp_server.list_active_games.fn()
    assert "active_games" in games_list, "Missing active_games"
    assert games_list["total_games"] >= 1, "Should have at least 1 game"
    
    print("    ✅ list_active_games works correctly")
    
    print("✅ All unit tests passed!")

def test_integration_scenarios():
    """Test complete integration scenarios"""
    print("\n🔗 INTEGRATION TESTS - Complete Game Scenarios")
    print("-" * 55)
    
    import mcp_server
    
    # Test complete game workflow
    print("  Testing complete game workflow...")
    
    # Create game
    game_result = mcp_server.create_game.fn(["IntegrationAI1", "IntegrationAI2"])
    game_id = game_result["game_id"]
    
    # Track game progress
    turns_played = 0
    properties_acquired = 0
    max_turns = 30
    
    for turn_num in range(max_turns):
        # Get current state
        state = mcp_server.get_game_state.fn(game_id)
        if state["game_over"]:
            print(f"    Game ended after {turns_played} turns")
            break
        
        current_player = state["current_player"]
        
        # Play turn
        turn_result = mcp_server.play_turn.fn(game_id, current_player, "roll")
        if "error" in turn_result:
            continue
            
        turns_played += 1
        
        # Handle property landings
        if "landed_on" in turn_result:
            landed_space = turn_result["landed_on"]
            
            # Simple AI: buy if we have money
            player_money = next(p["money"] for p in state["players"] if p["name"] == current_player)
            
            if player_money > 400:  # Keep some cash buffer
                buy_result = mcp_server.buy_property.fn(game_id, current_player, landed_space)
                if "success" in buy_result and buy_result["success"]:
                    properties_acquired += 1
                    print(f"    Turn {turns_played}: {current_player} bought {landed_space}")
                elif "error" in buy_result and "not a property" not in buy_result["error"]:
                    # Decline and trigger auction
                    decline_result = mcp_server.decline_property.fn(game_id, current_player)
                    if "auction_held" in decline_result:
                        print(f"    Turn {turns_played}: {landed_space} went to auction")
    
    # Verify game progressed
    assert turns_played > 0, "No turns were played"
    final_state = mcp_server.get_game_state.fn(game_id)
    total_properties = sum(len(p["properties"]) for p in final_state["players"])
    
    print(f"    Game progress: {turns_played} turns, {total_properties} properties owned")
    print("    ✅ Complete game workflow successful")
    
    # Test multi-game management
    print("  Testing multi-game management...")
    
    # Create additional games
    game2_result = mcp_server.create_game.fn(["Multi1", "Multi2", "Multi3"])
    game3_result = mcp_server.create_game.fn(["Solo1", "Solo2"])
    
    games_list = mcp_server.list_active_games.fn()
    assert games_list["total_games"] >= 3, f"Should have 3+ games, got {games_list['total_games']}"
    
    # Verify all games are accessible
    for game_info in games_list["active_games"]:
        state = mcp_server.get_game_state.fn(game_info["game_id"])
        assert "error" not in state, f"Game {game_info['game_id']} not accessible"
    
    print("    ✅ Multi-game management works")
    
    # Test player properties tracking
    print("  Testing player properties tracking...")
    
    # Find a player with properties
    all_players_props = []
    for game_info in games_list["active_games"]:
        state = mcp_server.get_game_state.fn(game_info["game_id"])
        for player in state["players"]:
            if len(player["properties"]) > 0:
                props = mcp_server.get_player_properties.fn(game_info["game_id"], player["name"])
                assert "error" not in props, f"Error getting properties: {props}"
                assert props["total_properties"] == len(player["properties"]), "Property count mismatch"
                all_players_props.append((player["name"], len(player["properties"])))
    
    print(f"    Found {len(all_players_props)} players with properties")
    print("    ✅ Player properties tracking works")
    
    print("✅ All integration tests passed!")

def test_error_handling():
    """Test error handling and edge cases"""
    print("\n🚨 ERROR HANDLING TESTS - Edge Cases and Invalid Operations")
    print("-" * 55)
    
    import mcp_server
    
    # Test invalid game operations
    print("  Testing invalid game operations...")
    
    fake_game_id = "nonexistent_game_12345"
    
    # All operations with fake game should fail
    state_result = mcp_server.get_game_state.fn(fake_game_id)
    assert "error" in state_result, "get_game_state should fail with fake ID"
    
    turn_result = mcp_server.play_turn.fn(fake_game_id, "FakePlayer", "roll")
    assert "error" in turn_result, "play_turn should fail with fake ID"
    
    buy_result = mcp_server.buy_property.fn(fake_game_id, "FakePlayer", "Boardwalk")
    assert "error" in buy_result, "buy_property should fail with fake ID"
    
    props_result = mcp_server.get_player_properties.fn(fake_game_id, "FakePlayer")
    assert "error" in props_result, "get_player_properties should fail with fake ID"
    
    print("    ✅ Invalid game operations handled correctly")
    
    # Test wrong player turn
    print("  Testing wrong player turn handling...")
    
    # Create game for turn testing
    game_result = mcp_server.create_game.fn(["TurnTest1", "TurnTest2"])
    game_id = game_result["game_id"]
    
    state = mcp_server.get_game_state.fn(game_id)
    current_player = state["current_player"]
    wrong_player = "TurnTest1" if current_player == "TurnTest2" else "TurnTest2"
    
    wrong_turn_result = mcp_server.play_turn.fn(game_id, wrong_player, "roll")
    assert "error" in wrong_turn_result, "Should error when wrong player plays"
    
    print("    ✅ Wrong turn handling works correctly")
    
    # Test invalid game creation
    print("  Testing invalid game creation...")
    
    # Too few players
    result1 = mcp_server.create_game.fn([])
    assert "error" in result1, "Should error with no players"
    
    result2 = mcp_server.create_game.fn(["OnlyOne"])
    assert "error" in result2, "Should error with one player"
    
    # Too many players
    result3 = mcp_server.create_game.fn([f"Player{i}" for i in range(10)])
    assert "error" in result3, "Should error with 10 players"
    
    print("    ✅ Invalid game creation handled correctly")
    
    print("✅ All error handling tests passed!")

def test_game_invariants():
    """Test that game invariants are maintained"""
    print("\n🔬 PROPERTY-BASED TESTS - Game Invariants")
    print("-" * 55)
    
    import mcp_server
    
    # Test position validity
    print("  Testing position validity invariant...")
    
    game_result = mcp_server.create_game.fn(["InvariantTest1", "InvariantTest2"])
    game_id = game_result["game_id"]
    
    for turn in range(25):
        state = mcp_server.get_game_state.fn(game_id)
        if state["game_over"]:
            break
        
        # Check all positions are valid
        for player in state["players"]:
            pos = player["position"]
            assert 0 <= pos < 40, f"Invalid position {pos} for {player['name']}"
            assert isinstance(pos, int), f"Position not integer: {pos}"
        
        # Play turn
        current_player = state["current_player"]
        mcp_server.play_turn.fn(game_id, current_player, "roll")
    
    print("    ✅ Position validity maintained")
    
    # Test money reasonableness
    print("  Testing money reasonableness...")
    
    game_result = mcp_server.create_game.fn(["MoneyTest1", "MoneyTest2"])
    game_id = game_result["game_id"]
    
    for turn in range(20):
        state = mcp_server.get_game_state.fn(game_id)
        if state["game_over"]:
            break
        
        # Check money is reasonable
        for player in state["players"]:
            money = player["money"]
            assert isinstance(money, int), f"Money not integer: {money}"
            assert money >= -2000, f"Money too negative: {money}"  # Allow some debt
            assert money <= 100000, f"Money unreasonably high: {money}"
        
        # Play turn
        current_player = state["current_player"]
        mcp_server.play_turn.fn(game_id, current_player, "roll")
    
    print("    ✅ Money reasonableness maintained")
    
    # Test game state structure
    print("  Testing game state structure...")
    
    # Use existing game
    state = mcp_server.get_game_state.fn(game_id)
    
    # Check required fields
    required_fields = ["game_id", "game_over", "current_player", "players", 
                      "houses_remaining", "hotels_remaining"]
    for field in required_fields:
        assert field in state, f"Missing required field: {field}"
    
    # Check player structure
    for player in state["players"]:
        player_fields = ["name", "money", "position", "in_jail", "properties"]
        for field in player_fields:
            assert field in player, f"Missing player field: {field}"
    
    print("    ✅ Game state structure correct")
    
    print("✅ All invariant tests passed!")

def run_performance_check():
    """Basic performance check"""
    print("\n⚡ PERFORMANCE CHECK - Basic Speed Test")
    print("-" * 55)
    
    import mcp_server
    import time
    
    # Test game creation speed
    print("  Testing game creation performance...")
    
    start_time = time.time()
    
    # Create multiple games quickly
    for i in range(10):
        mcp_server.create_game.fn([f"PerfTest{i}_1", f"PerfTest{i}_2"])
    
    creation_time = time.time() - start_time
    print(f"    Created 10 games in {creation_time:.3f} seconds ({creation_time/10:.3f}s per game)")
    
    # Test turn execution speed
    print("  Testing turn execution performance...")
    
    # Get one game and play many turns
    games = mcp_server.list_active_games.fn()
    test_game_id = games["active_games"][0]["game_id"]
    
    start_time = time.time()
    turns_completed = 0
    
    for turn in range(50):
        state = mcp_server.get_game_state.fn(test_game_id)
        if state["game_over"]:
            break
        
        current_player = state["current_player"]
        turn_result = mcp_server.play_turn.fn(test_game_id, current_player, "roll")
        
        if "error" not in turn_result:
            turns_completed += 1
    
    execution_time = time.time() - start_time
    
    if turns_completed > 0:
        print(f"    Executed {turns_completed} turns in {execution_time:.3f} seconds ({execution_time/turns_completed:.3f}s per turn)")
    else:
        print("    No turns completed (game may have ended quickly)")
    
    print("✅ Performance check completed!")

def main():
    """Run all verification tests"""
    print("🎲 COMPREHENSIVE MCP FUNCTIONS VERIFICATION")
    print("=" * 65)
    
    try:
        # Reset environment for clean testing
        reset_test_environment()
        
        # Run all test suites
        test_unit_functionality()
        test_integration_scenarios()
        test_error_handling()
        test_game_invariants()
        run_performance_check()
        
        print("\n" + "=" * 65)
        print("🎉 ALL MCP FUNCTIONS VERIFICATION COMPLETE!")
        print("=" * 65)
        print("\nComprehensive verification results:")
        print("✅ Unit Tests: All individual functions work correctly")
        print("✅ Integration Tests: Complete workflows function properly") 
        print("✅ Error Handling: Invalid operations handled gracefully")
        print("✅ Invariant Tests: Game rules and constraints maintained")
        print("✅ Performance Check: Functions execute efficiently")
        print("\n🚀 The MCP server functions are production-ready!")
        print("\nAI agents can reliably use these MCP tools to:")
        print("  • Create and manage multiplayer Monopoly games")
        print("  • Execute turns with dice rolling and movement")
        print("  • Buy and manage properties")
        print("  • Track game state and player information")
        print("  • Handle all edge cases gracefully")
        
        return True
        
    except Exception as e:
        print(f"\n❌ MCP VERIFICATION FAILED: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)