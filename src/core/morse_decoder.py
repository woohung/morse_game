"""
Morse code decoder module.
Converts between Morse code and text.
"""

# Dictionary representing the Morse code chart
MORSE_CODE_DICT = { 'A':'.-', 'B':'-...',
                    'C':'-.-.', 'D':'-..', 'E':'.',
                    'F':'..-.', 'G':'--.', 'H':'....',
                    'I':'..', 'J':'.---', 'K':'-.-',
                    'L':'.-..', 'M':'--', 'N':'-.',
                    'O':'---', 'P':'.--.', 'Q':'--.-',
                    'R':'.-.', 'S':'...', 'T':'-',
                    'U':'..-', 'V':'...-', 'W':'.--',
                    'X':'-..-', 'Y':'-.--', 'Z':'--..',
                    '1':'.----', '2':'..---', '3':'...--',
                    '4':'....-', '5':'.....', '6':'-....',
                    '7':'--...', '8':'---..', '9':'----.',
                    '0':'-----', ', ':'--..--', '.':'.-.-.-',
                    '?':'..--..', '/':'-..-.', '-':'-....-',
                    '(':'-.--.', ')':'-.--.-'}

# Reverse dictionary for decoding
REVERSE_MORSE_CODE_DICT = {v:k for k,v in MORSE_CODE_DICT.items()}

class MorseDecoder:
    """Handles encoding and decoding of Morse code."""
    
    def __init__(self):
        self.buffer = ''  # Keep buffer for backward compatibility
    
    def reset(self):
        """Reset the decoder state."""
        self.buffer = ''
    
    def _validate_morse_char(self, morse_char: str) -> bool:
        """
        Validate if a Morse code character contains only dots and dashes.
        
        Args:
            morse_char: Morse code character to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not morse_char:
            return False
        return all(c in '.-' for c in morse_char)
    
    def _validate_text_char(self, char: str) -> bool:
        """
        Validate if a character can be encoded to Morse.
        
        Args:
            char: Character to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not char:
            return False
        return char.upper() in MORSE_CODE_DICT or char == ' '
    
    def decode(self, code: str) -> str:
        """
        Convert Morse code to a character.

        Args:
            code: Morse code string (e.g., '...' for 'S')

        Returns:
            Decoded character or empty string if not found
        """
        try:
            if not code:
                return ''
            
            # Validate Morse code format
            if not self._validate_morse_char(code):
                print(f"Warning: Invalid Morse code format: '{code}'")
                return ''
            
            # Use the reverse dictionary to decode
            result = REVERSE_MORSE_CODE_DICT.get(code, '')
            if not result:
                print(f"Warning: Unknown Morse code pattern: '{code}'")
            
            return result
                
        except Exception as e:
            print(f"Error decoding Morse code: {e}")
            return ''
    
    def decode_message(self, morse_message: str) -> str:
        """
        Convert a full Morse code message to text.
        
        Args:
            morse_message: Complete Morse code message with spaces between characters
                          and double spaces between words
        
        Returns:
            Decoded text message
        """
        try:
            if not morse_message:
                return ''
            
            # Add space at the end to handle last character
            morse_message += ' '
            
            decipher = ''
            citext = ''
            space_count = 0
            
            for letter in morse_message:
                if letter != ' ':
                    # Reset space counter when we get a non-space character
                    space_count = 0
                    citext += letter
                else:
                    # We encountered a space
                    space_count += 1
                    
                    if space_count == 2:
                        # Double space means word separation
                        decipher += ' '
                    elif citext:
                        # Single space means character separation
                        decoded_char = REVERSE_MORSE_CODE_DICT.get(citext, '')
                        decipher += decoded_char
                        citext = ''
            
            return decipher.strip()
            
        except Exception as e:
            print(f"Error decoding Morse message: {e}")
            return ''

    def encode(self, text: str) -> str:
        """
        Convert text to Morse code.
        
        Args:
            text: Text to encode (single character or word)
            
        Returns:
            Morse code string
        """
        try:
            morse_code = []
            for char in text.upper():
                if char in MORSE_CODE_DICT:
                    morse_code.append(MORSE_CODE_DICT[char])
                elif char == ' ':
                    morse_code.append('/')  # Space between words
                else:
                    print(f"Warning: Cannot encode character: '{char}'")
            return ' '.join(morse_code)
        except Exception as e:
            print(f"Error encoding text to Morse: {e}")
            return ''
    
    def encode_message(self, text: str) -> str:
        """
        Convert full text message to Morse code with proper spacing.
        
        Args:
            text: Complete text message to encode
            
        Returns:
            Complete Morse code message with single spaces between characters
            and double spaces between words
        """
        try:
            if not text:
                return ''
            
            morse_code = []
            words = text.upper().split(' ')
            
            for i, word in enumerate(words):
                for char in word:
                    if char in MORSE_CODE_DICT:
                        morse_code.append(MORSE_CODE_DICT[char])
                        morse_code.append(' ')  # Space between characters
                    else:
                        print(f"Warning: Cannot encode character: '{char}'")
                
                # Add double space between words (except after last word)
                if i < len(words) - 1:
                    morse_code.append(' ')  # Extra space for word separation
            
            return ''.join(morse_code).strip()
            
        except Exception as e:
            print(f"Error encoding text message to Morse: {e}")
            return ''

# Example usage
if __name__ == "__main__":
    decoder = MorseDecoder()
    
    # Test single character decoding
    print("Single character tests:")
    print(f"... -> {decoder.decode('...')}")  # Should print "S"
    print(f"- -> {decoder.decode('-')}")   # Should print "T"
    print(f".- -> {decoder.decode('.-')}")  # Should print "A"
    
    # Test full message encoding and decoding
    print("\nFull message tests:")
    test_message = "SOS HELP"
    encoded = decoder.encode_message(test_message)
    print(f"'{test_message}' -> '{encoded}'")
    
    decoded = decoder.decode_message(encoded)
    print(f"'{encoded}' -> '{decoded}'")
    
    # Test with multiple words
    print("\nMultiple words test:")
    test_message2 = "HELLO WORLD"
    encoded2 = decoder.encode_message(test_message2)
    print(f"'{test_message2}' -> '{encoded2}'")
    
    decoded2 = decoder.decode_message(encoded2)
    print(f"'{encoded2}' -> '{decoded2}'")