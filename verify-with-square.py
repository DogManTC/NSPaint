import asyncio
import websockets
import json
import pygame
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Global variables
square_pos = [random.randint(50, 750), random.randint(50, 550)]  # initial position of the square
square_alpha = 128  # 50% transparency
actions_registered = False

# Define WebSocket server URL
ws_url = "ws://localhost:8000/"  # Change to "wss://" if using secure WebSocket

# Define actions
def register_actions():
    global actions_registered
    actions_registered = True
    actions = [
        {
            "name": "place",
            "description": "Place the square by making it 0% transparent.",
            "schema": {}
        },
        {
            "name": "shuffle",
            "description": "Shuffle the square's position by moving it randomly.",
            "schema": {}
        }
    ]
    register_message = {
        "command": "actions/register",
        "game": "Test Game",
        "data": {
            "actions": actions
        }
    }
    return register_message

# Define WebSocket message handler
async def handle_websocket():
    global square_pos, square_alpha, actions_registered

    try:
        # Connect to the WebSocket server
        async with websockets.connect(ws_url) as websocket:
            logging.info("WebSocket connection established!")

            # Register actions at the beginning
            await websocket.send(json.dumps(register_actions()))
            logging.info("Sent action registration message!")

            # Main WebSocket loop
            while True:
                # Wait for a message from the server
                message = await websocket.recv()
                logging.info(f"Received message: {message}")
                data = json.loads(message)

                # Handle specific commands
                if data.get("command") == "action":
                    action_name = data["data"]["name"]
                    if action_name == "shuffle":
                        # Shuffle square position
                        square_pos = [random.randint(50, 750), random.randint(50, 550)]
                        logging.info("Square shuffled to new position.")
                    elif action_name == "place":
                        # Place the square (make it fully opaque)
                        square_alpha = 255
                        logging.info("Square placed (fully opaque).")

                    # Send action result back to Randy
                    result_message = {
                        "command": "action/result",
                        "game": "Test Game",
                        "data": {
                            "id": data["data"]["id"],
                            "success": True,
                            "message": f"Action {action_name} completed."
                        }
                    }
                    await websocket.send(json.dumps(result_message))
                    logging.info(f"Sent action result: {result_message}")

                elif data.get("command") == "actions/reregister_all":
                    # Reregister actions if requested
                    logging.info("Reregistering actions.")
                    await websocket.send(json.dumps(register_actions()))
                    logging.info("Sent reregister actions message!")

    except Exception as e:
        logging.error(f"Error during WebSocket communication: {e}")

# Pygame window and handling
def run_pygame():
    global square_pos, square_alpha

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Randy Game Interface')

    # Create a surface for the square
    square = pygame.Surface((100, 100), pygame.SRCALPHA)
    square.fill((0, 0, 255, square_alpha))  # Blue square with transparency

    # Game loop
    running = True
    while running:
        screen.fill((255, 255, 255))  # Fill the screen with white

        # Draw the square at its current position
        screen.blit(square, (square_pos[0], square_pos[1]))

        # Update transparency if needed
        square.set_alpha(square_alpha)

        # Update the Pygame display
        pygame.display.flip()

        # Handle Pygame events (e.g., closing the window)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()

# Main function to run both WebSocket and Pygame
async def main():
    # Run the Pygame loop in the background
    pygame_task = asyncio.create_task(asyncio.to_thread(run_pygame))

    # Run the WebSocket communication loop
    await handle_websocket()

# Run the application
if __name__ == "__main__":
    asyncio.run(main())
