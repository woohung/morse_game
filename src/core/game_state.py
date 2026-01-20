"""
Game state management for Morse Code Game
"""
from enum import Enum
from typing import Optional, List, Dict, Any
import time
from .config import WORD_TIME_LIMIT, TIME_PER_LETTER, O_LETTER_BONUS, DIFFICULTY_SETTINGS
from ..data.high_scores import HighScoreManager

class GameState(Enum):
    """Game states enumeration."""
    MAIN_MENU = "main_menu"
    NUMBERED_MENU = "numbered_menu"  # New numbered menu with Morse input
    DIFFICULTY_SELECT = "difficulty_select"
    NICKNAME_INPUT = "nickname_input"
    PLAYING = "playing"
    PRACTICE = "practice"  # New practice mode for single letter training
    GAME_OVER = "game_over"
    HIGH_SCORES = "high_scores"

class GameData:
    """Store game session data."""
    def __init__(self):
        self.nickname: str = ""
        self.difficulty: str = "easy"  # "easy" or "hard"
        self.current_word: str = ""
        self.current_input: str = ""
        self.words_completed: int = 0
        self.score: int = 0
        self.time_remaining: float = 120.0  # Will be set based on difficulty
        self.game_start_time: Optional[float] = None
        self.word_states: List[Dict[str, Any]] = []  # Track letter states
        self.letter_colors: List[str] = []  # Track colors for each letter
        self.current_letter_index: int = 0  # Track which letter we're working on
        self.letter_errors: Dict[int, int] = {}  # Track errors per letter
        self.total_errors: int = 0  # Track total errors for tie-breaking
        self.word_start_time: Optional[float] = None  # Track when current word started
        self.word_time_limit: float = WORD_TIME_LIMIT  # Time limit per word in seconds
        
        # Practice mode specific data
        self.practice_letter: str = ""  # Current letter for practice
        self.practice_letter_color: str = "white"  # Color state for practice letter
        self.practice_completed: int = 0  # Number of letters completed in practice
        self.practice_errors: int = 0  # Errors in practice mode
        
        # Error effect data
        self.error_time: Optional[float] = None  # Time when error occurred for glitch effect

class MenuOption:
    """Menu option class."""
    def __init__(self, text: str, action: str, y_position: int):
        self.text = text
        self.action = action
        self.y_position = y_position
        self.selected = False

class GameStateManager:
    """Manage game states and transitions."""
    def __init__(self):
        self.current_state = GameState.MAIN_MENU
        self.game_data = GameData()
        self.menu_options: List[MenuOption] = []
        self.difficulty_options: List[MenuOption] = []
        self.numbered_menu_options: List[MenuOption] = []  # New numbered menu
        self.selected_menu_index = 0
        self.selected_difficulty_index = 0
        self.nickname_input = ""
        self.morse_input = ""  # New Morse input for numbered menu
        self.cursor_visible = True
        self.cursor_timer = 0
        self.high_score_difficulty = 'easy'  # Track which difficulty scores to show
        self.high_score_manager = HighScoreManager()  # Add high score manager
        self.nickname_error = False  # Track nickname availability error
        
        # Initialize menus
        self._init_main_menu()
        self._init_difficulty_menu()
        self._init_numbered_menu()  # Initialize numbered menu
    
    def _init_main_menu(self):
        """Initialize main menu options."""
        self.menu_options = [
            MenuOption("START TRANSMISSION", "start", 300),
            MenuOption("PRACTICE", "practice", 350),
            MenuOption("OPERATORS LOG", "high_scores", 400),
            MenuOption("DISCONNECT", "exit", 450)
        ]
        self.selected_menu_index = 0
        self.menu_options[0].selected = True
    
    def _init_difficulty_menu(self):
        """Initialize difficulty selection menu."""
        self.difficulty_options = [
            MenuOption("TELEGRAPH BEGINNER (EASY)", "easy", 300),
            MenuOption("CONFIDENT OPERATOR (HARD)", "hard", 350),
            MenuOption("BACK TO TERMINAL", "back", 400)
        ]
        self.selected_difficulty_index = 0
        self.difficulty_options[0].selected = True
    
    def _init_numbered_menu(self):
        """Initialize numbered menu with Morse input support."""
        self.numbered_menu_options = [
            MenuOption("ПРИЕМ СООБЩЕНИЙ", "start", 0),
            MenuOption("СТАТИСТИКА СВЯЗИ", "high_scores", 1),
            MenuOption("НАСТРОЙКИ ТЕРМИНАЛА", "settings", 2),
            MenuOption("ПОМОЩЬ ОПЕРАТОРУ", "help", 3),
            MenuOption("ЗАВЕРШИТЬ СЕАНС", "exit", 4)
        ]
        self.morse_input = ""  # Reset Morse input when menu is initialized
    
    def change_state(self, new_state: GameState):
        """Change game state."""
        self.current_state = new_state
        if new_state == GameState.MAIN_MENU:
            self._init_main_menu()
        elif new_state == GameState.NUMBERED_MENU:
            self._init_numbered_menu()
        elif new_state == GameState.DIFFICULTY_SELECT:
            self._init_difficulty_menu()
        elif new_state == GameState.NICKNAME_INPUT:
            self.nickname_input = ""
        elif new_state == GameState.PLAYING:
            # Don't reset game_data here - it should be set when game actually starts
            # This preserves the nickname that was set
            if not hasattr(self.game_data, 'nickname') or not self.game_data.nickname:
                # Preserve difficulty when creating new GameData
                old_difficulty = self.game_data.difficulty if hasattr(self.game_data, 'difficulty') else 'easy'
                self.game_data = GameData()
                self.game_data.difficulty = old_difficulty
            self.game_data.game_start_time = time.time()
        elif new_state == GameState.PRACTICE:
            # Initialize practice mode - don't reset letter if already set
            if not self.game_data.practice_letter:
                self.game_data.practice_letter = ""
            self.game_data.practice_completed = 0
            self.game_data.practice_errors = 0
    
    def move_menu_selection(self, direction: int):
        """Move menu selection up or down."""
        if self.current_state == GameState.MAIN_MENU:
            self.menu_options[self.selected_menu_index].selected = False
            self.selected_menu_index = (self.selected_menu_index + direction) % len(self.menu_options)
            self.menu_options[self.selected_menu_index].selected = True
        elif self.current_state == GameState.DIFFICULTY_SELECT:
            self.difficulty_options[self.selected_difficulty_index].selected = False
            self.selected_difficulty_index = (self.selected_difficulty_index + direction) % len(self.difficulty_options)
            self.difficulty_options[self.selected_difficulty_index].selected = True
    
    def get_selected_menu_action(self) -> str:
        """Get action of selected menu item."""
        if self.current_state == GameState.MAIN_MENU:
            return self.menu_options[self.selected_menu_index].action
        elif self.current_state == GameState.DIFFICULTY_SELECT:
            return self.difficulty_options[self.selected_difficulty_index].action
        return ""
    
    def get_selected_difficulty(self) -> str:
        """Get selected difficulty."""
        if self.current_state == GameState.DIFFICULTY_SELECT:
            return self.difficulty_options[self.selected_difficulty_index].action
        return "easy"
    
    def switch_high_score_difficulty(self):
        """Switch between difficulty high scores."""
        self.high_score_difficulty = 'hard' if self.high_score_difficulty == 'easy' else 'easy'
    
    def update_cursor(self, current_time: float):
        """Update cursor visibility for blinking effect."""
        if current_time - self.cursor_timer > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time
    
    def add_nickname_char(self, char: str):
        """Add character to nickname input."""
        if len(self.nickname_input) < 15:  # Limit nickname length
            self.nickname_input += char
            self.nickname_error = False  # Reset error when user types
    
    def remove_nickname_char(self):
        """Remove last character from nickname input."""
        if self.nickname_input:
            self.nickname_input = self.nickname_input[:-1]
            self.nickname_error = False  # Reset error when user deletes
    
    def confirm_nickname(self):
        """Confirm nickname and start game."""
        if self.nickname_input.strip():
            # Check if nickname is unique
            if not self.high_score_manager.is_nickname_available(self.nickname_input.strip()):
                self.nickname_error = True  # Set error flag
                return False  # Nickname already exists
            
            # Reset error flag on successful validation
            self.nickname_error = False
            
            # Set nickname first, then change state
            if not hasattr(self.game_data, 'nickname') or not self.game_data.nickname:
                # Preserve difficulty when creating new GameData
                old_difficulty = self.game_data.difficulty if hasattr(self.game_data, 'difficulty') else 'easy'
                self.game_data = GameData()
                self.game_data.difficulty = old_difficulty
            self.game_data.nickname = self.nickname_input.strip()
            return True
        return False
    
    def start_word_timer(self, word: str = ""):
        """Start timer for current word with dynamic time calculation."""
        self.game_data.word_start_time = time.time()
        
        # Calculate dynamic time limit based on word and difficulty
        if word:
            settings = DIFFICULTY_SETTINGS.get(self.game_data.difficulty, DIFFICULTY_SETTINGS['easy'])
            base_time = settings['word_time_limit']
            letter_time = len(word) * settings['time_per_letter']
            o_bonus = word.upper().count('O') * settings['o_letter_bonus']
            self.game_data.word_time_limit = base_time + letter_time + o_bonus
            print(f"Word '{word}' ({self.game_data.difficulty}) - Time limit: {self.game_data.word_time_limit:.1f}s (base: {base_time}s, letters: {letter_time}s, O-bonus: {o_bonus}s)")
        else:
            self.game_data.word_time_limit = WORD_TIME_LIMIT
    
    def is_word_time_expired(self) -> bool:
        """Check if word time limit has expired."""
        if self.game_data.word_start_time is None:
            return False
        return (time.time() - self.game_data.word_start_time) > self.game_data.word_time_limit
    
    def get_word_time_remaining(self) -> float:
        """Get remaining time for current word."""
        if self.game_data.word_start_time is None:
            return self.game_data.word_time_limit
        elapsed = time.time() - self.game_data.word_start_time
        return max(0, self.game_data.word_time_limit - elapsed)
    
    def add_error(self):
        """Add an error to the total count."""
        self.game_data.total_errors += 1
    
    def set_difficulty(self, difficulty: str):
        """Set game difficulty."""
        if difficulty in ['easy', 'hard']:
            self.game_data.difficulty = difficulty
            # Update game duration based on difficulty
            settings = DIFFICULTY_SETTINGS[difficulty]
            self.game_data.time_remaining = settings['game_duration']
            print(f"Difficulty set to: {difficulty}, Game duration: {settings['game_duration']}s")
    
    def get_difficulty_settings(self):
        """Get current difficulty settings."""
        return DIFFICULTY_SETTINGS.get(self.game_data.difficulty, DIFFICULTY_SETTINGS['easy'])
    
    def add_morse_char(self, char: str):
        """Add Morse character to input."""
        if char in ['.', '-', ' ']:
            self.morse_input += char
    
    def clear_morse_input(self):
        """Clear Morse input."""
        self.morse_input = ""
    
    def process_numbered_menu_selection(self) -> Optional[str]:
        """Process selection from numbered menu (either number or Morse)."""
        if self.morse_input.isdigit():
            # Direct number input
            try:
                num = int(self.morse_input) - 1  # Convert to 0-based index
                if 0 <= num < len(self.numbered_menu_options):
                    return self.numbered_menu_options[num].action
            except ValueError:
                pass
        else:
            # Try to decode Morse input
            try:
                from .morse_decoder import MorseDecoder
                decoder = MorseDecoder()
                decoded = decoder.decode(self.morse_input)
                if decoded.isdigit():
                    num = int(decoded) - 1  # Convert to 0-based index
                    if 0 <= num < len(self.numbered_menu_options):
                        return self.numbered_menu_options[num].action
            except:
                pass
        
        return None  # Invalid selection
    
    def get_numbered_menu_action_by_number(self, number: int) -> Optional[str]:
        """Get menu action by number (for direct key input)."""
        if 1 <= number <= len(self.numbered_menu_options):
            return self.numbered_menu_options[number - 1].action
        return None
