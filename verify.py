import asyncio
import websockets
import json

# Define the WebSocket server URI
ws_url = "ws://localhost:8000/"  # Change to "wss://" if using a secure WebSocket

# Function to send the WebSocket request and register actions
async def send_websocket_request():
    try:
        # Connect to the WebSocket server
        async with websockets.connect(ws_url) as websocket:
            print("WebSocket connection established!")

            # Define the actions to register
            actions = [
                {
                    "name": "join_friend_lobby",
                    "description": "Allows the player to join a friend's lobby.",
                    "schema": {
                        "friend_name": {"type": "string"}  # Schema for the friend's name
                    }
                },
                {
                    "name": "use_item",
                    "description": "Allows the player to use an item in their inventory.",
                    "schema": {
                        "item_id": {"type": "string"},
                        "quantity": {"type": "integer"}
                    }
                }
            ]

            # Register actions by sending the 'actions/register' message
            register_message = {
                "command": "actions/register",
                "game": "Test Game",  # Replace with your game name
                "data": {
                    "actions": actions
                }
            }

            # Send the register actions message
            await websocket.send(json.dumps(register_message))
            print("Sent action registration message!")

            # Optionally, you can receive a response from the server
            response = await websocket.recv()
            print(f"Received response: {response}")

    except Exception as e:
        print(f"Error during WebSocket communication: {e}")

# Main function to execute the script
async def main():
    await send_websocket_request()

# Run the script
if __name__ == "__main__":
    asyncio.run(main())
