import { useState, useCallback } from 'react';

export default function Toolbar({ lens, onLensChange, depthOffset, onDepthChange, onSearch }) {
  const [query, setQuery] = useState('');

  const handleInput = useCallback(
    (e) => {
      const val = e.target.value;
      setQuery(val);
      onSearch(val);
    },
    [onSearch],
  );

  return (
    <div className="toolbar">
      {/* Lens toggle */}
      <div className="lens-toggle">
        <button
          className={lens === 'emphasis' ? 'active' : ''}
          onClick={() => onLensChange('emphasis')}
        >
          Course Emphasis
        </button>
        <button
          className={lens === 'progress' ? 'active' : ''}
          onClick={() => onLensChange('progress')}
        >
          My Progress
        </button>
      </div>

      <div className="divider" />

      {/* Depth control */}
      <div className="depth-control">
        <label>Depth</label>
        <button onClick={() => onDepthChange(Math.max(0, depthOffset - 1))}>-</button>
        <span className="depth-value">{depthOffset}</span>
        <button onClick={() => onDepthChange(Math.min(4, depthOffset + 1))}>+</button>
      </div>

      <div className="divider" />

      {/* Search */}
      <div className="search-box">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          placeholder="Search topics..."
          value={query}
          onChange={handleInput}
        />
      </div>
    </div>
  );
}
