import React, { useState, useRef, useEffect } from 'react';
import { Search, Loader2, X, Sparkles } from 'lucide-react';
import { useNLQuery } from '@/hooks/useQuery';
import { useQueryStore } from '@/stores/queryStore';
import styles from './TopQueryBar.module.css';

export default function TopQueryBar() {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const { submitQuery, isLoading } = useNLQuery();
  const { queryHistory, parsedQuery, queryError } = useQueryStore();
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    await submitQuery(inputValue.trim());
    setShowSuggestions(false);
  };

  const handleClear = () => {
    setInputValue('');
    inputRef.current?.focus();
  };

  const selectFromHistory = (query: string) => {
    setInputValue(query);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  // Keyboard shortcut: Ctrl/Cmd + K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className={styles.container}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.inputWrapper}>
          <Sparkles size={18} className={styles.sparkleIcon} />

          <input
            ref={inputRef}
            type="text"
            className={styles.input}
            placeholder="자연어로 데이터를 요청하세요... (예: 2022년 서울시장 공약 CSV로 뽑아줘)"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          />

          {inputValue && (
            <button type="button" className={styles.clearBtn} onClick={handleClear}>
              <X size={16} />
            </button>
          )}

          <button
            type="submit"
            className={styles.submitBtn}
            disabled={!inputValue.trim() || isLoading}
          >
            {isLoading ? <Loader2 size={18} className={styles.spinner} /> : <Search size={18} />}
          </button>
        </div>

        <kbd className={styles.shortcut}>⌘K</kbd>
      </form>

      {/* Query History Suggestions */}
      {showSuggestions && queryHistory.length > 0 && (
        <div className={styles.suggestions}>
          <div className={styles.suggestionsHeader}>RECENT QUERIES</div>
          {queryHistory.slice(0, 5).map((item, index) => (
            <button
              key={index}
              className={styles.suggestionItem}
              onClick={() => selectFromHistory(item.query)}
            >
              <Search size={14} />
              <span>{item.query}</span>
            </button>
          ))}
        </div>
      )}

      {/* Parsed Query Preview */}
      {parsedQuery && (
        <div className={styles.parsedPreview}>
          <span className={styles.intentBadge}>{parsedQuery.intent}</span>
          <span className={styles.confidence}>
            신뢰도: {Math.round(parsedQuery.confidence * 100)}%
          </span>
        </div>
      )}

      {/* Error Display */}
      {queryError && <div className={styles.error}>{queryError}</div>}
    </div>
  );
}
