# 🤖 Monopoly MCP Server - AI Agent Usage Guide

This document explains how AI agents (LLMs) can connect to and play the Monopoly game using the Model Context Protocol (MCP) server.

## 🚀 Quick Start

### Starting the MCP Server

```bash
# Install dependencies
uv sync

# Start the MCP server
uv run monopoly-mcp
```

The server will start and listen for MCP client connections.

### Connecting AI Agents

AI agents can connect to the server using any MCP-compatible client. The server exposes the following tools:

## 🛠 Available MCP Tools

### Game Management

#### `create_game`
Create a new Monopoly game with specified players.

**Parameters:**
- `player_names` (List[str]): List of 2-8 player names

**Returns:**
```json
{
  "game_id": "game_1",
  "players": ["AI_Agent_1", "AI_Agent_2"],
  "current_player": "AI_Agent_1",
  "message": "Created new Monopoly game with 2 players"
}
```

#### `list_active_games`
List all active Monopoly games.

**Returns:**
```json
{
  "active_games": [
    {
      "game_id": "game_1",
      "players": ["Alice", "Bob"],
      "current_player": "Alice",
      "game_over": false,
      "winner": null
    }
  ],
  "total_games": 1
}
```

### Game State

#### `get_game_state`
Get the current state of a Monopoly game.

**Parameters:**
- `game_id` (str): The ID of the game to query

**Returns:**
```json
{
  "game_id": "game_1",
  "game_over": false,
  "winner": null,  
  "current_player": "Alice",
  "current_player_position": 5,
  "current_space": "Reading Railroad",
  "houses_remaining": 32,
  "hotels_remaining": 12,
  "players": [
    {
      "name": "Alice",
      "money": 1500,
      "position": 5,
      "in_jail": false,
      "jail_turns": 0,
      "get_out_of_jail_free_cards": 0,
      "properties": ["Mediterranean Avenue"],
      "total_wealth": 1560
    }
  ]
}
```

#### `get_player_properties`
Get detailed information about a player's properties.

**Parameters:**
- `game_id` (str): The ID of the game
- `player_name` (str): Name of the player

**Returns:**
```json
{
  "player": "Alice",
  "properties": [
    {
      "name": "Mediterranean Avenue",
      "color": "BROWN",
      "price": 60,
      "houses": 0,
      "is_mortgaged": false,
      "mortgage_value": 30,
      "rent": 4,
      "owns_monopoly": false
    }
  ],
  "total_properties": 1
}
```

### Gameplay Actions

#### `play_turn`
Play a turn for a player in the Monopoly game.

**Parameters:**
- `game_id` (str): The ID of the game
- `player_name` (str): Name of the player taking the turn
- `action` (str): Action to take ("roll", "pay_jail", "use_jail_card")

**Returns:**
```json
{
  "player": "Alice",
  "action": "roll",
  "dice": [3, 4],
  "doubles": false,
  "landed_on": "Connecticut Avenue",
  "money_change": -120,
  "new_money": 1380,
  "position_change": 7,
  "new_position": 9
}
```

#### `buy_property`
Buy a property for a player.

**Parameters:**
- `game_id` (str): The ID of the game
- `player_name` (str): Name of the player buying
- `property_name` (str): Name of the property to buy

**Returns:**
```json
{
  "success": true,
  "player": "Alice",
  "property": "Connecticut Avenue",
  "price": 120,
  "remaining_money": 1380
}
```

#### `decline_property`
Decline to buy a property, triggering an auction.

**Parameters:**
- `game_id` (str): The ID of the game
- `player_name` (str): Name of the player declining

**Returns:**
```json
{
  "auction_held": true,
  "winner": "Bob",
  "price": 60,
  "property": "Connecticut Avenue"
}
```

### Board Information

#### `get_board_info`
Get information about the Monopoly board layout.

**Returns:**
```json
{
  "board_spaces": [
    {
      "position": 0,
      "name": "GO",
      "type": "GO"
    },
    {
      "position": 1,
      "name": "Mediterranean Avenue",
      "type": "PROPERTY",
      "property": {
        "color": "BROWN",
        "price": 60,
        "rent_base": 2,
        "house_cost": 50
      }
    }
  ],
  "total_spaces": 40
}
```

## 🎮 AI Agent Gameplay Strategy

### Basic Gameplay Loop

1. **Join/Create Game**: Use `create_game` to start a new game
2. **Check Turn**: Use `get_game_state` to see if it's your turn
3. **Play Turn**: Use `play_turn` with action "roll" to roll dice and move
4. **Handle Landing**: Based on where you land:
   - **Property**: Use `buy_property` or `decline_property`
   - **Special spaces**: Handle automatically (taxes, cards, etc.)
5. **Repeat**: Continue until game ends

### Example AI Turn Sequence

```python
# 1. Check if it's my turn
state = mcp_client.call_tool("get_game_state", {"game_id": "game_1"})
if state["current_player"] != "MyAI":
    return  # Not my turn

# 2. Play turn (roll dice)
turn_result = mcp_client.call_tool("play_turn", {
    "game_id": "game_1",
    "player_name": "MyAI",
    "action": "roll"
})

# 3. Handle property purchase decision
if "landed_on" in turn_result:
    # Simple strategy: buy if affordable and good value
    state = mcp_client.call_tool("get_game_state", {"game_id": "game_1"})
    my_money = next(p["money"] for p in state["players"] if p["name"] == "MyAI")
    
    if my_money > 300:  # Keep some cash buffer
        mcp_client.call_tool("buy_property", {
            "game_id": "game_1",
            "player_name": "MyAI",
            "property_name": turn_result["landed_on"]
        })
    else:
        mcp_client.call_tool("decline_property", {
            "game_id": "game_1",
            "player_name": "MyAI"
        })
```

## 🧠 Advanced AI Strategies

### Property Investment Strategy
- **Early Game**: Focus on completing color groups (monopolies)
- **Mid Game**: Build houses/hotels on monopolies
- **Late Game**: Manage cash flow and debt

### Risk Management
- Keep cash reserves for rent payments
- Monitor opponent property ownership
- Calculate expected returns on property investments

### Competitive Analysis
- Track opponent wealth and property portfolios
- Identify blocking opportunities
- Time trades strategically

## 🔧 Integration Examples

### Claude Desktop Integration

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "monopoly": {
      "command": "uv",
      "args": ["run", "monopoly-mcp"],
      "cwd": "/path/to/monopopy"
    }
  }
}
```

### Python Client Example

```python
from fastmcp.client import FastMCPClient

async def play_monopoly():
    client = FastMCPClient()
    
    # Create game
    result = await client.call_tool("create_game", {
        "player_names": ["AI_1", "AI_2"]
    })
    game_id = result["game_id"]
    
    # Game loop
    while True:
        state = await client.call_tool("get_game_state", {"game_id": game_id})
        
        if state["game_over"]:
            print(f"Game over! Winner: {state['winner']}")
            break
            
        current_player = state["current_player"]
        
        # Play turn for current player
        turn_result = await client.call_tool("play_turn", {
            "game_id": game_id,
            "player_name": current_player,
            "action": "roll"
        })
        
        print(f"{current_player} rolled {turn_result['dice']}")
        
        # Handle property purchases with simple AI logic
        if "landed_on" in turn_result:
            # Buy if we have enough money
            player_data = next(p for p in state["players"] if p["name"] == current_player)
            if player_data["money"] > 500:
                await client.call_tool("buy_property", {
                    "game_id": game_id,
                    "player_name": current_player,
                    "property_name": turn_result["landed_on"]
                })
```

## 🎯 Testing Your AI Agent

Use the provided test script to verify your MCP integration:

```bash
uv run python test_mcp_server.py
```

This will verify that:
- The MCP server starts correctly
- All tools are properly registered
- Basic game functionality works
- Game state is properly managed

## 📊 Game Rules Summary

For AI agents to play effectively, they should understand:

- **Objective**: Be the last player with money (eliminate opponents through bankruptcy)
- **Turn Flow**: Roll dice → Move → Handle space → End turn
- **Property System**: Buy properties → Build monopolies → Collect rent
- **Cash Management**: Balance property investment with cash reserves
- **Special Spaces**: Handle Chance/Community Chest cards, taxes, jail

## 🚀 Getting Started Checklist

- [ ] Install dependencies: `uv sync`
- [ ] Test MCP server: `uv run python test_mcp_server.py`
- [ ] Start MCP server: `uv run monopoly-mcp`
- [ ] Connect your AI client to the server
- [ ] Create a game with `create_game`
- [ ] Implement basic turn-taking logic
- [ ] Add property purchase decision-making
- [ ] Test with multiple AI agents

The Monopoly MCP server provides a complete, production-ready interface for AI agents to play the classic board game. Have fun building intelligent agents that can master the art of property trading and wealth management!