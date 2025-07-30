import string

def count_vowels(text):
    return sum(1 for char in text.lower() if char in 'aeiou')

def is_palindrome(text):
    cleaned = ''.join(char.lower() for char in text if char.isalnum())
    return cleaned == cleaned[::-1]

def remove_punctuation(text):
    return ''.join(c for c in text if c not in string.punctuation)

def word_frequency(text):
    words = text.lower().split()
    return {word: words.count(word) for word in set(words)}

def capitalize_words(text):
    return ' '.join(word.capitalize() for word in text.split())
