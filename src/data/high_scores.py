"""
High scores management for Morse Code Game
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

class HighScoreManager:
    """Manage high scores storage and retrieval with difficulty support."""
    
    def __init__(self, scores_file: str = None):
        if scores_file is None:
            base_dir = Path(__file__).parent
            scores_file = str(base_dir / 'high_scores.json')
        
        self.scores_file = scores_file
        self.scores: Dict[str, List[Dict[str, Any]]] = {'easy': [], 'hard': []}
        self.max_scores = None  # Save all scores, no limit
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.scores_file), exist_ok=True)
        
        self.load_scores()
    
    def load_scores(self):
        """Load high scores from file."""
        try:
            if os.path.exists(self.scores_file):
                with open(self.scores_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle backward compatibility
                    if isinstance(data, list):
                        # Old format - migrate to easy mode
                        self.scores = {'easy': data, 'hard': []}
                    elif isinstance(data, dict):
                        self.scores = data
                    else:
                        self.scores = {'easy': [], 'hard': []}
            else:
                self.scores = {'easy': [], 'hard': []}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading high scores: {e}")
            self.scores = {'easy': [], 'hard': []}
    
    def save_scores(self):
        """Save high scores to file."""
        try:
            with open(self.scores_file, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving high scores: {e}")
    
    def add_score(self, nickname: str, score: int, words_completed: int, time_taken: float, errors: int = 0, difficulty: str = 'easy'):
        """Add a new score to the high scores list."""
        if difficulty not in self.scores:
            difficulty = 'easy'
            
        score_entry = {
            'nickname': nickname,
            'score': score,
            'words_completed': words_completed,
            'time_taken': time_taken,
            'errors': errors,
            'difficulty': difficulty,
            'date': datetime.now().isoformat(),
            'timestamp': datetime.now().timestamp()
        }
        
        self.scores[difficulty].append(score_entry)
        # Sort by score, then by fewer errors (for tie-breaking), then by time taken
        self.scores[difficulty].sort(key=lambda x: (x['score'], -x['words_completed'], -x.get('errors', 0), x['time_taken']), reverse=True)
        
        # No limit on number of scores - save all attempts
        
        self.save_scores()
    
    def get_top_scores(self, difficulty: str = 'easy', limit: int = None) -> List[Dict[str, Any]]:
        """Get top scores for specific difficulty."""
        if difficulty not in self.scores:
            difficulty = 'easy'
        
        if limit is None:
            limit = len(self.scores[difficulty])
        return self.scores[difficulty][:limit]
    
    def is_high_score(self, score: int, difficulty: str = 'easy') -> bool:
        """Check if score qualifies for high scores in specific difficulty."""
        # Since we save all scores now, all scores qualify
        return True
    
    def is_nickname_available(self, nickname: str, difficulty: str = None) -> bool:
        """Check if nickname is available (not already used in high scores).
        
        Args:
            nickname: Nickname to check
            difficulty: If specified, check only in this difficulty; if None, check all difficulties
            
        Returns:
            True if nickname is available, False if already exists
        """
        nickname_lower = nickname.lower().strip()
        
        if difficulty is None:
            # Check all difficulties
            for diff_scores in self.scores.values():
                if any(score['nickname'].lower().strip() == nickname_lower for score in diff_scores):
                    return False
            return True
        else:
            # Check specific difficulty
            if difficulty not in self.scores:
                difficulty = 'easy'
            return not any(score['nickname'].lower().strip() == nickname_lower for score in self.scores[difficulty])
    
    def get_existing_nicknames(self, difficulty: str = None) -> List[str]:
        """Get list of existing nicknames.
        
        Args:
            difficulty: If specified, get nicknames from this difficulty only; if None, get all
            
        Returns:
            List of unique nicknames
        """
        if difficulty is None:
            # Get from all difficulties
            all_scores = []
            for diff_scores in self.scores.values():
                all_scores.extend(diff_scores)
            scores_to_check = all_scores
        else:
            if difficulty not in self.scores:
                difficulty = 'easy'
            scores_to_check = self.scores[difficulty]
        
        return list(set(score['nickname'] for score in scores_to_check))

    def get_player_best_score(self, nickname: str, difficulty: str = 'easy') -> Dict[str, Any]:
        """Get best score for a specific player in specific difficulty."""
        if difficulty not in self.scores:
            difficulty = 'easy'
            
        player_scores = [s for s in self.scores[difficulty] if s['nickname'].lower() == nickname.lower()]
        if not player_scores:
            return None
        
        return max(player_scores, key=lambda x: (x['score'], -x['words_completed'], -x.get('errors', 0)))
    
    def clear_scores(self, difficulty: str = None):
        """Clear high scores for specific difficulty or all difficulties."""
        if difficulty is None:
            self.scores = {'easy': [], 'hard': []}
        elif difficulty in self.scores:
            self.scores[difficulty] = []
        
        self.save_scores()
    
    def get_stats(self, difficulty: str = None) -> Dict[str, Any]:
        """Get statistics about high scores for specific difficulty or all."""
        if difficulty is None:
            # Combined stats for all difficulties
            all_scores = []
            for diff_scores in self.scores.values():
                all_scores.extend(diff_scores)
            scores_to_analyze = all_scores
        else:
            if difficulty not in self.scores:
                difficulty = 'easy'
            scores_to_analyze = self.scores[difficulty]
        
        if not scores_to_analyze:
            return {
                'total_games': 0,
                'unique_players': 0,
                'highest_score': 0,
                'average_score': 0,
                'total_words': 0
            }
        
        total_games = len(scores_to_analyze)
        unique_players = len(set(s['nickname'] for s in scores_to_analyze))
        highest_score = max(s['score'] for s in scores_to_analyze)
        average_score = sum(s['score'] for s in scores_to_analyze) / total_games
        total_words = sum(s['words_completed'] for s in scores_to_analyze)
        
        return {
            'total_games': total_games,
            'unique_players': unique_players,
            'highest_score': highest_score,
            'average_score': round(average_score, 1),
            'total_words': total_words
        }
    
    def get_rank(self, score: int, words_completed: int, errors: int, difficulty: str = 'easy') -> int:
        """Get rank position for a score in specific difficulty.
        
        Args:
            score: Score to check
            words_completed: Number of words completed
            errors: Number of errors
            difficulty: Difficulty level
            
        Returns:
            Rank position (1-based), or 0 if no scores exist
        """
        if difficulty not in self.scores:
            difficulty = 'easy'
        
        if not self.scores[difficulty]:
            return 1  # First score would be rank 1
        
        # Count how many existing scores are better than this score
        # Better means: higher score, or same score with more words completed, 
        # or same score and words with fewer errors
        better_scores = 0
        for existing_score in self.scores[difficulty]:
            if (existing_score['score'] > score or
                (existing_score['score'] == score and existing_score['words_completed'] > words_completed) or
                (existing_score['score'] == score and existing_score['words_completed'] == words_completed and existing_score.get('errors', 0) < errors)):
                better_scores += 1
        
        return better_scores + 1  # Rank is 1-based
