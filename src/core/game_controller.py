"""
Game Controller for Morse Code Game
Handles game logic and state transitions.
"""
import time
import random
import string
from typing import Optional
from .game_state import GameStateManager, GameState
from .word_generator import WordGenerator
from .morse_decoder import MorseDecoder
from ..data.high_scores import HighScoreManager
from ..hardware.megohmmeter_control import MegohmmeterController, MockMegohmmeterController


class GameController:
    """Controls game logic and manages game state."""
    
    def __init__(self, state_manager: GameStateManager):
        self.state_manager = state_manager
        self.word_generator = WordGenerator()
        self.decoder = MorseDecoder()
        self.high_scores = HighScoreManager()
        self.current_sequence = ""
        self.last_element_time: Optional[float] = None
        self.last_timeout_check = time.time()  # Initialize timeout check timer
        
        # Initialize megohmmeter
        self.megohmmeter = self._initialize_megohmmeter()
    
    def _initialize_megohmmeter(self):
        """Initialize megohmmeter controller."""
        from .config import (MEGOHMMETER_PIN, MEGOHMMETER_PULLBACK_PIN, MEGOHMMETER_PWM_FREQUENCY, 
                          MEGOHMMETER_BASELINE_FORCE, MEGOHMMETER_DOT_AMPLITUDE, 
                          MEGOHMMETER_DASH_AMPLITUDE)
        
        try:
            # Try to initialize real megohmmeter
            megohmmeter = MegohmmeterController(
                meter_pin=MEGOHMMETER_PIN,
                pullback_pin=MEGOHMMETER_PULLBACK_PIN,
                pwm_frequency=MEGOHMMETER_PWM_FREQUENCY
            )
            if megohmmeter.initialize():
                # Set configuration parameters
                megohmmeter.baseline_force = MEGOHMMETER_BASELINE_FORCE
                megohmmeter.dot_amplitude = MEGOHMMETER_DOT_AMPLITUDE
                megohmmeter.dash_amplitude = MEGOHMMETER_DASH_AMPLITUDE
                
                print(f"Мегомметр инициализирован:")
                print(f"  Основная катушка: GPIO {MEGOHMMETER_PIN}")
                print(f"  Оттягивающая катушка: GPIO {MEGOHMMETER_PULLBACK_PIN}")
                print(f"  Сила оттягивания: {MEGOHMMETER_BASELINE_FORCE}")
                print(f"  Амплитуда точки: {MEGOHMMETER_DOT_AMPLITUDE}")
                print(f"  Амплитуда тире: {MEGOHMMETER_DASH_AMPLITUDE}")
                return megohmmeter
            else:
                print("Не удалось инициализировать мегомметр, используем mock")
        except Exception as e:
            print(f"Ошибка при инициализации мегомметра: {e}")
        
        # Fallback to mock
        mock_megohmmeter = MockMegohmmeterController(
            meter_pin=MEGOHMMETER_PIN,
            pullback_pin=MEGOHMMETER_PULLBACK_PIN,
            pwm_frequency=MEGOHMMETER_PWM_FREQUENCY
        )
        mock_megohmmeter.baseline_force = MEGOHMMETER_BASELINE_FORCE
        mock_megohmmeter.dot_amplitude = MEGOHMMETER_DOT_AMPLITUDE
        mock_megohmmeter.dash_amplitude = MEGOHMMETER_DASH_AMPLITUDE
        
        print(f"Mock мегомметр с параметрами:")
        print(f"  Основная катушка: GPIO {MEGOHMMETER_PIN}")
        print(f"  Оттягивающая катушка: GPIO {MEGOHMMETER_PULLBACK_PIN}")
        print(f"  Сила оттягивания: {MEGOHMMETER_BASELINE_FORCE}")
        print(f"  Амплитуда точки: {MEGOHMMETER_DOT_AMPLITUDE}")
        print(f"  Амплитуда тире: {MEGOHMMETER_DASH_AMPLITUDE}")
        
        return mock_megohmmeter
    
    def cleanup(self):
        """Clean up megohmmeter resources when exiting application."""
        if self.megohmmeter:
            self.megohmmeter.cleanup()
    
    def start_new_game(self):
        """Start a new game session."""
        print(f"Starting new game for player: {self.state_manager.game_data.nickname}")
        
        # Reset megohmmeter needle before starting new game
        if self.megohmmeter:
            self.megohmmeter.force_reset()
        
        # Set up difficulty-based settings
        difficulty = self.state_manager.game_data.difficulty
        settings = self.state_manager.get_difficulty_settings()
        
        # Configure word generator for difficulty
        self.word_generator.set_difficulty(difficulty)
        self.word_generator.reset()
        
        # Get first word
        self.state_manager.game_data.current_word = self.word_generator.get_random_word()
        self.state_manager.game_data.letter_colors = ['white'] * len(self.state_manager.game_data.current_word)
        self.state_manager.game_data.current_letter_index = 0
        self.state_manager.game_data.letter_errors = {}
        self.state_manager.game_data.words_completed = 0
        self.state_manager.game_data.score = 0
        self.state_manager.game_data.time_remaining = settings['game_duration']
        self.state_manager.game_data.total_errors = 0
        self.state_manager.game_data.game_start_time = time.time()
        self.current_sequence = ""
        self.last_timeout_check = time.time()  # Reset timeout check timer
        print(f"First word: {self.state_manager.game_data.current_word} (difficulty: {difficulty})")
        
        # Start timer for first word
        self.state_manager.start_word_timer(self.state_manager.game_data.current_word)
        
        # Change state after setting all game data
        self.state_manager.change_state(GameState.PLAYING)
    
    def on_key_press(self):
        """Handle Morse key press during gameplay."""
        if self.state_manager.current_state == GameState.PLAYING:
            self.state_manager.cursor_visible = True
            self.state_manager.cursor_timer = time.time()
            # Move megohmmeter needle to maximum when key is pressed
            if self.megohmmeter:
                self.megohmmeter.key_pressed()
    
    def on_key_release(self, press_duration: float):
        """Handle Morse key release during gameplay."""
        from .config import DEBOUNCE_TIME, DOT_DURATION, DASH_DURATION
        
        if self.state_manager.current_state != GameState.PLAYING:
            return
        
        # Return megohmmeter needle to baseline when key is released
        if self.megohmmeter:
            self.megohmmeter.key_released()
            
        now = time.time()

        # Ignore debounce
        if press_duration < DEBOUNCE_TIME:
            return

        # Determine dot or dash and apply appropriate amplitude
        threshold = (DOT_DURATION + DASH_DURATION) / 2
        if press_duration < threshold:
            self.current_sequence += "."
            print("Added: . (dot)")
            # Apply dot amplitude to megohmmeter
            if self.megohmmeter:
                self.megohmmeter.apply_dot()
        else:
            self.current_sequence += "-"
            print("Added: - (dash)")
            # Apply dash amplitude to megohmmeter
            if self.megohmmeter:
                self.megohmmeter.apply_dash()

        print(f"Current sequence: {self.current_sequence}")

        # Update timers
        self.last_element_time = now
        self.state_manager.cursor_visible = True
        self.state_manager.cursor_timer = now
    
    def check_morse_input(self):
        """Check if current Morse sequence matches the current letter in the word."""
        if not self.current_sequence or self.state_manager.current_state != GameState.PLAYING:
            return
        
        # Try to decode the current sequence
        decoded_char = self.decoder.decode(self.current_sequence)
        
        # If decoding failed (unknown pattern), clear input and return
        if not decoded_char:
            print(f"Unknown pattern '{self.current_sequence}' - clearing input")
            self.current_sequence = ""
            return
        
        current_word = self.state_manager.game_data.current_word
        current_index = self.state_manager.game_data.current_letter_index
        letter_colors = self.state_manager.game_data.letter_colors
        
        # Check if we've completed the word
        if current_index >= len(current_word):
            return
        
        target_char = current_word[current_index]
        
        if decoded_char == target_char:
            # Correct letter found
            letter_colors[current_index] = 'green'
            self.state_manager.game_data.letter_colors = letter_colors
            print(f"Correct! Found '{decoded_char}' at position {current_index}")
            
            # Move to next letter
            self.state_manager.game_data.current_letter_index += 1
            
            # Check if word is complete
            if self.state_manager.game_data.current_letter_index >= len(current_word):
                self._word_completed()
        else:
            # Wrong letter - increment error count
            error_count = self.state_manager.game_data.letter_errors.get(current_index, 0) + 1
            self.state_manager.game_data.letter_errors[current_index] = error_count
            
            # Add to total errors for tie-breaking
            self.state_manager.add_error()
            
            # Mark as red and trigger glitch effect
            letter_colors[current_index] = 'red'
            self.state_manager.game_data.letter_colors = letter_colors
            self.state_manager.game_data.error_time = time.time()  # Set error time for glitch effect
            print(f"Wrong! '{decoded_char}' doesn't match '{target_char}' (errors: {error_count})")
        
        # Reset current sequence
        self.current_sequence = ""
    
    def clear_current_input(self):
        """Clear current Morse input and reset current letter only."""
        if self.state_manager.current_state == GameState.PLAYING:
            self.current_sequence = ""
            # Reset only current letter if it's red
            current_index = self.state_manager.game_data.current_letter_index
            letter_colors = self.state_manager.game_data.letter_colors
            if current_index < len(letter_colors) and letter_colors[current_index] == 'red':
                letter_colors[current_index] = 'white'
                self.state_manager.game_data.letter_colors = letter_colors
                # Reset error count for this letter
                if current_index in self.state_manager.game_data.letter_errors:
                    del self.state_manager.game_data.letter_errors[current_index]
    
    def check_timeouts(self):
        """Check for timeouts in Morse code input during gameplay or practice."""
        from .config import LETTER_GAP
        
        # Handle practice mode timeouts
        if self.state_manager.current_state == GameState.PRACTICE:
            self.check_practice_timeouts()
            # Periodically ensure needle is at zero when not pressed in practice mode
            self._ensure_needle_at_zero()
            return
        
        if self.state_manager.current_state != GameState.PLAYING:
            # Ensure needle is at zero when not in playing state
            self._ensure_needle_at_zero()
            return

        now = time.time()
        delta = now - getattr(self, 'last_timeout_check', now)
        self.last_timeout_check = now

        # Check for Morse character completion
        if self.current_sequence and self.last_element_time is not None:
            if now - self.last_element_time >= LETTER_GAP:
                self.check_morse_input()
                self.last_element_time = now
        
        # Check word timer
        if self.state_manager.is_word_time_expired():
            print(f"Word time expired! Moving to next word without counting.")
            self._word_time_expired()
        
        # Decrease game time by delta (this preserves bonus time)
        if self.state_manager.game_data.game_start_time:
            self.state_manager.game_data.time_remaining = max(0, self.state_manager.game_data.time_remaining - delta)
            
            if self.state_manager.game_data.time_remaining <= 0:
                self.end_game()
    
    def _ensure_needle_at_zero(self):
        """Ensure needle is at baseline when key should not be pressed."""
        if self.megohmmeter and hasattr(self.megohmmeter, 'current_value'):
            # Only check if we have access to GPIO handler state
            if hasattr(self, '_last_gpio_state_check'):
                if time.time() - self._last_gpio_state_check > 0.5:  # Check every 0.5 seconds
                    baseline = self.megohmmeter.baseline_force
                    tolerance = 0.02  # Допуск вокруг базового подпора
                    if abs(self.megohmmeter.current_value - baseline) > tolerance:
                        print(f"Мегомметр: обнаружено отклонение от базового подпора, принудительный сброс")
                        self.megohmmeter.force_reset()
                    self._last_gpio_state_check = time.time()
            else:
                self._last_gpio_state_check = time.time()
    
    def _word_completed(self):
        """Handle successful completion of current word."""
        self.state_manager.game_data.words_completed += 1
        self.state_manager.increment_streak()
        print(f"Word completed successfully! Total: {self.state_manager.game_data.words_completed}")
        print(f"Current streak: {self.state_manager.game_data.streak_count} words without errors")
        
        # Check for time bonus based on difficulty
        settings = self.state_manager.get_difficulty_settings()
        
        if self.state_manager.game_data.difficulty == 'hard':
            # Hard mode: bonus every 3 consecutive correct words without errors
            bonus_every = 3  # Fixed to 3 consecutive words
            bonus_amount = settings.get('time_bonus_amount', 0)
            
            if bonus_amount > 0:
                if self.state_manager.game_data.streak_count > 0 and self.state_manager.game_data.streak_count % bonus_every == 0:
                    # Add bonus time
                    old_time = self.state_manager.game_data.time_remaining
                    self.state_manager.game_data.time_remaining += bonus_amount
                    # Set bonus effect data
                    self.state_manager.game_data.bonus_time_received = time.time()
                    self.state_manager.game_data.bonus_amount = bonus_amount
                    print(f"STREAK BONUS! +{bonus_amount}s added ({self.state_manager.game_data.streak_count} consecutive correct words!)")
                    print(f"Time before: {old_time:.1f}s, Time after: {self.state_manager.game_data.time_remaining:.1f}s")
        
        elif self.state_manager.game_data.difficulty == 'easy':
            # Easy mode: streak bonus
            streak_every = settings.get('streak_bonus_every_words', 0)
            streak_amount = settings.get('streak_bonus_amount', 0)
            
            if streak_every > 0 and streak_amount > 0:
                if self.state_manager.game_data.streak_count == streak_every:
                    # Add streak bonus time
                    old_time = self.state_manager.game_data.time_remaining
                    self.state_manager.game_data.time_remaining += streak_amount
                    # Set bonus effect data
                    self.state_manager.game_data.bonus_time_received = time.time()
                    self.state_manager.game_data.bonus_amount = streak_amount
                    print(f"STREAK BONUS! +{streak_amount}s added ({self.state_manager.game_data.streak_count} word streak!)")
                    print(f"Time before: {old_time:.1f}s, Time after: {self.state_manager.game_data.time_remaining:.1f}s")
        
        self._get_next_word()
    
    def _word_time_expired(self):
        """Handle word time expiration - move to next word without counting."""
        print(f"Word time expired! Word not counted.")
        self.state_manager.reset_streak()  # Reset streak on timeout
        self._get_next_word()
    
    def _get_next_word(self):
        """Get next word and reset state."""
        # Get new word
        self.state_manager.game_data.current_word = self.word_generator.get_random_word()
        self.state_manager.game_data.letter_colors = ['white'] * len(self.state_manager.game_data.current_word)
        self.state_manager.game_data.current_letter_index = 0
        self.state_manager.game_data.letter_errors = {}
        self.current_sequence = ""
        
        # Reset error tracking for new word
        self.state_manager.start_new_word()
        
        # Start timer for new word
        self.state_manager.start_word_timer(self.state_manager.game_data.current_word)
    
    def end_game(self):
        """End the current game session."""
        # Reset megohmmeter needle instead of cleaning up resources
        if self.megohmmeter:
            self.megohmmeter.force_reset()
            
        # Calculate final score
        self.state_manager.game_data.score = self.state_manager.game_data.words_completed
        
        # Save to high scores
        settings = self.state_manager.get_difficulty_settings()
        time_taken = settings['game_duration'] - self.state_manager.game_data.time_remaining
        self.high_scores.add_score(
            self.state_manager.game_data.nickname,
            self.state_manager.game_data.score,
            self.state_manager.game_data.words_completed,
            time_taken,
            self.state_manager.game_data.total_errors,
            self.state_manager.game_data.difficulty
        )
        
        self.state_manager.change_state(GameState.GAME_OVER)
    
    def start_practice_mode(self):
        """Start practice mode for single letter training."""
        print("Starting practice mode")
        
        # Reset megohmmeter needle before starting practice mode
        if self.megohmmeter:
            self.megohmmeter.force_reset()
        
        # Reset practice data
        self.state_manager.game_data.practice_completed = 0
        self.state_manager.game_data.practice_errors = 0
        self.current_sequence = ""
        self.last_timeout_check = time.time()
        
        # Generate first random letter BEFORE changing state
        self._generate_practice_letter()
        
        # Change to practice state AFTER letter is generated
        self.state_manager.change_state(GameState.PRACTICE)
    
    def _generate_practice_letter(self):
        """Generate a random letter for practice."""
        # Generate random uppercase letter A-Z
        self.state_manager.game_data.practice_letter = random.choice(string.ascii_uppercase)
        self.state_manager.game_data.practice_letter_color = "white"  # Reset color
        print(f"Practice letter: {self.state_manager.game_data.practice_letter}")
    
    def on_practice_key_press(self):
        """Handle Morse key press during practice."""
        if self.state_manager.current_state == GameState.PRACTICE:
            self.state_manager.cursor_visible = True
            self.state_manager.cursor_timer = time.time()
            # Move megohmmeter needle to maximum when key is pressed
            if self.megohmmeter:
                self.megohmmeter.key_pressed()
    
    def on_practice_key_release(self, press_duration: float):
        """Handle Morse key release during practice."""
        from .config import DEBOUNCE_TIME, DOT_DURATION, DASH_DURATION
        
        if self.state_manager.current_state != GameState.PRACTICE:
            return
        
        # Return megohmmeter needle to baseline when key is released
        if self.megohmmeter:
            self.megohmmeter.key_released()
            
        now = time.time()

        # Ignore debounce
        if press_duration < DEBOUNCE_TIME:
            return

        # Determine dot or dash and apply appropriate amplitude
        threshold = (DOT_DURATION + DASH_DURATION) / 2
        if press_duration < threshold:
            self.current_sequence += "."
            print("Practice: Added . (dot)")
            # Apply dot amplitude to megohmmeter
            if self.megohmmeter:
                self.megohmmeter.apply_dot()
        else:
            self.current_sequence += "-"
            print("Practice: Added - (dash)")
            # Apply dash amplitude to megohmmeter
            if self.megohmmeter:
                self.megohmmeter.apply_dash()

        print(f"Practice current sequence: {self.current_sequence}")

        # Update timers
        self.last_element_time = now
        self.state_manager.cursor_visible = True
        self.state_manager.cursor_timer = now
    
    def check_practice_morse_input(self):
        """Check if current Morse sequence matches the practice letter."""
        if not self.current_sequence or self.state_manager.current_state != GameState.PRACTICE:
            return
        
        # Try to decode the current sequence
        decoded_char = self.decoder.decode(self.current_sequence)
        
        # If decoding failed (unknown pattern), clear input and return
        if not decoded_char:
            print(f"Practice: Unknown pattern '{self.current_sequence}' - clearing input")
            self.current_sequence = ""
            return
        
        target_char = self.state_manager.game_data.practice_letter
        
        if decoded_char == target_char:
            # Correct letter found
            print(f"Practice correct! Found '{decoded_char}'")
            self.state_manager.game_data.practice_letter_color = "green"
            self.state_manager.game_data.practice_completed += 1
            
            # Schedule new letter generation after delay to show green color
            self.state_manager.game_data.practice_next_letter_time = time.time() + 0.75
        else:
            # Wrong letter
            print(f"Practice wrong! '{decoded_char}' doesn't match '{target_char}'")
            self.state_manager.game_data.practice_letter_color = "red"
            self.state_manager.game_data.practice_errors += 1
            self.state_manager.game_data.error_time = time.time()  # Set error time for glitch effect
        
        # Reset current sequence
        self.current_sequence = ""
    
    def clear_practice_input(self):
        """Clear current Morse input in practice mode."""
        if self.state_manager.current_state == GameState.PRACTICE:
            self.current_sequence = ""
            # Reset letter color to white if it was red
            if self.state_manager.game_data.practice_letter_color == "red":
                self.state_manager.game_data.practice_letter_color = "white"
    
    def check_practice_timeouts(self):
        """Check for timeouts in Morse code input during practice."""
        from .config import LETTER_GAP
        
        if self.state_manager.current_state != GameState.PRACTICE:
            return

        now = time.time()
        delta = now - getattr(self, 'last_timeout_check', now)
        self.last_timeout_check = now

        # Check for Morse character completion
        if self.current_sequence and self.last_element_time is not None:
            if now - self.last_element_time >= LETTER_GAP:
                self.check_practice_morse_input()
                self.last_element_time = now
        
        # Check if it's time to generate a new letter (after correct answer)
        if hasattr(self.state_manager.game_data, 'practice_next_letter_time'):
            if now >= self.state_manager.game_data.practice_next_letter_time:
                self._generate_practice_letter()
                delattr(self.state_manager.game_data, 'practice_next_letter_time')
