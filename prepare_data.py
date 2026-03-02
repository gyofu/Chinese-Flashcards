import csv
import json
import re
import os

# --- CONFIGURATION & MAPPING ---

TONE_MAP = {
    'ā': ('a', '1'), 'á': ('a', '2'), 'ǎ': ('a', '3'), 'à': ('a', '4'),
    'ē': ('e', '1'), 'é': ('e', '2'), 'ě': ('e', '3'), 'è': ('e', '4'),
    'ī': ('i', '1'), 'í': ('i', '2'), 'ǐ': ('i', '3'), 'ì': ('i', '4'),
    'ō': ('o', '1'), 'ó': ('o', '2'), 'ǒ': ('o', '3'), 'ò': ('o', '4'),
    'ū': ('u', '1'), 'ú': ('u', '2'), 'ǔ': ('u', '3'), 'ù': ('u', '4'),
    'ü': ('v', '1'), 'ǘ': ('v', '2'), 'ǚ': ('v', '3'), 'ǜ': ('v', '4'),
}

# --- HELPERS ---

def pinyin_to_clean(pinyin_str):
    words = pinyin_str.lower().split()
    result_words = []
    for word in words:
        clean_word = ""
        for char in word:
            if char in TONE_MAP:
                clean_word += TONE_MAP[char][0]
            elif char.isalpha():
                clean_word += char
        result_words.append(clean_word)
    return "".join(result_words)

def clean_text(text):
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip().lower()

# --- PARSING LOGIC ---

def process_csv(file_path, category, start_index=0):
    vocabulary = {}
    idx = start_index
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found. Skipping.")
        return vocabulary, idx

    with open(file_path, mode='r', encoding='utf-8') as f:
        for line in f:
            if ',' not in line or '/' not in line:
                continue
            
            char, rest = line.strip().split(',', 1)
            pinyin_raw, english_raw = rest.split('/', 1)
            
            pinyin_clean = pinyin_to_clean(pinyin_raw)
            english_list = [clean_text(e) for e in english_raw.split('/')]
            english_list = [e for e in english_list if e]
            
            vocabulary[char] = {
                "pinyin": [pinyin_clean],
                "english": english_list,
                "char": char,
                "frequency_index": idx,
                "category": category
            }
            idx += 1
    return vocabulary, idx

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    # Process Computing Terms
    vocab_computing, next_idx = process_csv('C:/Dev/ChinesePracticeApp/computing_terms.csv', 'computing', 0)
    
    # Process Business Terms
    vocab_business, next_idx = process_csv('C:/Dev/ChinesePracticeApp/business_terms.csv', 'business', next_idx)
    
    # Process Common 500 Terms
    vocab_common, next_idx = process_csv('C:/Dev/ChinesePracticeApp/common_500.csv', 'common', next_idx)
    
    # Merge for a master list
    final_vocab = {**vocab_computing, **vocab_business, **vocab_common}
    
    output_path = 'C:/Dev/ChinesePracticeApp/frontend/src/data/vocabulary.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_vocab, f, ensure_ascii=False, indent=2)
        
    print(f"Success! Processed {len(vocab_computing)} computing, {len(vocab_business)} business, and {len(vocab_common)} common terms.")
