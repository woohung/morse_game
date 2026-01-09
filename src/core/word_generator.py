"""
Word generator for Morse Code Game
Network technology themed words with difficulty-based word selection
"""
import random
from typing import List

class WordGenerator:
    """Generate network technology themed words for the game."""
    
    def __init__(self):
        # Easy mode words (max 4 letters, simpler terms)
        self.easy_words = [
            # Basic network terms
            "WIFI", "LAN", "WAN", "VPN", "DNS", "FTP", "HTTP", "TCP",
            "UDP", "IP", "MAC", "PING", "PORT", "HOST", "NODE", "LINK",
            "DATA", "PACK", "BYTE", "BITS", "MODE", "SYNC", "AUTH",
            "KEY", "API", "WEB", "MAIL", "CHAT", "CALL", "SAFE", "LOCK",
            "PASS", "USER", "ROOT", "LOAD", "FAST", "SLOW", "HIGH",
            "LOW", "SPEED", "LOSS", "ERROR", "FAIL", "SYNC", "CACHE",
            "DISK", "SIZE", "FREE", "USED", "HELP", "INFO", "NOTE",
            "WARN", "OK", "YES", "NO", "NEW", "OLD", "HOT", "ON", "OFF",
            
            # Hardware terms
            "ROUT", "HUB", "FIRE", "WALL", "GATE", "MODEM", "WIRE",
            "CABLE", "CHIP", "CARD", "SLOT", "RACK", "CASE", "FAN", "LED",
            
            # Protocol terms
            "SSH", "TEL", "RDP", "VNC", "SFTP", "LIVE", "REAL", "TIME",
            
            # Security terms
            "WORD", "ADMIN", "GUEST", "LOGIN", "SIGN", "OUT", "EXIT",
            "ENTER", "BLOCK", "ALLOW", "PERM", "ROLE", "GROUP", "TEAM",
            "WORK",
            
            # Common abbreviations
            "AI", "ML", "IoT", "AR", "VR", "UX", "UI", "QA", "CI",
            "CD", "DEV", "OPS", "IT", "HR", "CEO", "CTO", "CFO",
            "FAQ", "START", "STOP", "RUN", "END", "QUIT"
        ]
        
        # Hard mode words (up to 6 letters, more complex IT terms)
        self.hard_words = [
            # Network protocols (5-6 letters)
            "HTTPS", "SMTP", "POP3", "IMAP", "SOAP", "JSON", "XML",
            "CODE", "TEST", "DEMO", "SWITCH", "BRIDGE", "MODEM",
            "RADIO", "FIBER", "COPPER", "MOUSE", "SCREEN", "TOUCH",
            
            # DevOps/Cloud terms (5-6 letters)
            "DOCKER", "KUBE", "NODE", "POD", "CLUST", "SCALE",
            "BALANCE", "HEALTH", "CHECK", "MONITOR", "LOG", "TRACE",
            "DEBUG", "BUILD", "DEPLOY", "PUSH", "PULL", "MERGE",
            "BRANCH", "TAG", "RELEASE", "PATCH", "UPDATE",
            "UPGRADE", "MIGRATE",
            
            # Performance terms (5-6 letters)
            "SPEED", "LATENCY", "DELAY", "JITTER", "RETRY", "BACKUP",
            "RESTORE", "MEMORY", "SPACE", "TOTAL",
            
            # Network types (5-6 letters)
            "BLUETOOTH", "SIGNAL", "WAVE", "SATELLITE",
            
            # Security terms (5-6 letters)
            "TOKEN", "HASH", "CERT", "CLOUD", "EDGE", "CORE", "BACK",
            "FRONT", "ACCESS", "REMOVE", "CREATE", "DELETE", "MODIFY",
            
            # Technical terms (5-6 letters)
            "SERVER", "CLIENT", "SYSTEM", "NETWORK", "DATABASE",
            "SCRIPT", "CONFIG", "STATUS", "ACTIVE", "PASSIVE",
            "STATIC", "DYNAMIC", "PUBLIC", "PRIVATE", "VIRTUAL",
            "PHYSICAL", "DIGITAL", "ANALOG", "BINARY", "DECIMAL",
            "HEXADEC", "FORMAT", "ENCRYPT", "DECRYPT", "COMPRESS",
            "EXPAND", "IMPORT", "EXPORT", "STREAM", "DOWNLOAD",
            "UPLOAD", "ONLINE", "OFFLINE", "REMOTE", "LOCAL",
            "GLOBAL", "REGION", "ZONE", "CLUSTER", "WORKER",
            "MASTER", "SLAVE", "PRIMARY", "SECOND", "TERTIARY"
        ]
        
        # Filter hard words to max 6 letters
        self.hard_words = [word for word in self.hard_words if len(word) <= 6]
        
        # Filter easy words to max 4 letters
        self.easy_words = [word for word in self.easy_words if len(word) <= 4]
        
        self.used_words = []  # Track used words in current session
        self.current_difficulty = "easy"
    
    def set_difficulty(self, difficulty: str):
        """Set difficulty level for word generation."""
        if difficulty in ['easy', 'hard']:
            self.current_difficulty = difficulty
            self.used_words = []  # Reset used words when difficulty changes
    
    def get_random_word(self) -> str:
        """Get a random word based on current difficulty that hasn't been used recently."""
        # Select word list based on difficulty
        word_list = self.easy_words if self.current_difficulty == "easy" else self.hard_words
        
        available_words = [word for word in word_list if word not in self.used_words]
        
        # If all words have been used, reset the used list
        if not available_words:
            self.used_words = []
            available_words = word_list.copy()
        
        word = random.choice(available_words).upper()
        self.used_words.append(word)
        
        # Keep used words list manageable
        if len(self.used_words) > 20:
            self.used_words = self.used_words[-10:]
        
        return word
    
    def reset(self):
        """Reset the word generator for a new game."""
        self.used_words = []
    
    def get_word_count(self) -> int:
        """Get total number of available words for current difficulty."""
        word_list = self.easy_words if self.current_difficulty == "easy" else self.hard_words
        return len(word_list)
