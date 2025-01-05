# NSPaint - Neuro-Sama Paint
# using the neuro sdk documentation to allow Neuro-sama to create original artworks as well as collaborate with human artists
# but not yet this is just squares
# tested with the Tony graphical Neuro-api interface (https://github.com/Pasu4/neuro-api-tony)


import asyncio
import websockets
import json
import pygame
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Global variables
squares = []  # List to store all squares (position, transparency, and color)
max_squares = 10  # Max squares on screen (can be adjusted)

# Define WebSocket server URL
ws_url = "ws://localhost:8000/"  # Change to "wss://" if using secure WebSocket

# Define actions
def register_actions():
    actions = [
        {
            "name": "place",
            "description": "Place the most recent unplaced square by making it 0% transparent.",
            "schema": {}
        },
        {
            "name": "shuffle",
            "description": "Shuffle the square's position by moving it randomly.",
            "schema": {}
        },
        {
            "name": "spawn_square",
            "description": "Spawn a square at a specific position with specific RGB values.",
            "schema": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "rgb": {"type": "array", "items": {"type": "integer"}}
            }
        },
        {
            "name": "spawn_random_square",
            "description": "Spawn a square at a random position with random RGB values.",
            "schema": {}
        },
        {
            "name": "move_square",
            "description": "Move the current unplaced square to a new position.",
            "schema": {
                "x": {"type": "integer"},
                "y": {"type": "integer"}
            }
        }
    ]
    register_message = {
        "command": "actions/register",
        "game": "NeuroDraws",
        "data": {
            "actions": actions
        }
    }
    return register_message

# Define WebSocket message handler
async def handle_websocket():
    global squares

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
                    action_data = data["data"].get("data", {})
                    if action_name == "shuffle":
                        # Shuffle square position
                        if squares:
                            square = squares[-1]
                            square["x"] = random.randint(50, 750)  # Move square to a new random position
                            square["y"] = random.randint(50, 550)
                        logging.info("Square shuffled to new position.")
                    elif action_name == "place":
                        # Place the most recent unplaced square
                        for square in reversed(squares):
                            if not square["placed"]:
                                square["alpha"] = 255  # Fully opaque
                                square["placed"] = True
                                logging.info(f"Square at position {square['x'], square['y']} placed.")
                                break
                    elif action_name == "spawn_square":
                        try:
                            # Parse square data
                            square_data = json.loads(action_data)
                            x = square_data["x"]
                            y = square_data["y"]
                            rgb = square_data["rgb"]

                            # Ensure there is only one unplaced square
                            unplaced_squares = [sq for sq in squares if not sq["placed"]]
                            if unplaced_squares:
                                squares.remove(unplaced_squares[-1])

                            # Add the new square to the list
                            squares.append({
                                "x": x,
                                "y": y,
                                "color": rgb,
                                "alpha": 128,
                                "placed": False
                            })
                            logging.info(f"Spawned unplaced square at ({x}, {y}) with color {rgb}.")
                        except (KeyError, json.JSONDecodeError) as e:
                            logging.error(f"Failed to spawn square: {e}")
                            await websocket.send(json.dumps({
                                "command": "action/result",
                                "game": "NeuroDraws",
                                "data": {
                                    "id": data["data"]["id"],
                                    "success": False,
                                    "message": f"Error parsing square data: {e}"
                                }
                            }))
                            continue
                    elif action_name == "spawn_random_square":
                        # Spawn a random square
                        x = random.randint(50, 750)
                        y = random.randint(50, 550)
                        rgb = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

                        # Ensure there is only one unplaced square
                        unplaced_squares = [sq for sq in squares if not sq["placed"]]
                        if unplaced_squares:
                            squares.remove(unplaced_squares[-1])

                        # Add the new random square
                        squares.append({
                            "x": x,
                            "y": y,
                            "color": rgb,
                            "alpha": 128,
                            "placed": False
                        })
                        logging.info(f"Spawned random unplaced square at ({x}, {y}) with color {rgb}.")
                    elif action_name == "move_square":
                        try:
                            # Parse move data
                            move_data = json.loads(action_data)
                            x = move_data["x"]
                            y = move_data["y"]

                            # Move the most recent unplaced square
                            for square in reversed(squares):
                                if not square["placed"]:
                                    square["x"] = x
                                    square["y"] = y
                                    logging.info(f"Moved unplaced square to new position ({x}, {y}).")
                                    break
                        except (KeyError, json.JSONDecodeError) as e:
                            logging.error(f"Failed to move square: {e}")
                            await websocket.send(json.dumps({
                                "command": "action/result",
                                "game": "NeuroDraws",
                                "data": {
                                    "id": data["data"]["id"],
                                    "success": False,
                                    "message": f"Error parsing move data: {e}"
                                }
                            }))
                            continue

                    # Send action result back to Randy
                    result_message = {
                        "command": "action/result",
                        "game": "NeuroDraws",
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
    global squares

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('NeuroDraws')

    # Game loop
    running = True
    while running:
        screen.fill((255, 255, 255))  # Fill the screen with white

        # Draw each square
        for square in squares:
            surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            surface.fill((*square["color"], square["alpha"]))  # Apply transparency

            # Draw the square at its current position
            screen.blit(surface, (square["x"], square["y"]))

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
