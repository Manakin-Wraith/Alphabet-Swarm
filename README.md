# Alphabet Swarm

Alphabet Swarm is an interactive game where letters swarm around the screen, and the player's goal is to spell a target word by typing the letters in the correct order. The game features a unique two-step preview/confirm mechanism for selecting letters, adding a layer of strategy and challenge.

## Features

*   **Engaging Gameplay:** Watch as letters of the alphabet move dynamically across the screen.
*   **Multiple Game Modes:**
    *   **1-Player Mode:** A single-player experience where you try to achieve a high score.
    *   **2-Player Versus Mode:** Compete against a friend to see who can score higher.
*   **Word Spelling Challenge:** Test your spelling skills with a list of words and their corresponding clues.
*   **Interactive Letter Selection:**
    *   **Preview:** Press a key to preview which letters will be selected.
    *   **Confirm:** Press the same key again to confirm your choice.
*   **Scoring System:** Earn points based on the length of the word and how quickly you spell it.
*   **Hint System:** Get up to three hints per word if you're stuck.
*   **Leaderboard:** Your high scores are saved, so you can track your progress and compete for the top spot.
*   **Sound Effects:** Optional sound effects for correct and incorrect moves enhance the gaming experience.
*   **Customizable Word Lists:** The game can load words from an external `words.txt` file, allowing for easy customization.

## How to Play

1.  **Start the Game:** Run the `AlphabetSwarm.py` script.
2.  **Main Menu:** From the main menu, you can choose to start a 1-player game, a 2-player versus game, view the leaderboard, or quit.
3.  **Enter Your Name:** You will be prompted to enter your name before the game starts.
4.  **Gameplay:**
    *   A clue for the target word will be displayed at the top of the screen.
    *   The letters of the alphabet will swarm around the screen.
    *   To select a letter, press the corresponding key on your keyboard. This will "preview" the letter, causing it to enlarge.
    *   To confirm the selection, press the same key again.
    *   If the selected letter is the correct one in the sequence of the target word, it will move to its designated slot at the top of the screen.
    *   If you select the wrong letter, you'll get feedback, and you can try again.
5.  **Hints:** If you are stuck, wait for a short period, and a hint will automatically be used to reveal the next letter.
6.  **Scoring:** Spell the word correctly to score points. The faster you are, the more points you get.
7.  **Winning (2-Player Mode):** In 2-player versus mode, the player with the highest score at the end of the game wins.

## Requirements

To run Alphabet Swarm, you need to have Python and the Pygame library installed.

*   **Python 3.x**
*   **Pygame:** You can install it using pip:
    ```
    pip install pygame
    ```

The game also looks for the following optional files in the same directory:

*   `words.txt`: A text file containing custom words and clues. If not found, a default list of words is used.
*   `correct.wav`: A sound file to be played for a correct move.
*   `incorrect.wav`: A sound file to be played for an incorrect move.
*   `word_complete.wav`: A sound file to be played upon successful completion of a word.

## Installation and Running

1.  **Clone the Repository:**
    ```
    git clone <repository-url>
    cd <repository-directory>
    ```
2.  **Install Dependencies:**
    ```
    pip install -r requirements.txt
    ```
3.  **Run the Game:**
    ```
    python AlphabetSwarm.py
    ```

## File Structure

*   `AlphabetSwarm.py`: The main script containing the entire game logic.
*   `.gitignore`: Standard gitignore file.
*   `README.md`: This file.
*   `words.txt` (optional): A file to customize the words and clues used in the game. Each line should be in the format: `word,clue`.
*   `leaderboard.json` (generated): This file is automatically created to store high scores.

## Contributing

Contributions are welcome! If you have ideas for new features, bug fixes, or improvements, feel free to fork the repository and submit a pull request. You can also open an issue to report a bug or suggest a feature.
