# AlphabetSwarm.py
# A game where letters swarm around, and the player tries to spell a target word
# by typing the letters in the correct order using a two-step preview/confirm mechanism.

# ------------- Imports -------------
import pygame
import random
import string
import math
import sys

# ------------- Pygame and Mixer Initialization -------------
pygame.init()
pygame.mixer.init()

# ------------- Sound Setup -------------
correct_sound_path = "correct.wav"
incorrect_sound_path = "incorrect.wav"
word_complete_sound_path = "word_complete.wav"
try:
    correct_sound = pygame.mixer.Sound(correct_sound_path)
except pygame.error:
    correct_sound = None; print(f"Warning: Sound file {correct_sound_path} not found.")
try:
    incorrect_sound = pygame.mixer.Sound(incorrect_sound_path)
except pygame.error:
    incorrect_sound = None; print(f"Warning: Sound file {incorrect_sound_path} not found.")
try:
    word_complete_sound = pygame.mixer.Sound(word_complete_sound_path)
except pygame.error:
    word_complete_sound = None; print(f"Warning: Sound file {word_complete_sound_path} not found.")

# ------------- Game Configuration / Variables -------------
WORD_LIST_FILENAME = "words.txt"
DEFAULT_SIMPLE_WORDS = [
    {'word': "CAT", 'clue': "A furry animal that meows"},
    {'word': "DOG", 'clue': "Barks and wags its tail"},
    {'word': "SUN", 'clue': "Shines during the day"},
    {'word': "TREE", 'clue': "Has leaves and a trunk"},
    {'word': "BOOK", 'clue': "Something you read"},
    {'word': "FISH", 'clue': "Swims in water"},
    {'word': "BALL", 'clue': "Round toy for playing"},
    {'word': "STAR", 'clue': "Twinkles in the night sky"}
]

def load_words_from_file(filename):
    valid_words = []
    try:
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                parts = line.split(',', 1)
                if len(parts) == 2:
                    word_candidate = parts[0].strip().upper()
                    clue_candidate = parts[1].strip()
                    if word_candidate and clue_candidate and 3 <= len(word_candidate) <= 5 and word_candidate.isalpha():
                        valid_words.append({'word': word_candidate, 'clue': clue_candidate})
        if valid_words:
            print(f"Info: Successfully loaded {len(valid_words)} word-clue pairs from '{filename}'.")
        else:
            print(f"Info: No valid word-clue pairs found in '{filename}'.")
    except FileNotFoundError:
        print(f"Info: Word file '{filename}' not found.")
    return valid_words

simple_words = load_words_from_file(WORD_LIST_FILENAME)
if not simple_words:
    simple_words = DEFAULT_SIMPLE_WORDS
    print(f"Info: Using default word list of {len(simple_words)} word-clue pairs.")
if not simple_words:
    print("CRITICAL ERROR: No words available. Exiting."); pygame.quit(); sys.exit()

# --- Game Window ---
window_width = 1000
window_height = 700
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Alphabet Swarm")

# --- Colors ---
BLACK = (0, 0, 0); WHITE = (255, 255, 255); GREEN = (0, 255, 0); RED = (255, 0, 0); YELLOW = (255, 255, 0)

# --- Game States ---
STATE_MAIN_MENU = "main_menu"; STATE_PLAYER_NAME_INPUT = "player_name_input"
STATE_GAME_PLAY = "game_play"; STATE_SHOW_TURN_TRANSITION = "show_turn_transition"
STATE_VERSUS_GAME_OVER = "versus_game_over"; STATE_LEADERBOARD_DISPLAY = "leaderboard_display"
ACTION_QUIT = "ACTION_QUIT"
current_game_state = STATE_MAIN_MENU

# --- Letter States ---
STATE_NORMAL = "normal"; STATE_PREVIEW = "preview"
STATE_ANIMATING_TO_SLOT = "animating_to_slot"; STATE_PLACED = "placed"

# --- Constants ---
ANIMATION_SPEED = 10; PREVIEW_DURATION_MS = 3000; PREVIEW_SPEED_FACTOR = 0.5
ENLARGED_LETTER_SIZE_FACTOR = 5.0; HINTS_PER_WORD = 3; HINT_TIMER_DURATION_MS = 30000
SCORE_DISPLAY_DURATION_MS = 2000; MAX_NAME_LENGTH = 8; CURSOR_BLINK_RATE_MS = 500

# --- Game Mode & Player State ---
GAME_MODE_1P = "1P"; GAME_MODE_2P_VERSUS = "2P_Versus"; current_game_mode = GAME_MODE_1P
current_player_turn = 1; player_names = ["Player 1", "Player 2"]; player_scores = [0, 0]
input_active_player = 0; player_name_inputs = ["", ""]
cursor_visible = True; cursor_timer = 0
player_failed_last_word = [False, False]

# --- Letter Attributes & Data Lists ---
default_letter_size = 40
ENLARGED_LETTER_SIZE = int(default_letter_size * ENLARGED_LETTER_SIZE_FACTOR)
default_letter_speed = 2; num_letters = 26; letters = list(string.ascii_uppercase)
letter_positions, letter_velocities, original_letter_velocities = [], [], []
letter_colors, letter_states, letter_preview_timers = [], [], []
letter_target_slot_indices, letter_feedback_flash_timers = [], []

# --- Word Game Variables ---
target_word = ""; current_clue_text = ""; displayed_word_chars = []
current_letter_index = 0; word_start_time = 0

# --- Hint State Variables ---
hints_used_this_word = 0; hint_timer_start_time = 0
is_hint_timer_active = False; show_clue_on_screen = True

# --- Preview State Variables ---
previewed_letter_char = None; active_preview_letter_indices = []

# --- Timers & Message Variables ---
show_feedback_message_until = 0; pending_new_word_setup_time = 0
last_word_score = 0; show_last_word_score_until = 0

# --- Pygame Clock & UI Font ---
clock = pygame.time.Clock()
ui_font = pygame.font.Font(None, 40)
menu_item_font = pygame.font.Font(None, 50)
title_font = pygame.font.Font(None, 74)
feedback_font = pygame.font.Font(None, 60)

# --- Button Configurations ---
main_menu_buttons = {
    "1P_Game": {"text": "1 Player Game", "rect": None, "action_state": STATE_PLAYER_NAME_INPUT, "mode": GAME_MODE_1P, "hovered": False},
    "2P_Game": {"text": "2 Player Versus", "rect": None, "action_state": STATE_PLAYER_NAME_INPUT, "mode": GAME_MODE_2P_VERSUS, "hovered": False},
    "Leaderboard": {"text": "Leaderboard", "rect": None, "action_state": STATE_LEADERBOARD_DISPLAY, "mode": None, "hovered": False},
    "Quit": {"text": "Quit", "rect": None, "action_state": ACTION_QUIT, "mode": None, "hovered": False}
}
turn_transition_button_rect = None
turn_transition_button_hovered = False
versus_game_over_buttons = {
    "MainMenu": {"text": "Main Menu", "rect": None, "action_state": STATE_MAIN_MENU, "hovered": False},
    "Leaderboard": {"text": "Leaderboard", "rect": None, "action_state": STATE_LEADERBOARD_DISPLAY, "hovered": False}
}


# ------------- Helper Functions -------------
def get_word_base_score(word_str):
    length = len(word_str);
    if length == 3: return 30
    elif length == 4: return 40
    elif length == 5: return 50
    else: return 0
def calculate_speed_multiplier(time_taken_ms, word_length):
    if word_length == 0: return 1.0; time_for_max_bonus_per_letter_ms = 3000; time_for_min_bonus_per_letter_ms = 8000
    max_bonus_target_time_ms = word_length * time_for_max_bonus_per_letter_ms
    min_bonus_target_time_ms = word_length * time_for_min_bonus_per_letter_ms; bonus_multiplier_factor = 0.0
    if time_taken_ms < max_bonus_target_time_ms: bonus_multiplier_factor = 1.0
    elif time_taken_ms < min_bonus_target_time_ms:
        range_ms = min_bonus_target_time_ms - max_bonus_target_time_ms
        if range_ms > 0: bonus_multiplier_factor = (min_bonus_target_time_ms - time_taken_ms) / range_ms
    final_multiplier = 1.0 + bonus_multiplier_factor; return max(1.0, min(final_multiplier, 2.0))
def get_slot_position(slot_index):
    global target_word, displayed_word_chars, window_width
    if not target_word or slot_index < 0 or slot_index >= len(target_word): return (-100, -100)
    font_target_word_calc = pygame.font.Font(None, 50); current_display_string_list = []
    for i_char in range(len(target_word)):
        char_to_measure = displayed_word_chars[i_char] if i_char < len(displayed_word_chars) else '_'
        current_display_string_list.append(char_to_measure)
        if i_char < len(target_word) - 1: current_display_string_list.append(' ')
    full_display_text = "".join(current_display_string_list); total_word_width = font_target_word_calc.size(full_display_text)[0]
    target_word_display_center_x = window_width // 2; target_word_start_x = target_word_display_center_x - (total_word_width // 2)
    slot_center_x = target_word_start_x
    for i in range(slot_index):
        char_to_measure_i = displayed_word_chars[i] if i < len(displayed_word_chars) else '_'
        char_width = font_target_word_calc.size(char_to_measure_i + " ")[0]; slot_center_x += char_width
    char_at_slot_index = displayed_word_chars[slot_index] if slot_index < len(displayed_word_chars) else '_'
    slot_center_x += font_target_word_calc.size(char_at_slot_index)[0] // 2; slot_y_pos = 30
    return (slot_center_x, slot_y_pos)

# ------------- Game Setup and Reset Functions -------------
def setup_new_word_for_active_player(current_time_ticks):
    global target_word, current_clue_text, displayed_word_chars, current_letter_index
    global word_start_time, hints_used_this_word, hint_timer_start_time, is_hint_timer_active
    global show_clue_on_screen, previewed_letter_char, active_preview_letter_indices
    global letter_states, letter_positions, letter_velocities, original_letter_velocities
    global letter_colors, letter_preview_timers, letter_target_slot_indices, letter_feedback_flash_timers
    global player_failed_last_word, current_player_turn

    selected_word_obj = random.choice(simple_words)
    target_word = selected_word_obj['word']
    current_clue_text = selected_word_obj['clue']
    displayed_word_chars = ['_'] * len(target_word)
    current_letter_index = 0

    word_start_time = current_time_ticks
    hints_used_this_word = 0
    hint_timer_start_time = current_time_ticks
    is_hint_timer_active = True
    show_clue_on_screen = True
    previewed_letter_char = None
    active_preview_letter_indices = []

    player_idx = current_player_turn - 1
    if 0 <= player_idx < len(player_failed_last_word):
        player_failed_last_word[player_idx] = False

    for i in range(num_letters):
        letter_states[i] = STATE_NORMAL
        letter_positions[i] = (random.randint(0, window_width - default_letter_size),
                               random.randint(0, window_height - default_letter_size))
        angle = random.uniform(0, 2 * math.pi)
        speed = random.randint(1, default_letter_speed)
        vx_new = math.cos(angle) * speed
        vy_new = math.sin(angle) * speed
        letter_velocities[i] = (vx_new, vy_new)
        original_letter_velocities[i] = (vx_new, vy_new)
        letter_colors[i] = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        letter_preview_timers[i] = 0
        letter_target_slot_indices[i] = -1
        letter_feedback_flash_timers[i] = 0

    print(f"Player {current_player_turn}'s turn. New word: {target_word}")

def setup_new_game_session():
    global current_player_turn, player_scores, player_name_inputs, input_active_player
    global pending_new_word_setup_time, last_word_score, show_last_word_score_until
    global player_failed_last_word, current_game_state # Added current_game_state

    if current_game_state == STATE_PLAYER_NAME_INPUT:
         player_scores = [0,0]
         current_player_turn = 1

    player_name_inputs = ["", ""]
    input_active_player = 0
    player_failed_last_word = [False, False]

    pending_new_word_setup_time = 0
    last_word_score = 0
    show_last_word_score_until = 0
    show_feedback_message_until = 0

    # This will be called AFTER player names are input, or when transitioning to a new turn
    # if not in 2P mode where STATE_SHOW_TURN_TRANSITION is used.
    # For the very first game start, setup_new_word_for_active_player is called
    # after player name input (when transitioning to STATE_GAME_PLAY).
    # If it's a restart from game over, this also applies.
    # If it's a new word in 1P mode, that's handled by update_game_play_logic calling setup_new_word_for_active_player.

# ------------- Game State Specific Functions -------------
def handle_events_main_menu(event):
    global current_game_state, running, current_game_mode
    if event.type == pygame.QUIT: running = False
    elif event.type == pygame.MOUSEMOTION:
        mouse_pos = pygame.mouse.get_pos()
        for key in main_menu_buttons:
            button = main_menu_buttons[key]
            if button["rect"] and button["rect"].collidepoint(mouse_pos): button["hovered"] = True
            else: button["hovered"] = False
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for key in main_menu_buttons:
                button = main_menu_buttons[key]
                if button["rect"] and button["rect"].collidepoint(mouse_pos):
                    action = button["action_state"]; mode = button["mode"]
                    if mode: current_game_mode = mode
                    if action == ACTION_QUIT: running = False
                    else:
                        current_game_state = action
                        if action == STATE_PLAYER_NAME_INPUT:
                            setup_new_game_session()
                    break
def draw_main_menu(window_surface):
    title_surf = title_font.render("Alphabet Swarm", True, GREEN)
    title_rect = title_surf.get_rect(center=(window_width // 2, window_height // 4))
    window_surface.blit(title_surf, title_rect)
    button_start_y = title_rect.bottom + 70; button_spacing = 60
    for index, key in enumerate(main_menu_buttons):
        button_info = main_menu_buttons[key]
        text_color = YELLOW if button_info['hovered'] else WHITE
        text_surf = menu_item_font.render(button_info['text'], True, text_color)
        y_position = button_start_y + index * button_spacing
        button_rect = text_surf.get_rect(center=(window_width // 2, y_position))
        main_menu_buttons[key]['rect'] = button_rect
        window_surface.blit(text_surf, button_rect)

def handle_events_player_name_input(event):
    global current_game_state, running, player_names, player_name_inputs, input_active_player, current_game_mode
    if event.type == pygame.QUIT: running = False
    elif event.type == pygame.KEYDOWN:
        active_input_list_index = input_active_player
        if event.key == pygame.K_BACKSPACE:
            player_name_inputs[active_input_list_index] = player_name_inputs[active_input_list_index][:-1]
        elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            current_name = player_name_inputs[active_input_list_index].strip()
            player_names[active_input_list_index] = current_name if current_name else f"Player {active_input_list_index + 1}"
            if current_game_mode == GAME_MODE_1P or active_input_list_index == 1:
                if current_game_mode == GAME_MODE_1P and player_names[1] != "Player 2":
                    player_names[1] = "Player 2"
                # Now that names are set, fully setup the first word for player 1
                setup_new_word_for_active_player(pygame.time.get_ticks())
                current_game_state = STATE_GAME_PLAY
                print(f"Names finalized: P1: {player_names[0]}, P2: {player_names[1]}. Starting game.")
            else:
                input_active_player = 1
        elif len(player_name_inputs[active_input_list_index]) < MAX_NAME_LENGTH:
            if event.unicode.isalnum() or event.unicode == ' ':
                player_name_inputs[active_input_list_index] += event.unicode
def draw_player_name_input(window_surface):
    global cursor_visible
    y_offset = window_height // 2 - 60
    prompt_p1_text = f"{player_names[0] if player_names[0] != 'Player 1' else 'Player 1'} Name:"
    if input_active_player == 0 and player_name_inputs[0] == "" and player_names[0] == "Player 1":
        prompt_p1_text = "Player 1 Name:"
    elif input_active_player == 0 :
         prompt_p1_text = f"Player 1 Name: {player_name_inputs[0]}"
    else:
         prompt_p1_text = f"{player_names[0]} Name: {player_names[0]}"
    p1_prompt_surf = ui_font.render(prompt_p1_text, True, WHITE)
    p1_prompt_rect = p1_prompt_surf.get_rect(center=(window_width // 2, y_offset))
    window_surface.blit(p1_prompt_surf, p1_prompt_rect)
    input_text_p1 = player_name_inputs[0]
    if input_active_player == 0 and cursor_visible: input_text_p1 += "|"
    p1_input_surf = ui_font.render(input_text_p1, True, YELLOW if input_active_player == 0 else WHITE)
    p1_input_rect = p1_input_surf.get_rect(center=(window_width // 2, y_offset + 40))
    window_surface.blit(p1_input_surf, p1_input_rect)
    if current_game_mode == GAME_MODE_2P_VERSUS:
        y_offset += 100
        prompt_p2_text = f"{player_names[1] if player_names[1] != 'Player 2' else 'Player 2'} Name:"
        if input_active_player == 1 and player_name_inputs[1] == "" and player_names[1] == "Player 2":
             prompt_p2_text = "Player 2 Name:"
        elif input_active_player == 1:
             prompt_p2_text = f"Player 2 Name: {player_name_inputs[1]}"
        else:
             prompt_p2_text = f"{player_names[1]} Name: {player_names[1]}"
        p2_prompt_surf = ui_font.render(prompt_p2_text, True, WHITE)
        p2_prompt_rect = p2_prompt_surf.get_rect(center=(window_width // 2, y_offset))
        window_surface.blit(p2_prompt_surf, p2_prompt_rect)
        input_text_p2 = player_name_inputs[1]
        if input_active_player == 1 and cursor_visible: input_text_p2 += "|"
        p2_input_surf = ui_font.render(input_text_p2, True, YELLOW if input_active_player == 1 else WHITE)
        p2_input_rect = p2_input_surf.get_rect(center=(window_width // 2, y_offset + 40))
        window_surface.blit(p2_input_surf, p2_input_rect)
    instruction_text = "Type name(s). Press Enter to confirm each name. Max 8 chars."
    if input_active_player == 0 and current_game_mode == GAME_MODE_1P:
        instruction_text = "Type name and Press Enter to Start. Max 8 chars."
    elif input_active_player == 1 and current_game_mode == GAME_MODE_2P_VERSUS:
        instruction_text = "Type Player 2 name and Press Enter to Start. Max 8 chars."
    instr_surf = ui_font.render(instruction_text, True, WHITE)
    instr_rect = instr_surf.get_rect(center=(window_width // 2, window_height - 50))
    window_surface.blit(instr_surf, instr_rect)
def update_player_name_input_logic(current_time_ticks):
    global cursor_timer, cursor_visible
    if current_time_ticks - cursor_timer > CURSOR_BLINK_RATE_MS:
        cursor_timer = current_time_ticks; cursor_visible = not cursor_visible

def handle_events_game_play(event, current_time_ticks):
    global running, show_clue_on_screen, current_game_state
    global previewed_letter_char, active_preview_letter_indices, letter_states, letter_velocities
    global original_letter_velocities, letter_preview_timers, current_letter_index, player_scores, player_failed_last_word
    global last_word_score, show_last_word_score_until, hints_used_this_word, hint_timer_start_time
    global is_hint_timer_active, word_start_time, pending_new_word_setup_time, displayed_word_chars
    global target_word, current_clue_text, letter_target_slot_indices, letter_colors
    global letter_feedback_flash_timers, current_player_turn
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE: current_game_state = STATE_MAIN_MENU; return
        if event.key == pygame.K_c: show_clue_on_screen = not show_clue_on_screen
        elif pending_new_word_setup_time == 0 and event.unicode.isalpha():
            pressed_char = event.unicode.upper(); is_confirmation_press = False
            if previewed_letter_char is not None and pressed_char == previewed_letter_char:
                is_confirmation_press = True; confirmed_indices = list(active_preview_letter_indices)
                for idx in confirmed_indices:
                    if idx < len(letter_states): letter_states[idx] = STATE_NORMAL; letter_velocities[idx] = original_letter_velocities[idx]; letter_preview_timers[idx] = 0
                active_preview_letter_indices = []; previewed_letter_char = None
                if target_word and current_letter_index < len(target_word):
                    expected_letter = target_word[current_letter_index]
                    if pressed_char == expected_letter:
                        if correct_sound: correct_sound.play()
                        if confirmed_indices:
                            animating_letter_index = -1
                            for con_idx in confirmed_indices:
                                if letter_states[con_idx] == STATE_NORMAL: animating_letter_index = con_idx; break
                            target_slot_for_animation = current_letter_index
                            if animating_letter_index != -1:
                                 letter_states[animating_letter_index] = STATE_ANIMATING_TO_SLOT
                                 letter_target_slot_indices[animating_letter_index] = target_slot_for_animation
                                 letter_colors[animating_letter_index] = GREEN
                        current_letter_index += 1
                        if current_letter_index < len(target_word): hint_timer_start_time = current_time_ticks; is_hint_timer_active = True
                        else: is_hint_timer_active = False
                        if current_letter_index == len(target_word):
                            player_idx = current_player_turn - 1
                            if 0 <= player_idx < len(player_failed_last_word): player_failed_last_word[player_idx] = False
                            time_taken_ms = current_time_ticks - word_start_time; base_score = get_word_base_score(target_word)
                            speed_mult = calculate_speed_multiplier(time_taken_ms, len(target_word)); score_for_this_word = int(base_score * speed_mult)
                            if 0 <= player_idx < len(player_scores):
                                player_scores[player_idx] += score_for_this_word
                                print(f"Player {current_player_turn} scored {score_for_this_word} for '{target_word}'. Total: {player_scores[player_idx]}")
                            last_word_score = score_for_this_word; show_last_word_score_until = current_time_ticks + SCORE_DISPLAY_DURATION_MS
                            if word_complete_sound: word_complete_sound.play()
                            show_feedback_message_until = current_time_ticks + 2000 ; pending_new_word_setup_time = current_time_ticks + 2000
                    else:
                        if incorrect_sound: incorrect_sound.play()
                        for idx_flash in confirmed_indices:
                            if idx_flash < len(letter_feedback_flash_timers): letter_feedback_flash_timers[idx_flash] = current_time_ticks + 500
                else:
                    if is_confirmation_press:
                        if incorrect_sound: incorrect_sound.play()
                        for idx_flash in confirmed_indices:
                            if idx_flash < len(letter_feedback_flash_timers): letter_feedback_flash_timers[idx_flash] = current_time_ticks + 500
            if not is_confirmation_press:
                if previewed_letter_char:
                    for idx_old_preview in active_preview_letter_indices:
                        if idx_old_preview < len(letter_states):
                            letter_states[idx_old_preview] = STATE_NORMAL; letter_velocities[idx_old_preview] = original_letter_velocities[idx_old_preview]; letter_preview_timers[idx_old_preview] = 0
                active_preview_letter_indices = []; previewed_letter_char = pressed_char
                for i in range(num_letters):
                    if letters[i] == pressed_char:
                        letter_states[i] = STATE_PREVIEW; x_pos, y_pos = letter_positions[i]
                        if x_pos < 0: x_pos = 0
                        if y_pos < 0: y_pos = 0
                        if x_pos + ENLARGED_LETTER_SIZE > window_width: x_pos = window_width - ENLARGED_LETTER_SIZE
                        if y_pos + ENLARGED_LETTER_SIZE > window_height: y_pos = window_height - ENLARGED_LETTER_SIZE
                        letter_positions[i] = (x_pos, y_pos)
                        letter_velocities[i] = (original_letter_velocities[i][0] * PREVIEW_SPEED_FACTOR, original_letter_velocities[i][1] * PREVIEW_SPEED_FACTOR)
                        letter_preview_timers[i] = current_time_ticks + PREVIEW_DURATION_MS ; active_preview_letter_indices.append(i)

def update_game_play_logic(current_time_ticks):
    global target_word, current_clue_text, displayed_word_chars, current_letter_index, word_start_time
    global hints_used_this_word, hint_timer_start_time, is_hint_timer_active, show_clue_on_screen
    global previewed_letter_char, active_preview_letter_indices, letter_states, letter_positions
    global letter_velocities, original_letter_velocities, letter_colors, letter_preview_timers
    global letter_target_slot_indices, letter_feedback_flash_timers, pending_new_word_setup_time
    global last_word_score, show_last_word_score_until, current_player_turn, player_scores, player_failed_last_word
    global current_game_mode, simple_words, letters, num_letters, current_game_state, STATE_SHOW_TURN_TRANSITION
    global default_letter_size, default_letter_speed

    if pending_new_word_setup_time > 0 and current_time_ticks >= pending_new_word_setup_time:
        pending_new_word_setup_time = 0
        if current_game_mode == GAME_MODE_2P_VERSUS:
            # Game over check will be added here before transitioning
            current_game_state = STATE_SHOW_TURN_TRANSITION
        else:
            setup_new_word_for_active_player(current_time_ticks)

    if is_hint_timer_active and hints_used_this_word < HINTS_PER_WORD and pending_new_word_setup_time == 0:
        elapsed_time_since_last_action = current_time_ticks - hint_timer_start_time
        if elapsed_time_since_last_action >= HINT_TIMER_DURATION_MS:
            if current_letter_index < len(target_word):
                correct_letter_char = target_word[current_letter_index]; letter_to_animate_index = -1
                for state_preference in [STATE_NORMAL, STATE_PREVIEW]:
                    for i in range(num_letters):
                        if letters[i] == correct_letter_char and letter_states[i] == state_preference: letter_to_animate_index = i; break
                    if letter_to_animate_index != -1: break
                if letter_to_animate_index != -1:
                    idx = letter_to_animate_index
                    if letter_states[idx] == STATE_PREVIEW and previewed_letter_char == letters[idx]:
                        if idx in active_preview_letter_indices: active_preview_letter_indices.remove(idx)
                        if not active_preview_letter_indices: previewed_letter_char = None
                    letter_states[idx] = STATE_ANIMATING_TO_SLOT; letter_target_slot_indices[idx] = current_letter_index; letter_colors[idx] = GREEN
                    print(f"Hint used: Revealing letter '{correct_letter_char}' for slot {current_letter_index}.")
                    hints_used_this_word += 1; current_letter_index += 1
                    if correct_sound: correct_sound.play()

                    if hints_used_this_word >= HINTS_PER_WORD and current_letter_index < len(target_word):
                        player_idx_fail = current_player_turn - 1
                        if 0 <= player_idx_fail < len(player_failed_last_word): player_failed_last_word[player_idx_fail] = True
                        print(f"Player {current_player_turn} failed '{target_word}' after all hints.")
                        last_word_score = 0 ; show_last_word_score_until = current_time_ticks + SCORE_DISPLAY_DURATION_MS
                        show_feedback_message_until = current_time_ticks + 2000
                        pending_new_word_setup_time = current_time_ticks + 2000
                        is_hint_timer_active = False
                    elif current_letter_index == len(target_word):
                        player_idx_complete = current_player_turn - 1
                        if 0 <= player_idx_complete < len(player_failed_last_word): player_failed_last_word[player_idx_complete] = False
                        time_taken_ms = current_time_ticks - word_start_time ; base_score = get_word_base_score(target_word)
                        speed_mult = calculate_speed_multiplier(time_taken_ms, len(target_word)); score_for_this_word = int(base_score * speed_mult)
                        if 0 <= player_idx_complete < len(player_scores):
                            player_scores[player_idx_complete] += score_for_this_word
                            print(f"Player {current_player_turn} scored {score_for_this_word} for '{target_word}' (completed by hint). Total: {player_scores[player_idx_complete]}")
                        last_word_score = score_for_this_word; show_last_word_score_until = current_time_ticks + SCORE_DISPLAY_DURATION_MS
                        if word_complete_sound: word_complete_sound.play()
                        show_feedback_message_until = current_time_ticks + 2000 ; pending_new_word_setup_time = current_time_ticks + 2000
                        is_hint_timer_active = False
                    elif hints_used_this_word < HINTS_PER_WORD :
                        hint_timer_start_time = current_time_ticks; is_hint_timer_active = True
                    else: is_hint_timer_active = False
                else: print(f"Warning: Hint triggered for '{correct_letter_char}', but no suitable instance found in swarm."); hint_timer_start_time = current_time_ticks
            else: is_hint_timer_active = False
    if hints_used_this_word >= HINTS_PER_WORD: is_hint_timer_active = False

    if previewed_letter_char is not None and active_preview_letter_indices:
        still_in_preview_indices = []
        for i in list(active_preview_letter_indices):
            if i < len(letter_states) and letter_states[i] == STATE_PREVIEW:
                if current_time_ticks > letter_preview_timers[i] and letter_preview_timers[i] != 0:
                    letter_states[i] = STATE_NORMAL; letter_velocities[i] = original_letter_velocities[i] ; letter_preview_timers[i] = 0
                else: still_in_preview_indices.append(i)
        active_preview_letter_indices = still_in_preview_indices
        if not active_preview_letter_indices: previewed_letter_char = None

    for i in range(num_letters):
        x, y = letter_positions[i]; vx, vy = letter_velocities[i]; state = letter_states[i]
        current_letter_draw_size = default_letter_size
        if state == STATE_PREVIEW: current_letter_draw_size = ENLARGED_LETTER_SIZE
        if state == STATE_ANIMATING_TO_SLOT:
            slot_idx = letter_target_slot_indices[i]
            if slot_idx != -1:
                target_pos = get_slot_position(slot_idx); dx, dy = target_pos[0] - x, target_pos[1] - y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < ANIMATION_SPEED:
                    x, y = target_pos; vx, vy = 0, 0 ; letter_states[i] = STATE_PLACED ; letter_velocities[i] = (vx,vy)
                    if 0 <= slot_idx < len(displayed_word_chars): displayed_word_chars[slot_idx] = letters[i]
                else: vx = (dx / dist) * ANIMATION_SPEED; vy = (dy / dist) * ANIMATION_SPEED; x += vx; y += vy
            else: letter_states[i] = STATE_NORMAL
        elif state == STATE_NORMAL or state == STATE_PREVIEW:
            x += vx; y += vy
            if x < 0 or x > window_width - current_letter_draw_size: vx = -vx
            if y < 0 or y > window_height - current_letter_draw_size: vy = -vy
            letter_velocities[i] = (vx, vy)
        letter_positions[i] = (x,y)

def draw_game_play(window_surface, current_time_ticks):
    global letter_states, letter_positions, letter_colors, letter_feedback_flash_timers
    global letters, num_letters, default_letter_size, ENLARGED_LETTER_SIZE
    global displayed_word_chars, window_width, WHITE, GREEN
    global show_feedback_message_until, feedback_font, ui_font
    global HINTS_PER_WORD, hints_used_this_word, is_hint_timer_active, pending_new_word_setup_time
    global HINT_TIMER_DURATION_MS, hint_timer_start_time, show_clue_on_screen, current_clue_text
    global show_last_word_score_until, last_word_score, player_names, player_scores, current_player_turn, current_game_mode, player_failed_last_word

    # 1. Draw Swarming/Animating Letters
    for i in range(num_letters):
        x, y = letter_positions[i]; state = letter_states[i]
        current_letter_draw_size = default_letter_size
        if state == STATE_PREVIEW: current_letter_draw_size = ENLARGED_LETTER_SIZE
        if state != STATE_PLACED:
            current_display_color = letter_colors[i]
            if state == STATE_ANIMATING_TO_SLOT: current_display_color = GREEN
            elif letter_feedback_flash_timers[i] > current_time_ticks: current_display_color = RED
            letter_font = pygame.font.Font(None, current_letter_draw_size)
            letter_surface = letter_font.render(letters[i], True, current_display_color)
            window_surface.blit(letter_surface, (x, y))

    # 2. Draw Target Word Display
    font_target_word = pygame.font.Font(None, 50)
    display_text = " ".join(displayed_word_chars)
    text_target_word_surface = font_target_word.render(display_text, True, WHITE)
    text_rect_target_word = text_target_word_surface.get_rect(center=(window_width // 2, 30))
    window_surface.blit(text_target_word_surface, text_rect_target_word)

    # 3. Draw "Well Done!" / "Word Failed!" Message
    well_done_rect_bottom = 0
    if current_time_ticks < show_feedback_message_until:
        message_str = "Well Done!"
        message_color = GREEN
        player_idx = current_player_turn -1
        if 0 <= player_idx < len(player_failed_last_word) and player_failed_last_word[player_idx]:
            message_str = "Word Failed!"
            message_color = RED

        text_feedback = feedback_font.render(message_str, True, message_color)
        text_rect_feedback = text_feedback.get_rect(center=(window_width // 2, window_height // 2 - 30))
        window_surface.blit(text_feedback, text_rect_feedback)
        well_done_rect_bottom = text_rect_feedback.bottom

    # 4. Draw Last Word Score
    if show_last_word_score_until > current_time_ticks:
        score_text_str = f"Word Score: {last_word_score}"
        word_score_surface = ui_font.render(score_text_str, True, GREEN)
        y_offset_for_score = window_height // 2 + 20
        if current_time_ticks < show_feedback_message_until :
             y_offset_for_score = well_done_rect_bottom + 20
        word_score_rect = word_score_surface.get_rect(center=(window_width // 2, y_offset_for_score))
        window_surface.blit(word_score_surface, word_score_rect)

    # 5. Draw Top-Right UI (Hints, P2 Score)
    current_ui_y_offset_right = 20
    hints_text_str = f"Hints Left: {HINTS_PER_WORD - hints_used_this_word}/{HINTS_PER_WORD}"
    hints_surface = ui_font.render(hints_text_str, True, WHITE)
    hints_rect = hints_surface.get_rect(topright=(window_width - 20, current_ui_y_offset_right))
    window_surface.blit(hints_surface, hints_rect)
    current_ui_y_offset_right = hints_rect.bottom + 5

    if is_hint_timer_active and hints_used_this_word < HINTS_PER_WORD and pending_new_word_setup_time == 0 :
        time_since_timer_start = current_time_ticks - hint_timer_start_time
        time_remaining_s = max(0, (HINT_TIMER_DURATION_MS - time_since_timer_start) // 1000)
        timer_text_str = f"Next Hint: {time_remaining_s}s"
        timer_surface = ui_font.render(timer_text_str, True, WHITE)
        timer_rect = timer_surface.get_rect(topright=(window_width - 20, current_ui_y_offset_right))
        window_surface.blit(timer_surface, timer_rect)
        current_ui_y_offset_right = timer_rect.bottom + 5

    if current_game_mode == GAME_MODE_2P_VERSUS:
        p2_score_str = f"{player_names[1]}: {player_scores[1]}"
        p2_score_surface = ui_font.render(p2_score_str, True, WHITE)
        p2_score_rect = p2_score_surface.get_rect(topright=(window_width - 20, current_ui_y_offset_right))
        window_surface.blit(p2_score_surface, p2_score_rect)

    # 6. Draw Top-Left UI (Clue, P1 Score)
    current_ui_y_offset_left = 20
    if show_clue_on_screen and current_clue_text and pending_new_word_setup_time == 0:
        clue_surface = ui_font.render(f"Clue: {current_clue_text}", True, WHITE)
        clue_rect = clue_surface.get_rect(topleft=(20, current_ui_y_offset_left))
        window_surface.blit(clue_surface, clue_rect)
        current_ui_y_offset_left = clue_rect.bottom + 5

    p1_score_str = f"{player_names[0]}: {player_scores[0]}"
    p1_score_surface = ui_font.render(p1_score_str, True, WHITE)
    p1_score_rect = p1_score_surface.get_rect(topleft=(20, current_ui_y_offset_left))
    window_surface.blit(p1_score_surface, p1_score_rect)

    # 7. Draw Current Player's Turn (Bottom Center)
    active_player_name = player_names[current_player_turn - 1]
    turn_text_str = f"{active_player_name}'s Turn"
    turn_surface = ui_font.render(turn_text_str, True, WHITE)
    turn_rect = turn_surface.get_rect(center=(window_width // 2, window_height - 30))
    window_surface.blit(turn_surface, turn_rect)

# --- Turn Transition State ---
def handle_events_show_turn_transition(event):
    global current_game_state, running, current_player_turn
    if event.type == pygame.QUIT: running = False
    if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1): # Any key or left click
        current_player_turn = 2 if current_player_turn == 1 else 1
        setup_new_word_for_active_player(pygame.time.get_ticks())
        current_game_state = STATE_GAME_PLAY

def draw_show_turn_transition(window_surface):
    global turn_transition_button_rect, turn_transition_button_hovered

    player_who_just_finished_idx = (current_player_turn % 2) # If current P1 (turn 1), this is P2 (idx 1). If current P2 (turn 2), this is P1 (idx 0).
    # This is the player whose turn it *was*.
    # The current_player_turn variable still holds the player who just finished.
    ended_player_name = player_names[current_player_turn - 1]
    ended_player_score = player_scores[current_player_turn - 1]

    next_player_logical_turn = 2 if current_player_turn == 1 else 1
    next_player_name_display = player_names[next_player_logical_turn - 1]

    line1_text = f"{ended_player_name}'s turn is over."
    line2_text = f"Total Score: {ended_player_score}"
    line3_text = f"{next_player_name_display}, get ready!"
    button_text_str = "Click or Press Any Key to Start Turn"

    line1_surf = ui_font.render(line1_text, True, WHITE)
    line1_rect = line1_surf.get_rect(center=(window_width // 2, window_height // 2 - 100))
    window_surface.blit(line1_surf, line1_rect)

    line2_surf = ui_font.render(line2_text, True, WHITE)
    line2_rect = line2_surf.get_rect(center=(window_width // 2, window_height // 2 - 60))
    window_surface.blit(line2_surf, line2_rect)

    line3_surf = feedback_font.render(line3_text, True, GREEN)
    line3_rect = line3_surf.get_rect(center=(window_width // 2, window_height // 2))
    window_surface.blit(line3_surf, line3_rect)

    text_color = YELLOW if turn_transition_button_hovered else WHITE
    button_surface = ui_font.render(button_text_str, True, text_color)
    current_button_rect = button_surface.get_rect(center=(window_width // 2, window_height * 3 // 4 + 20))
    turn_transition_button_rect = current_button_rect
    window_surface.blit(button_surface, current_button_rect)


# --- Versus Game Over State ---
def handle_events_versus_game_over(event):
    global current_game_state, running, versus_game_over_buttons # Added versus_game_over_buttons
    if event.type == pygame.QUIT: running = False
    elif event.type == pygame.MOUSEMOTION:
        mouse_pos = pygame.mouse.get_pos()
        for key in versus_game_over_buttons:
            button = versus_game_over_buttons[key]
            if button["rect"] and button["rect"].collidepoint(mouse_pos): button["hovered"] = True
            else: button["hovered"] = False
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for key in versus_game_over_buttons:
                button = versus_game_over_buttons[key]
                if button["rect"] and button["rect"].collidepoint(mouse_pos):
                    action = button["action_state"]
                    if action == STATE_MAIN_MENU:
                        # setup_new_game_session() # Reset for a potential new game from main menu
                        current_game_state = STATE_MAIN_MENU
                    elif action == STATE_LEADERBOARD_DISPLAY:
                        current_game_state = STATE_LEADERBOARD_DISPLAY
                    break
def draw_versus_game_over(window_surface):
    global versus_game_over_buttons # Ensure it uses the global
    winner_text_str = "Game Over!"
    if player_scores[0] > player_scores[1]: winner_text_str = f"{player_names[0]} Wins!"
    elif player_scores[1] > player_scores[0]: winner_text_str = f"{player_names[1]} Wins!"
    else: winner_text_str = "It's a Tie!"

    score_p1_text = f"{player_names[0]}: {player_scores[0]}"
    score_p2_text = f"{player_names[1]}: {player_scores[1]}"

    winner_surface = feedback_font.render(winner_text_str, True, GREEN)
    winner_rect = winner_surface.get_rect(center=(window_width // 2, window_height // 2 - 100))

    score_p1_surface = ui_font.render(score_p1_text, True, WHITE)
    score_p1_rect = score_p1_surface.get_rect(center=(window_width // 2, window_height // 2 - 40))

    score_p2_surface = ui_font.render(score_p2_text, True, WHITE)
    score_p2_rect = score_p2_surface.get_rect(center=(window_width // 2, window_height // 2 -10))

    window_surface.blit(winner_surface, winner_rect)
    window_surface.blit(score_p1_surface, score_p1_rect)
    window_surface.blit(score_p2_surface, score_p2_rect)

    button_start_y = score_p2_rect.bottom + 70
    button_spacing = 60
    for index, key in enumerate(versus_game_over_buttons):
        button_info = versus_game_over_buttons[key]
        text_color = YELLOW if button_info['hovered'] else WHITE
        text_surf = menu_item_font.render(button_info['text'], True, text_color)
        y_pos = button_start_y + index * button_spacing
        button_rect = text_surf.get_rect(center=(window_width // 2, y_pos))
        versus_game_over_buttons[key]['rect'] = button_rect
        window_surface.blit(text_surf, button_rect)


# --- Leaderboard Display State ---
def handle_events_leaderboard_display(event):
    global current_game_state, running
    if event.type == pygame.QUIT: running = False
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RETURN:
            current_game_state = STATE_MAIN_MENU
def draw_leaderboard_display(window_surface):
    placeholder_text = ui_font.render(f"State: Leaderboard (Placeholder - Press Enter for Menu)", True, WHITE)
    text_rect = placeholder_text.get_rect(center=(window_width // 2, window_height // 2))
    window_surface.blit(placeholder_text, text_rect)

# ------------- Initial Game Setup Function (New) -------------
def setup_new_game_session():
    global target_word, current_clue_text, displayed_word_chars, current_letter_index
    global word_start_time, hints_used_this_word, hint_timer_start_time, is_hint_timer_active
    global show_clue_on_screen, previewed_letter_char, active_preview_letter_indices
    global pending_new_word_setup_time, last_word_score, show_last_word_score_until
    global letter_states, letter_positions, letter_velocities, original_letter_velocities
    global letter_colors, letter_preview_timers, letter_target_slot_indices, letter_feedback_flash_timers
    global current_player_turn, player_scores, player_name_inputs, input_active_player, player_failed_last_word

    if current_game_state == STATE_PLAYER_NAME_INPUT: # Called when transitioning from Main Menu to Player Name Input
         player_scores = [0,0]
         current_player_turn = 1 # Player 1 always starts a new game session
         player_names = ["Player 1", "Player 2"] # Reset to defaults before input

    player_name_inputs = ["", ""]
    input_active_player = 0
    player_failed_last_word = [False, False]

    pending_new_word_setup_time = 0
    last_word_score = 0
    show_last_word_score_until = 0
    show_feedback_message_until = 0

    # Word setup is now primarily in setup_new_word_for_active_player
    # This function mainly resets session-wide variables.
    # For the very first word after name input, setup_new_word_for_active_player will be called
    # when transitioning from STATE_PLAYER_NAME_INPUT to STATE_GAME_PLAY.

def setup_new_word_for_current_player(current_time_ticks): # Renamed from previous plan
    """Sets up a new word, resets hints, timers, and letter states for the current active player."""
    global target_word, current_clue_text, displayed_word_chars, current_letter_index
    global word_start_time, hints_used_this_word, hint_timer_start_time, is_hint_timer_active
    global show_clue_on_screen, previewed_letter_char, active_preview_letter_indices
    global letter_states, letter_positions, letter_velocities, original_letter_velocities
    global letter_colors, letter_preview_timers, letter_target_slot_indices, letter_feedback_flash_timers
    global player_failed_last_word, current_player_turn

    selected_word_obj = random.choice(simple_words)
    target_word = selected_word_obj['word']
    current_clue_text = selected_word_obj['clue']
    displayed_word_chars = ['_'] * len(target_word)
    current_letter_index = 0

    word_start_time = current_time_ticks
    hints_used_this_word = 0
    hint_timer_start_time = current_time_ticks
    is_hint_timer_active = True
    show_clue_on_screen = True
    previewed_letter_char = None
    active_preview_letter_indices = []

    player_idx = current_player_turn - 1
    if 0 <= player_idx < len(player_failed_last_word):
        player_failed_last_word[player_idx] = False

    for i in range(num_letters):
        letter_states[i] = STATE_NORMAL
        letter_positions[i] = (random.randint(0, window_width - default_letter_size),
                               random.randint(0, window_height - default_letter_size))
        angle = random.uniform(0, 2 * math.pi)
        speed = random.randint(1, default_letter_speed)
        vx_new = math.cos(angle) * speed
        vy_new = math.sin(angle) * speed
        letter_velocities[i] = (vx_new, vy_new)
        original_letter_velocities[i] = (vx_new, vy_new)
        letter_colors[i] = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        letter_preview_timers[i] = 0
        letter_target_slot_indices[i] = -1
        letter_feedback_flash_timers[i] = 0

    print(f"Player {current_player_turn}'s turn. New word: {target_word}")


# ------------- Main Game Loop -------------
running = True
while running:
    current_time = pygame.time.get_ticks()

    # --- Event Handling (State-Dependent) ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

        if current_game_state == STATE_MAIN_MENU:
            handle_events_main_menu(event)
        elif current_game_state == STATE_PLAYER_NAME_INPUT:
            handle_events_player_name_input(event)
        elif current_game_state == STATE_GAME_PLAY:
            handle_events_game_play(event, current_time)
        elif current_game_state == STATE_SHOW_TURN_TRANSITION:
            handle_events_show_turn_transition(event)
        elif current_game_state == STATE_VERSUS_GAME_OVER:
            handle_events_versus_game_over(event)
        elif current_game_state == STATE_LEADERBOARD_DISPLAY:
            handle_events_leaderboard_display(event)

    if not running: break

    # --- Game Logic Updates (State-Dependent) ---
    if current_game_state == STATE_GAME_PLAY:
        update_game_play_logic(current_time)
    elif current_game_state == STATE_PLAYER_NAME_INPUT:
        update_player_name_input_logic(current_time)

    # --- Drawing (State-Dependent) ---
    window.fill(BLACK)
    if current_game_state == STATE_MAIN_MENU:
        draw_main_menu(window)
    elif current_game_state == STATE_PLAYER_NAME_INPUT:
        draw_player_name_input(window)
    elif current_game_state == STATE_GAME_PLAY:
        draw_game_play(window, current_time)
    elif current_game_state == STATE_SHOW_TURN_TRANSITION:
        draw_show_turn_transition(window)
    elif current_game_state == STATE_VERSUS_GAME_OVER:
        draw_versus_game_over(window)
    elif current_game_state == STATE_LEADERBOARD_DISPLAY:
        draw_leaderboard_display(window)

    pygame.display.update()
    clock.tick(120)

# ------------- Game Exit -------------
pygame.quit()
sys.exit()

[end of AlphabetSwarm.py]
