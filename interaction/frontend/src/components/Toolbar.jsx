import { useState, useCallback } from 'react';

export default function Toolbar({ lens, onLensChange, breadcrumbs, onBreadcrumbJump, onSearch }) {
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

      {/* Breadcrumb navigation */}
      <div className="breadcrumb-nav">
        {breadcrumbs.length === 0 ? (
          <span className="breadcrumb-current">Overview</span>
        ) : (
          <>
            <button
              className="breadcrumb-link"
              onClick={() => onBreadcrumbJump(-1)}
            >
              Overview
            </button>
            {breadcrumbs.map((crumb, i) => (
              <span key={crumb.id} className="breadcrumb-segment">
                <span className="breadcrumb-sep">/</span>
                {i === breadcrumbs.length - 1 ? (
                  <span className="breadcrumb-current">{crumb.label}</span>
                ) : (
                  <button
                    className="breadcrumb-link"
                    onClick={() => onBreadcrumbJump(i)}
                  >
                    {crumb.label}
                  </button>
                )}
              </span>
            ))}
          </>
        )}
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
