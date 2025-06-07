# AlphabetSwarm.py
# A game where letters swarm around, and the player tries to spell a target word
# by typing the letters in the correct order using a two-step preview/confirm mechanism.

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
WORD_LIST_FILENAME = "words.txt"
DEFAULT_SIMPLE_WORDS = ["CAT", "DOG", "SUN", "BIG", "RED", "FUN", "EAT", "RUN", "TOP", "HOT", "POT", "SKY", "FLY", "TRY"]

def load_words_from_file(filename):
    """Loads words from a file, filters them, and returns a list of valid words."""
    valid_words = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                word = line.strip().upper()
                if 3 <= len(word) <= 5 and word.isalpha():
                    valid_words.append(word)
        if not valid_words:
            print(f"Info: No valid words (3-5 letters, alpha only) found in '{filename}'.")
        else:
            print(f"Info: Successfully loaded {len(valid_words)} words from '{filename}'.")
    except FileNotFoundError:
        print(f"Info: Word file '{filename}' not found.")
    return valid_words

# Load words or use default
simple_words = load_words_from_file(WORD_LIST_FILENAME)
if not simple_words:
    simple_words = DEFAULT_SIMPLE_WORDS
    print(f"Info: Using default word list of {len(simple_words)} words.")

if not simple_words: # Should ideally not happen if DEFAULT_SIMPLE_WORDS is populated
    print("CRITICAL ERROR: No words available to play the game. Exiting.")
    pygame.quit()
    import sys
    sys.exit()


# Game window settings
window_width = 1000
window_height = 700
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Alphabet Swarm")

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)   # Color for correctly guessed/animating letters
RED = (255, 0, 0)     # Color for feedback flash on incorrect confirmation

# --- Letter States ---
# Defines the behavior and appearance of the swarming letters.
STATE_NORMAL = "normal"      # Default state: swarming randomly.
STATE_PREVIEW = "preview"    # Letter is previewed by player: enlarged, slowed down.
STATE_ANIMATING_TO_SLOT = "animating_to_slot" # Letter is confirmed correct and moving to its slot.
STATE_PLACED = "placed"      # Letter has reached its slot in the target word.

# --- Animation and Preview Constants ---
ANIMATION_SPEED = 10  # Speed (pixels per frame) of letter animation to the slot.
PREVIEW_DURATION_MS = 3000  # Duration (ms) a letter stays in preview before reverting.
PREVIEW_SPEED_FACTOR = 0.5  # Factor by which letter speed is reduced during preview.
ENLARGED_LETTER_SIZE_FACTOR = 5.0 # Factor by which letter size is increased during preview.

# --- Letter Attributes ---
default_letter_size = 40    # Default font size for swarming letters.
ENLARGED_LETTER_SIZE = int(default_letter_size * ENLARGED_LETTER_SIZE_FACTOR) # Calculated enlarged size.
default_letter_speed = 2    # Base maximum speed for swarming letters.
num_letters = 26            # Number of unique alphabet letters (A-Z).
letters = list(string.ascii_uppercase) # List of 'A' through 'Z'.

# ------------- Initial Game State Setup -------------
# --- Word Game State ---
target_word = random.choice(simple_words) # The word to be spelled.
# Represents the target word display, e.g., ['C', '_', 'T']
displayed_word_chars = ['_'] * len(target_word)
# Index of the next letter to be spelled in target_word.
current_letter_index = 0

# --- Preview State Variables ---
# The character (e.g., 'A') currently selected for preview.
previewed_letter_char = None
# List of indices of letter instances that are currently in STATE_PREVIEW.
active_preview_letter_indices = []

# --- Letter Data Lists ---
# These lists store properties for each of the 26 letters (A-Z) that swarm on screen.
letter_positions = []  # Stores (x, y) coordinates.
letter_velocities = [] # Stores current (vx, vy) velocities.
original_letter_velocities = [] # Stores original (vx,vy) to restore after preview/animation.
letter_colors = []     # Stores the base color of each letter (usually randomized).
letter_states = []     # Stores the current state (e.g., STATE_NORMAL) of each letter.
letter_preview_timers = [] # Stores timestamp for when a previewed letter should revert to normal.
# Stores the target slot (0, 1, 2,...) in target_word for a letter in STATE_ANIMATING_TO_SLOT.
letter_target_slot_indices = []
# Stores timestamp for flashing feedback color (e.g., RED for incorrect confirmation).
letter_feedback_flash_timers = []

# Initialize attributes for each of the 26 alphabet letters
for i in range(num_letters):
    x = random.randint(0, window_width - default_letter_size)
    y = random.randint(0, window_height - default_letter_size)
    angle = random.uniform(0, 2 * math.pi)
    speed = random.randint(1, default_letter_speed)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed

    letter_positions.append((x, y))
    letter_velocities.append((vx, vy))
    original_letter_velocities.append((vx, vy))
    letter_colors.append((random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))) # Less bright random colors
    letter_states.append(STATE_NORMAL)
    letter_preview_timers.append(0)
    letter_target_slot_indices.append(-1)
    letter_feedback_flash_timers.append(0)

# Pygame clock for controlling frame rate
clock = pygame.time.Clock()

# Helper function to get the screen position of a letter slot in the target word display
def get_slot_position(slot_index):
    if not target_word or slot_index < 0 or slot_index >= len(target_word):
        # Return a default off-screen position or handle error appropriately
        return (-100, -100)

    # Font used for displaying the target word (underscores and placed letters)
    font_target_word_calc = pygame.font.Font(None, 50)

    # Create the string as it's displayed (with spaces) to measure correctly
    current_display_string_list = []
    for i_char, char_in_word in enumerate(displayed_word_chars):
        current_display_string_list.append(char_in_word)
        if i_char < len(displayed_word_chars) -1: # Add space if not the last character
             current_display_string_list.append(' ')

    # Calculate total width of the currently displayed target word string (e.g., "C A _")
    # This ensures alignment even with variable-width characters and spaces.
    full_display_text = "".join(current_display_string_list)
    total_word_width = font_target_word_calc.size(full_display_text)[0]

    target_word_display_center_x = window_width // 2
    target_word_start_x = target_word_display_center_x - (total_word_width // 2)

    # Calculate the center x of the specific slot based on characters *before* it in the display string
    # Each character in displayed_word_chars is followed by a space, except the last one.
    slot_center_x = target_word_start_x
    for i in range(slot_index):
        # Add width of the character at index 'i' and the following space
        char_width = font_target_word_calc.size(displayed_word_chars[i] + " ")[0]
        slot_center_x += char_width

    # Add half the width of the character at slot_index itself (without the space)
    slot_center_x += font_target_word_calc.size(displayed_word_chars[slot_index])[0] // 2

    slot_y_pos = 30 # Y position of the target word display (center of the text)
    return (slot_center_x, slot_y_pos)

# --- Game State Timers ---
show_feedback_message_until = 0 # Timestamp for displaying "Well Done!" message.
pending_new_word_setup_time = 0 # Timestamp for when to set up the next word after completion.

# ------------- Main Game Loop -------------
running = True
while running:
    current_time = pygame.time.get_ticks()

    # --- Delayed New Word Setup ---
    # If a new word setup is pending and the time has come.
    if pending_new_word_setup_time > 0 and current_time >= pending_new_word_setup_time:
        target_word = random.choice(simple_words)
        current_letter_index = 0
        displayed_word_chars = ['_'] * len(target_word) # Reset with underscores

        # Reset all letter properties for a fresh start
        for i in range(num_letters):
            letter_states[i] = STATE_NORMAL
            # Re-scatter letters randomly
            letter_positions[i] = (random.randint(0, window_width - default_letter_size),
                                   random.randint(0, window_height - default_letter_size))

            # Assign new random velocities and update original velocities
            angle = random.uniform(0, 2 * math.pi)
            speed = random.randint(1, default_letter_speed)
            vx_new = math.cos(angle) * speed
            vy_new = math.sin(angle) * speed
            letter_velocities[i] = (vx_new, vy_new)
            original_letter_velocities[i] = (vx_new, vy_new)

            # Assign new random (less bright) base colors
            letter_colors[i] = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            letter_preview_timers[i] = 0 # Reset preview timer
            letter_target_slot_indices[i] = -1 # Clear animation target
            letter_feedback_flash_timers[i] = 0 # Clear feedback flash timer

        previewed_letter_char = None # Clear any active preview
        active_preview_letter_indices = []
        pending_new_word_setup_time = 0 # Mark setup as complete

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Process key press only if no new word setup is pending (i.e., game is active)
            if pending_new_word_setup_time == 0 and event.unicode.isalpha():
                pressed_char = event.unicode.upper()
                is_confirmation_press = False

                # --- Confirmation Logic ---
                # Check if the pressed key matches the currently previewed character.
                if previewed_letter_char is not None and pressed_char == previewed_letter_char:
                    is_confirmation_press = True
                    confirmed_indices = list(active_preview_letter_indices) # Make a copy

                    # Revert all letters that were part of this preview to normal state.
                    for idx in confirmed_indices:
                        if idx < len(letter_states):
                            letter_states[idx] = STATE_NORMAL
                            letter_velocities[idx] = original_letter_velocities[idx]
                            letter_preview_timers[idx] = 0 # Clear preview timer

                    active_preview_letter_indices = [] # Clear the list of active previewed letters
                    previewed_letter_char = None       # No letter is being previewed now

                    # --- Check Confirmed Letter Against Target Word ---
                    if target_word and current_letter_index < len(target_word):
                        expected_letter = target_word[current_letter_index]
                        if pressed_char == expected_letter: # Correct letter confirmed
                            if correct_sound:
                                correct_sound.play()

                            # Choose one instance of the confirmed letter to animate to the slot.
                            if confirmed_indices:
                                animating_letter_index = -1
                                for con_idx in confirmed_indices:
                                    # Ensure the chosen letter is actually in a normal state (should be).
                                    if letter_states[con_idx] == STATE_NORMAL:
                                        animating_letter_index = con_idx
                                        break

                                target_slot_for_animation = current_letter_index

                                if animating_letter_index != -1:
                                     letter_states[animating_letter_index] = STATE_ANIMATING_TO_SLOT
                                     letter_target_slot_indices[animating_letter_index] = target_slot_for_animation
                                     letter_colors[animating_letter_index] = GREEN # Make it green for animation

                            current_letter_index += 1 # Advance to the next letter in the target word

                            # --- Word Completion Check ---
                            if current_letter_index == len(target_word): # Word is complete
                                if word_complete_sound:
                                    word_complete_sound.play()
                                show_feedback_message_until = current_time + 2000 # Show "Well Done!"
                                pending_new_word_setup_time = current_time + 2000 # Schedule new word setup
                        else: # Incorrect letter confirmed (e.g., 'A' confirmed, but 'C' was expected)
                            if incorrect_sound:
                                incorrect_sound.play()
                            # Flash the letters (that were just confirmed and reverted) RED.
                            for idx_flash in confirmed_indices:
                                if idx_flash < len(letter_feedback_flash_timers):
                                    letter_feedback_flash_timers[idx_flash] = current_time + 500
                    else: # Word already spelled, or no target word (should not happen if pending_new_word_setup_time is handled)
                        if incorrect_sound:
                            incorrect_sound.play()
                        for idx_flash in confirmed_indices: # Flash if confirmed outside of active spelling
                            if idx_flash < len(letter_feedback_flash_timers):
                                letter_feedback_flash_timers[idx_flash] = current_time + 500

                # --- New Preview Logic ---
                # If it wasn't a confirmation press, it's a new preview attempt.
                if not is_confirmation_press:
                    # Clear any previously active preview (if 'A' was previewed, then 'B' is pressed).
                    if previewed_letter_char:
                        for idx_old_preview in active_preview_letter_indices:
                            if idx_old_preview < len(letter_states):
                                letter_states[idx_old_preview] = STATE_NORMAL
                                letter_velocities[idx_old_preview] = original_letter_velocities[idx_old_preview]
                                letter_preview_timers[idx_old_preview] = 0

                    active_preview_letter_indices = [] # Reset for the new preview
                    previewed_letter_char = pressed_char # Set the new character to be previewed

                    # Find all instances of the pressed character and set them to STATE_PREVIEW.
                    for i in range(num_letters):
                        if letters[i] == pressed_char:
                            letter_states[i] = STATE_PREVIEW

                            # Adjust position if enlarged letter goes off-screen
                            x_pos, y_pos = letter_positions[i]
                            if x_pos < 0: x_pos = 0
                            if y_pos < 0: y_pos = 0
                            if x_pos + ENLARGED_LETTER_SIZE > window_width:
                                x_pos = window_width - ENLARGED_LETTER_SIZE
                            if y_pos + ENLARGED_LETTER_SIZE > window_height:
                                y_pos = window_height - ENLARGED_LETTER_SIZE
                            letter_positions[i] = (x_pos, y_pos)

                            # Slow down for preview
                            letter_velocities[i] = (original_letter_velocities[i][0] * PREVIEW_SPEED_FACTOR,
                                                    original_letter_velocities[i][1] * PREVIEW_SPEED_FACTOR)
                            letter_preview_timers[i] = current_time + PREVIEW_DURATION_MS # Set timeout
                            active_preview_letter_indices.append(i)
            # else: Key pressed was not an alphabet character (e.g. Enter, Shift) - do nothing for now.

    # --- Timeout Logic for Previewed Letters ---
    # If a letter is being previewed and its timer expires, revert it to normal.
    if previewed_letter_char is not None and active_preview_letter_indices:
        still_in_preview_indices = [] # Temp list to track letters that remain in preview
        for i in list(active_preview_letter_indices): # Iterate over a copy as list might change
            if i < len(letter_states) and letter_states[i] == STATE_PREVIEW:
                if current_time > letter_preview_timers[i] and letter_preview_timers[i] != 0: # Check timer
                    letter_states[i] = STATE_NORMAL
                    letter_velocities[i] = original_letter_velocities[i] # Restore speed
                    letter_preview_timers[i] = 0
                else:
                    still_in_preview_indices.append(i) # Letter is still in preview

        active_preview_letter_indices = still_in_preview_indices # Update active list
        if not active_preview_letter_indices: # If all previewed letters timed out
            previewed_letter_char = None

    # --- Drawing / Rendering ---
    window.fill(BLACK) # Clear screen

    # --- Update and Draw Each Swarming Letter ---
    # These are drawn first, so UI elements like target word and messages can be on top.
    for i in range(num_letters):
        x, y = letter_positions[i]
        vx, vy = letter_velocities[i]
        state = letter_states[i]

        # Determine current size for drawing and collision based on state
        current_letter_draw_size = default_letter_size
        if state == STATE_PREVIEW:
            current_letter_draw_size = ENLARGED_LETTER_SIZE
        # STATE_ANIMATING_TO_SLOT and STATE_PLACED use default_letter_size for drawing

        # --- Letter Movement Logic ---
        if state == STATE_ANIMATING_TO_SLOT:
            slot_idx = letter_target_slot_indices[i]
            if slot_idx != -1: # Ensure a valid target slot is assigned
                target_pos = get_slot_position(slot_idx)

                dx = target_pos[0] - x # Difference in x
                dy = target_pos[1] - y # Difference in y
                dist = math.sqrt(dx*dx + dy*dy) # Distance to target

                if dist < ANIMATION_SPEED: # If close enough, snap to target
                    x, y = target_pos
                    vx, vy = 0, 0 # Stop movement
                    letter_states[i] = STATE_PLACED # Change state
                    letter_velocities[i] = (vx,vy)
                    # Update the displayed word with the character of the placed letter
                    if 0 <= slot_idx < len(displayed_word_chars):
                         displayed_word_chars[slot_idx] = letters[i]
                else: # Move towards target
                    vx = (dx / dist) * ANIMATION_SPEED
                    vy = (dy / dist) * ANIMATION_SPEED
                    x += vx
                    y += vy
            else: # Should not happen: animating without a target slot
                letter_states[i] = STATE_NORMAL # Revert to normal as a fallback

        elif state == STATE_NORMAL or state == STATE_PREVIEW:
            # Standard swarming movement
            x += vx
            y += vy

            # Bounce off window boundaries using the letter's current draw size
            if x < 0 or x > window_width - current_letter_draw_size:
                vx = -vx
            if y < 0 or y > window_height - current_letter_draw_size:
                vy = -vy
            letter_velocities[i] = (vx, vy) # Update velocity if bounced

        elif state == STATE_PLACED:
            # Letter is fixed in its slot, no movement needed. Velocity should be (0,0).
            pass

        letter_positions[i] = (x,y) # Store updated position

        # --- Letter Drawing ---
        # Letters in STATE_PLACED are not drawn here; they are part of the target_word display.
        if state != STATE_PLACED:
            # Determine display color based on state and feedback timers
            current_display_color = letter_colors[i] # Default to its base random color

            if state == STATE_ANIMATING_TO_SLOT:
                current_display_color = GREEN # Animating letters are GREEN
            elif letter_feedback_flash_timers[i] > current_time: # Check for active feedback flash
                current_display_color = RED # Flashing RED due to incorrect feedback
            # STATE_PREVIEW letters use their base random color (letter_colors[i])

            font = pygame.font.Font(None, current_letter_draw_size)
            letter_surface = font.render(letters[i], True, current_display_color)
            window.blit(letter_surface, (x, y))

    # --- Draw UI Elements (Target Word, Feedback Messages) On Top ---
    # Display the target word (e.g., "C A _")
    font_target_word = pygame.font.Font(None, 50)
    display_text = " ".join(displayed_word_chars) # Join with spaces for readability
    text_target_word_surface = font_target_word.render(display_text, True, WHITE)
    text_rect_target_word = text_target_word_surface.get_rect(center=(window_width // 2, 30))
    window.blit(text_target_word_surface, text_rect_target_word)

    # Display "Well Done!" feedback message if active
    if current_time < show_feedback_message_until:
        font_feedback = pygame.font.Font(None, 60)
        text_feedback = font_feedback.render("Well Done!", True, GREEN)
        text_rect_feedback = text_feedback.get_rect(center=(window_width // 2, window_height // 2))
        window.blit(text_feedback, text_rect_feedback)

    pygame.display.update() # Update the full display
    clock.tick(120) # Cap the frame rate

# ------------- Game Exit -------------
pygame.quit()
