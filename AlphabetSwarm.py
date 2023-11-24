import pygame
import random
import string
import math

# Initialize Pygame
pygame.init()

# Set up the game window
window_width = 1000
window_height = 700
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Alphabet Swarm")

# Set up colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Set up letter attributes
default_letter_size = 40
default_letter_speed = 2
num_letters = 26
letters = list(string.ascii_uppercase)

# Create a list to store letter positions and velocities
letter_positions = []
letter_velocities = []
letter_colors = []  # New list to store letter colors

for _ in range(num_letters):
    x = random.randint(0, window_width - default_letter_size)
    y = random.randint(0, window_height - default_letter_size)
    angle = random.uniform(0, 2 * math.pi)
    speed = random.randint(1, default_letter_speed)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    letter_positions.append((x, y))
    letter_velocities.append((vx, vy))
    letter_colors.append((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))  # Generate random colors

clock = pygame.time.Clock()

# Adjustable parameters
letter_size = default_letter_size
letter_speed = default_letter_speed

# New variable to store the selected letter
selected_letter = None

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Check if the pressed key matches a letter in the swarm
            if event.unicode.upper() in letters:
                selected_letter = event.unicode.upper()
                letter_size = 150  # Change the letter size to 150 when a letter is pressed

    # Clear the screen
    window.fill(BLACK)

    # Update letter positions
    for i, (x, y) in enumerate(letter_positions):
        vx, vy = letter_velocities[i]

        # Update letter position
        x += vx
        y += vy

        # Keep the letters within the window boundaries
        if x < 0 or x > window_width - letter_size:
            vx = -vx
        if y < 0 or y > window_height - letter_size:
            vy = -vy

        # Update letter position and velocity in the lists
        letter_positions[i] = (x, y)
        letter_velocities[i] = (vx, vy)

        # Get the color and size for the letter
        letter_color = letter_colors[i]
        current_letter_size = letter_size if letters[i] == selected_letter else default_letter_size

        # Draw the letter on the screen with the color and size
        font = pygame.font.Font(None, current_letter_size)
        letter_surface = font.render(letters[i], True, letter_color)
        window.blit(letter_surface, (x, y))

    # Update the display
    pygame.display.update()

    # Limit the frame rate
    clock.tick(120)

# Quit the game
pygame.quit()
