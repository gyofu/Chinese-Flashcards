import React, { useState, useEffect, useMemo } from 'react';
import './App.css';
import vocabData from './data/vocabulary.json';

// --- TYPES ---

interface Word {
  char: string;
  pinyin: string[];
  english: string[];
  frequency_index: number;
  category?: string;
}

interface Stats {
  right: number;
  wrong: number;
}

interface Progress {
  missed: string[];
  corrections: Record<string, { pinyin: string[]; english: string[] }>;
  stats: Record<string, Stats>;
}

const DEFAULT_PROGRESS: Progress = {
  missed: [],
  corrections: {},
  stats: {}
};

interface QuizResult {
  isCorrect: boolean;
  message: string;
  userPinyin: string;
  userEnglish: string;
}

type SortKey = 'pinyin' | 'total' | 'acc';
type SortDirection = 'asc' | 'desc';

function App() {
  // --- STATE ---
  const [sessionStarted, setSessionStarted] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>(['computing', 'business', 'common']);
  const [words, setWords] = useState<Word[]>([]);
  const [progress, setProgress] = useState<Progress>(DEFAULT_PROGRESS);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [pinyinInput, setPinyinInput] = useState('');
  const [englishInput, setEnglishInput] = useState('');
  const [isFlipped, setIsFlipped] = useState(false);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [drillMode, setDrillMode] = useState<string[]>([]);
  const [isDrilling, setIsDrilling] = useState(false);
  const [activeWord, setActiveWord] = useState<Word | null>(null);

  // Sorting state for the sidebar
  const [sortKey, setSortKey] = useState<SortKey>('acc');
  const [sortDir, setSortDir] = useState<SortDirection>('asc');

  // --- LIFECYCLE ---
  useEffect(() => {
    // Load progress from localStorage once
    const savedProgress = localStorage.getItem('chinese_practice_progress');
    if (savedProgress) {
      try {
        setProgress(JSON.parse(savedProgress));
      } catch (e) {
        console.error("Failed to parse saved progress", e);
        setProgress(DEFAULT_PROGRESS);
      }
    }
  }, []);

  const shuffleArray = (array: any[]) => {
    const newArr = [...array];
    for (let i = newArr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [newArr[i], newArr[j]] = [newArr[j], newArr[i]];
    }
    return newArr;
  };

  const startSession = () => {
    const allWords = Object.values(vocabData as Record<string, Word>);
    const filtered = allWords.filter(w => w.category && selectedCategories.includes(w.category));
    
    if (filtered.length === 0) {
      alert("Please select at least one category with words.");
      return;
    }

    const shuffled = shuffleArray(filtered);
    setWords(shuffled);
    setActiveWord(shuffled[0]);
    setSessionStarted(true);
    setCurrentIndex(0);
    setDrillMode([]);
    setIsDrilling(false);
  };

  const toggleCategory = (cat: string) => {
    setSelectedCategories(prev => 
      prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]
    );
  };

  const normalizePinyin = (s: string) => s.toLowerCase().replace(/\s+/g, '');
  const normalizeText = (s: string) => s.toLowerCase().trim();

  useEffect(() => {
    if (sessionStarted && !isFlipped && words.length > 0) {
      const next = isDrilling 
        ? words.find(w => w.char === drillMode[0])
        : words[currentIndex];
      setActiveWord(next || words[0]);
    }
  }, [currentIndex, isDrilling, drillMode, isFlipped, words, sessionStarted]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isFlipped || !activeWord) return;

    const validPinyins = new Set([...activeWord.pinyin, ...(progress?.corrections[activeWord.char]?.pinyin || [])]);
    const validEnglish = new Set([...activeWord.english, ...(progress?.corrections[activeWord.char]?.english || [])]);

    const pCorrect = validPinyins.has(normalizePinyin(pinyinInput));
    const eCorrect = [...validEnglish].some(val => normalizeText(englishInput) === normalizeText(val));

    const isCorrect = pCorrect && eCorrect;
    
    setResult({
      isCorrect,
      message: isCorrect ? 'Correct!' : 'Incorrect.',
      userPinyin: pinyinInput,
      userEnglish: englishInput
    });
    setIsFlipped(true);

    if (!isCorrect) {
      updateProgress(activeWord.char, false);
      if (!drillMode.includes(activeWord.char)) {
          const newDrill = [...drillMode, activeWord.char];
          setDrillMode(newDrill);
      }
    } else {
      updateProgress(activeWord.char, true);
    }
  };

  const updateProgress = (char: string, isCorrect: boolean, isManual: boolean = false) => {
    setProgress(prev => {
      const newProgress = { ...prev };
      
      if (!newProgress.stats[char]) {
        newProgress.stats[char] = { right: 0, wrong: 0 };
      }

      if (isCorrect) {
        newProgress.stats[char].right += 1;
      } else {
        newProgress.stats[char].wrong += 1;
        if (!newProgress.missed.includes(char)) {
          newProgress.missed.push(char);
        }
      }

      localStorage.setItem('chinese_practice_progress', JSON.stringify(newProgress));
      return newProgress;
    });
  };

  const nextWord = () => {
    if (!result || !activeWord) return;
    const wasCorrect = result.isCorrect;
    setIsFlipped(false);
    setResult(null);
    setPinyinInput('');
    setEnglishInput('');

    if (isDrilling) {
        if (wasCorrect) {
            const newDrill = drillMode.slice(1);
            setDrillMode(newDrill);
            if (newDrill.length === 0) setIsDrilling(false);
        } else {
            setDrillMode(prev => [...prev.slice(1), prev[0]]);
        }
    } else {
        if (drillMode.length >= 5) {
            setIsDrilling(true);
        } else {
            setCurrentIndex((prev) => (prev + 1) % words.length);
        }
    }
  };

  const handleManualCorrect = () => {
    if (!activeWord) return;
    setResult(prev => prev ? { ...prev, isCorrect: true, message: 'Corrected! (Typo ignored)' } : null);
    updateProgress(activeWord.char, true, true);
    if (drillMode.includes(activeWord.char)) {
        setDrillMode(prev => prev.filter(c => c !== activeWord.char));
    }
  };

  const handleReset = () => {
    if (window.confirm("Are you sure you want to reset all progress? This cannot be undone.")) {
      localStorage.removeItem('chinese_practice_progress');
      setProgress(DEFAULT_PROGRESS);
      window.location.reload();
    }
  };

  // --- SORTING LOGIC ---

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const statsList = useMemo(() => {
    if (!progress || !progress.stats) return [];

    const charToPinyin = Object.values(vocabData as Record<string, Word>).reduce((acc, w) => {
      acc[w.char] = w.pinyin[0];
      return acc;
    }, {} as Record<string, string>);

    const list = Object.entries(progress.stats).map(([char, s]) => {
      const total = s.right + s.wrong;
      return {
        char,
        right: s.right,
        wrong: s.wrong,
        total,
        acc: (s.right / total * 100) || 0,
        pinyin: charToPinyin[char] || ''
      };
    });

    list.sort((a, b) => {
      let valA: any = a[sortKey];
      let valB: any = b[sortKey];

      if (typeof valA === 'string') {
        return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortDir === 'asc' ? valA - valB : valB - valA;
    });

    return list;
  }, [progress, sortKey, sortDir]);

  if (!sessionStarted) {
    return (
      <div className="start-screen">
        <h1>Chinese Practice</h1>
        <p>Select your study focus:</p>
        <div className="category-selection">
          <label>
            <input 
              type="checkbox" 
              checked={selectedCategories.includes('computing')} 
              onChange={() => toggleCategory('computing')} 
            />
            Computing & Internet
          </label>
          <label>
            <input 
              type="checkbox" 
              checked={selectedCategories.includes('business')} 
              onChange={() => toggleCategory('business')} 
            />
            Business & Corporate
          </label>
          <label>
            <input 
              type="checkbox" 
              checked={selectedCategories.includes('common')} 
              onChange={() => toggleCategory('common')} 
            />
            Common 500
          </label>
        </div>
        <button className="start-btn" onClick={startSession}>Start Session</button>
        
        {statsList.length > 0 && (
          <div className="start-stats">
            <h3>Overall Progress: {statsList.length} words encountered</h3>
            <button onClick={handleReset} className="reset-btn-small">Reset Progress</button>
          </div>
        )}
      </div>
    );
  }

  if (words.length === 0) return <div className="loading">Loading Vocabulary...</div>;

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="sidebar-header">
            <h3>Stats</h3>
            <button onClick={() => setSessionStarted(false)} className="quit-btn" style={{ background: '#3498db' }}>Menu</button>
        </div>
        
        <div className="stats-header">
          <button className={`sort-label ${sortKey === 'pinyin' ? 'active' : ''}`} onClick={() => handleSort('pinyin')}>
            Char {sortKey === 'pinyin' && (sortDir === 'asc' ? '↑' : '↓')}
          </button>
          <button className={`sort-label ${sortKey === 'total' ? 'active' : ''}`} onClick={() => handleSort('total')}>
            # {sortKey === 'total' && (sortDir === 'asc' ? '↑' : '↓')}
          </button>
          <button className={`sort-label ${sortKey === 'acc' ? 'active' : ''}`} onClick={() => handleSort('acc')}>
            Acc {sortKey === 'acc' && (sortDir === 'asc' ? '↑' : '↓')}
          </button>
        </div>

        <div className="stats-scroll">
          {statsList.map(s => (
            <div key={s.char} className="stat-item">
              <span className="stat-char" title={s.pinyin}>{s.char}</span>
              <span className="stat-total">{s.total}</span>
              <span className="stat-acc">{s.acc.toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>

      <main className="quiz-area">
        {isDrilling && <div className="drill-banner">DRILL MODE: {drillMode.length} left</div>}
        {!isDrilling && drillMode.length > 0 && <div className="pending-banner">Mistakes: {drillMode.length}/5 before drill loop</div>}
        
        <div className={`flashcard ${isFlipped ? 'flipped' : ''}`}>
          <div className="card-front">
            <div className="card-category">{activeWord?.category?.toUpperCase()}</div>
            <h1>{activeWord?.char}</h1>
          </div>
          
          <div className="card-back">
            <h2>{activeWord?.char}</h2>
            
            <div className="comparison-grid">
              <div className="comp-header">Field</div>
              <div className="comp-header">Your Answer</div>
              <div className="comp-header">Expected</div>
              
              <div className="comp-label">Pinyin</div>
              <div className={`comp-val ${normalizePinyin(result?.userPinyin || '') === normalizePinyin(activeWord?.pinyin[0] || '') ? 'text-correct' : 'text-incorrect'}`}>
                {result?.userPinyin || '(empty)'}
              </div>
              <div className="comp-val">{activeWord?.pinyin.join(', ')}</div>

              <div className="comp-label">English</div>
              <div className="comp-val">
                {result?.userEnglish || '(empty)'}
              </div>
              <div className="comp-val">{activeWord?.english.join(', ')}</div>
            </div>

            <div className={`result-msg ${result?.isCorrect ? 'correct' : 'incorrect'}`}>
              {result?.message}
            </div>

            <div className="card-controls">
                {!result?.isCorrect && result !== null && (
                    <button onClick={handleManualCorrect} className="manual-correct">I was actually correct</button>
                )}
                <button onClick={nextWord} className="next-btn">Next Word</button>
            </div>
          </div>
        </div>

        {!isFlipped && (
          <form onSubmit={handleSubmit} className="input-area">
            <input 
              type="text" 
              placeholder="Pinyin" 
              value={pinyinInput} 
              onChange={(e) => setPinyinInput(e.target.value)}
              autoFocus
              autoComplete="off"
            />
            <input 
              type="text" 
              placeholder="English" 
              value={englishInput} 
              onChange={(e) => setEnglishInput(e.target.value)}
              autoComplete="off"
            />
            <button type="submit">Submit</button>
          </form>
        )}
      </main>
    </div>
  );
}

export default App;
