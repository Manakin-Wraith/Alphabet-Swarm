# AlphabetSwarm.py
# A game where letters swarm around, and the player tries to spell a target word
# by typing the letters in the correct order.

# ------------- Imports -------------
import pygame
import random
import string
import math

# ------------- Pygame and Mixer Initialization -------------
pygame.init()
pygame.mixer.init() # Initialize the sound mixer

# ------------- Sound Setup -------------
# Placeholder paths for sound files
correct_sound_path = "correct.wav"
incorrect_sound_path = "incorrect.wav"
word_complete_sound_path = "word_complete.wav"

# Load sounds with error handling in case files are missing
try:
    correct_sound = pygame.mixer.Sound(correct_sound_path)
except pygame.error:
    correct_sound = None
    print(f"Warning: Sound file {correct_sound_path} not found. Correct letter sound will be disabled.")
try:
    incorrect_sound = pygame.mixer.Sound(incorrect_sound_path)
except pygame.error:
    incorrect_sound = None
    print(f"Warning: Sound file {incorrect_sound_path} not found. Incorrect letter sound will be disabled.")
try:
    word_complete_sound = pygame.mixer.Sound(word_complete_sound_path)
except pygame.error:
    word_complete_sound = None
    print(f"Warning: Sound file {word_complete_sound_path} not found. Word complete sound will be disabled.")

# ------------- Game Configuration / Variables -------------
# List of simple words for the player to spell
simple_words = ["CAT", "DOG", "SUN", "BIG", "RED", "FUN"]

# Game window settings
window_width = 1000
window_height = 700
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Alphabet Swarm")

# Colors used in the game
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)   # Color for correctly guessed letters in the target word
YELLOW = (255, 255, 0) # Color for letters pressed that are in the word but not next
RED = (255, 0, 0)     # Color for letters pressed that are not in the word

# Attributes for the swarming letters
default_letter_size = 40    # Default size of the swarming letters
default_letter_speed = 2    # Maximum speed of the swarming letters
num_letters = 26            # Total number of unique alphabet letters to display
letters = list(string.ascii_uppercase) # List of 'A' through 'Z'

# ------------- Initial Game State Setup -------------
# Select the first word for the player to spell
target_word = random.choice(simple_words)
# Index to track the current letter to be guessed in the target_word
current_letter_index = 0

# Lists to store attributes of each swarming letter
letter_positions = []  # Stores (x, y) coordinates
letter_velocities = [] # Stores (vx, vy) velocities
# Stores colors of individual swarming letters. These change based on player input.
letter_colors = []

# Initialize positions, velocities, and random colors for each of the 26 alphabet letters
for i in range(num_letters):
    x = random.randint(0, window_width - default_letter_size)
    y = random.randint(0, window_height - default_letter_size)
    angle = random.uniform(0, 2 * math.pi)
    speed = random.randint(1, default_letter_speed)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    letter_positions.append((x, y))
    letter_velocities.append((vx, vy))
    # Each letter (A-Z) gets a random initial color. This list is parallel to 'letters'.
    letter_colors.append((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

# Pygame clock for controlling frame rate
clock = pygame.time.Clock()

# Game parameters (some might be adjustable in the future)
letter_speed = default_letter_speed # Current effective speed of letters (can be changed)

# Timestamp for displaying feedback messages (e.g., "Well Done!")
show_feedback_message_until = 0 # 0 means no message active

# ------------- Main Game Loop -------------
running = True
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            pressed_key_letter = event.unicode.upper() # Get the pressed key, convert to uppercase

            # Check if the pressed key is an alphabet letter
            if pressed_key_letter in letters:
                # Process letter press only if there's a target word and it's not fully spelled yet
                if target_word and current_letter_index < len(target_word):
                    expected_letter = target_word[current_letter_index]

                    # Find the index of the pressed physical letter on screen (A-Z)
                    # This index is used to change its color in 'letter_colors'.
                    try:
                        char_display_index = letters.index(pressed_key_letter)
                    except ValueError:
                        # This should ideally not happen if pressed_key_letter is in 'letters'
                        char_display_index = -1

                    # --- Game Logic: Check pressed letter ---
                    if pressed_key_letter == expected_letter:
                        current_letter_index += 1 # Move to the next letter in the target word
                        if char_display_index != -1:
                            # Change color of the correctly pressed letter to GREEN
                            letter_colors[char_display_index] = GREEN

                        if correct_sound:
                            correct_sound.play()

                        # --- Game Logic: Word Completion Check ---
                        if current_letter_index == len(target_word):
                            if word_complete_sound:
                                word_complete_sound.play()

                            # Activate "Well Done!" message display for 2 seconds
                            show_feedback_message_until = pygame.time.get_ticks() + 2000

                            # Select a new target word
                            target_word = random.choice(simple_words)
                            current_letter_index = 0 # Reset progress for the new word

                            # Reset all on-screen letter colors to new random colors
                            for i in range(len(letter_colors)):
                                letter_colors[i] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

                    elif pressed_key_letter in target_word: # Incorrect letter, but it's in the target word
                        if char_display_index != -1:
                            # Change color to YELLOW if not already correctly guessed (GREEN)
                            if letter_colors[char_display_index] != GREEN:
                                letter_colors[char_display_index] = YELLOW
                        if incorrect_sound:
                            incorrect_sound.play()

                    else: # Incorrect letter, and it's not in the target word
                        if char_display_index != -1:
                            # Change color to RED if not already correctly guessed (GREEN)
                            if letter_colors[char_display_index] != GREEN:
                                letter_colors[char_display_index] = RED
                        if incorrect_sound:
                            incorrect_sound.play()

    # --- Drawing / Rendering ---
    # Clear the screen with black
    window.fill(BLACK)

    # Display the current target word at the top-center
    font_target_word = pygame.font.Font(None, 50) # Default font, size 50
    text_target_word = font_target_word.render(target_word, True, WHITE)
    text_rect_target_word = text_target_word.get_rect(center=(window_width // 2, 30))
    window.blit(text_target_word, text_rect_target_word)

    # Display "Well Done!" feedback message if active
    if pygame.time.get_ticks() < show_feedback_message_until:
        font_feedback = pygame.font.Font(None, 60)
        text_feedback = font_feedback.render("Well Done!", True, GREEN)
        text_rect_feedback = text_feedback.get_rect(center=(window_width // 2, window_height // 2))
        window.blit(text_feedback, text_rect_feedback)

    # Update and draw each swarming letter
    for i, (x, y) in enumerate(letter_positions):
        vx, vy = letter_velocities[i]

        # Move letter
        x += vx
        y += vy

        # Bounce off window boundaries
        if x < 0 or x > window_width - default_letter_size:
            vx = -vx
        if y < 0 or y > window_height - default_letter_size:
            vy = -vy

        # Update lists with new positions and velocities
        letter_positions[i] = (x, y)
        letter_velocities[i] = (vx, vy)

        # Get the current color for this specific letter (A-Z)
        letter_color = letter_colors[i]
        # All swarming letters now use the default size
        current_letter_size = default_letter_size

        # Render and draw the letter
        font = pygame.font.Font(None, current_letter_size)
        letter_surface = font.render(letters[i], True, letter_color)
        window.blit(letter_surface, (x, y))

    # Update the full display
    pygame.display.update()

    # Cap the frame rate to 120 FPS
    clock.tick(120)

# ------------- Game Exit -------------
pygame.quit()
