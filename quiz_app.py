import json
import random
import os
import sys
import re

VOCAB_FILE = 'C:/Dev/ChinesePracticeApp/vocabulary.json'
PROGRESS_FILE = 'C:/Dev/ChinesePracticeApp/progress.json'

def load_data():
    with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
        vocab = json.load(f)
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    else:
        progress = {"missed": [], "corrections": {}, "stats": {}}
    if "stats" not in progress: progress["stats"] = {}
    return vocab, progress

def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def normalize_input(s):
    return s.strip().lower()

def normalize_pinyin(s):
    # Remove all spaces for pinyin comparison
    return re.sub(r'\s+', '', s.strip().lower())

def show_stats(progress, vocab):
    print("\n--- Vocabulary Performance Stats ---")
    stats = progress.get("stats", {})
    if not stats:
        print("No data yet.")
        return
    
    sorted_stats = []
    for char, data in stats.items():
        right = data.get("right", 0)
        wrong = data.get("wrong", 0)
        total = right + wrong
        ratio = (right / total * 100) if total > 0 else 0
        sorted_stats.append((char, right, wrong, ratio))
    
    # Worst 10
    sorted_stats.sort(key=lambda x: x[3])
    print(f"\nTop 10 Problem Words (Lowest Accuracy):")
    print(f"{'Char':<5} | {'Right':<6} | {'Wrong':<6} | {'Accuracy':<8}")
    print("-" * 35)
    for char, r, w, acc in sorted_stats[:10]:
        print(f"{char:<5} | {r:<6} | {w:<6} | {acc:>7.1f}%")
    
    # Best 10
    print(f"\nTop 10 Mastered Words (Highest Accuracy):")
    print(f"{'Char':<5} | {'Right':<6} | {'Wrong':<6} | {'Accuracy':<8}")
    print("-" * 35)
    for char, r, w, acc in sorted_stats[-10:][::-1]:
        print(f"{char:<5} | {r:<6} | {w:<6} | {acc:>7.1f}%")
    print("-" * 35)

def handle_input(prompt, progress, vocab, is_pinyin=False):
    user_input = input(prompt)
    norm = normalize_input(user_input)
    
    if norm == '!exit':
        save_progress(progress)
        print("Progress saved. Goodbye!")
        sys.exit()
    elif norm == '!stats':
        show_stats(progress, vocab)
        return handle_input(prompt, progress, vocab, is_pinyin)
    
    return normalize_pinyin(user_input) if is_pinyin else norm

def update_stats(char, is_correct, progress):
    if char not in progress["stats"]:
        progress["stats"][char] = {"right": 0, "wrong": 0}
    if is_correct:
        progress["stats"][char]["right"] += 1
    else:
        progress["stats"][char]["wrong"] += 1
    save_progress(progress)

def run_quiz():
    vocab, progress = load_data()
    # Sort all characters by frequency_index
    all_chars = sorted(vocab.keys(), key=lambda x: vocab[x].get('frequency_index', 9999))
    
    current_missed = []
    print("--- Chinese Vocabulary Quiz ---")
    print("Commands: '!exit' to quit, '!stats' to see performance.")
    
    session_correct = 0
    session_total = 0
    
    for char in all_chars:
        if len(current_missed) >= 5:
            print("\n!!! Mistake threshold reached. Entering Drill Mode !!!")
            drill_words(current_missed, vocab, progress)
            current_missed = []
            print("\n--- Resuming Main List ---")
        
        data = vocab[char]
        valid_pinyins = set(data['pinyin'])
        valid_english = set(data['english'])
        if char in progress['corrections']:
            valid_pinyins.update(progress['corrections'][char].get('pinyin', []))
            valid_english.update(progress['corrections'][char].get('english', []))
        
        print(f"\nCharacter: {char}")
        pinyin_input = handle_input("Pinyin: ", progress, vocab, is_pinyin=True)
        eng_input = handle_input("English: ", progress, vocab)
        
        session_total += 1
        p_correct = pinyin_input in valid_pinyins
        e_correct = eng_input in valid_english
        
        if p_correct and e_correct:
            print("Correct!")
            session_correct += 1
            update_stats(char, True, progress)
        else:
            print(f"Incorrect. Expected: {', '.join(valid_pinyins)} | {', '.join(valid_english)}")
            correction = input("Were you actually correct? (y/n): ").lower()
            if correction == 'y':
                print("Adding to valid answers.")
                if char not in progress['corrections']:
                    progress['corrections'][char] = {"pinyin": [], "english": []}
                if not p_correct: progress['corrections'][char]["pinyin"].append(pinyin_input)
                if not e_correct: progress['corrections'][char]["english"].append(eng_input)
                session_correct += 1
                update_stats(char, True, progress)
            else:
                update_stats(char, False, progress)
                current_missed.append(char)
                if char not in progress['missed']:
                    progress['missed'].append(char)
                save_progress(progress)
    
    print(f"\nSession Complete! Score: {session_correct}/{session_total}")
    show_stats(progress, vocab)

def drill_words(words, vocab, progress):
    to_drill = list(words)
    random.shuffle(to_drill)
    while to_drill:
        char = to_drill.pop(0)
        data = vocab[char]
        valid_pinyins = set(data['pinyin'])
        valid_english = set(data['english'])
        if char in progress['corrections']:
            valid_pinyins.update(progress['corrections'][char].get('pinyin', []))
            valid_english.update(progress['corrections'][char].get('english', []))
            
        print(f"\nDRILL - Character: {char}")
        pinyin_input = handle_input("Pinyin: ", progress, vocab, is_pinyin=True)
        eng_input = handle_input("English: ", progress, vocab)
        
        p_correct = pinyin_input in valid_pinyins
        e_correct = eng_input in valid_english
        
        if p_correct and e_correct:
            print("Correct! Removed from drill.")
            update_stats(char, True, progress)
        else:
            print(f"Incorrect. Expected: {', '.join(valid_pinyins)} | {', '.join(valid_english)}")
            correction = input("Were you actually correct? (y/n): ").lower()
            if correction == 'y':
                print("Adding to valid answers.")
                if char not in progress['corrections']:
                    progress['corrections'][char] = {"pinyin": [], "english": []}
                if not p_correct: progress['corrections'][char]["pinyin"].append(pinyin_input)
                if not e_correct: progress['corrections'][char]["english"].append(eng_input)
                update_stats(char, True, progress)
            else:
                update_stats(char, False, progress)
                to_drill.append(char)
                random.shuffle(to_drill)

if __name__ == "__main__":
    run_quiz()
