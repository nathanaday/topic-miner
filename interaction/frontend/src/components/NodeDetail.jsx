import { useState, useCallback, useEffect } from 'react';

export default function NodeDetail({ open, data, loading, onClose, onMasteryUpdate, onStudyThis, onLaunchClaude }) {
  const [mastery, setMastery] = useState(null);
  const [saving, setSaving] = useState(false);
  const [studyLoading, setStudyLoading] = useState(false);
  const [studyResult, setStudyResult] = useState(null);
  const [studyError, setStudyError] = useState(null);
  const [copied, setCopied] = useState(false);

  // Reset study state when selected node changes
  useEffect(() => {
    setStudyResult(null);
    setStudyError(null);
    setStudyLoading(false);
    setCopied(false);
  }, [data?.id]);

  // Sync mastery slider with incoming data
  const currentMastery = mastery ?? data?.student_mastery_score ?? 0;

  const handleSave = useCallback(async () => {
    if (!data?.id) return;
    setSaving(true);
    try {
      await onMasteryUpdate(data.original_id || data.id, currentMastery);
    } finally {
      setSaving(false);
      setMastery(null);
    }
  }, [data, currentMastery, onMasteryUpdate]);

  const handleStudyThis = useCallback(async () => {
    if (!data?.id) return;
    setStudyLoading(true);
    setStudyError(null);
    try {
      const result = await onStudyThis(data.original_id || data.id);
      setStudyResult(result);
    } catch (err) {
      setStudyError(err.message);
    } finally {
      setStudyLoading(false);
    }
  }, [data, onStudyThis]);

  const handleCopyToClipboard = useCallback(async () => {
    if (!studyResult) return;
    try {
      await navigator.clipboard.writeText(studyResult.markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setStudyError('Failed to copy to clipboard');
    }
  }, [studyResult]);

  const handleLaunchClaude = useCallback(async () => {
    if (!studyResult) return;
    try {
      await onLaunchClaude(studyResult.file_path);
    } catch (err) {
      setStudyError(err.message);
    }
  }, [studyResult, onLaunchClaude]);

  return (
    <div className={`detail-panel ${open ? 'open' : ''}`}>
      {loading && (
        <div style={{ padding: 24, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading...
        </div>
      )}

      {!loading && data && (
        <>
          <div className="detail-header">
            <button className="close-btn" onClick={onClose} aria-label="Close">
              &times;
            </button>
            <h2>{data.topic}</h2>
            <span className={`level-badge ${data.level}`}>{formatLevel(data.level)}</span>
          </div>

          <div className="detail-body">
            {/* Priority score */}
            {data.priority_score != null && (
              <div className="detail-section">
                <h3>Priority</h3>
                <div className="score-row">
                  <span className={`priority-band ${data.priority_band}`}>{data.priority_band}</span>
                  <div className="score-bar">
                    <div
                      className="score-bar-fill"
                      style={{
                        width: `${data.priority_score}%`,
                        background: bandColor(data.priority_band),
                      }}
                    />
                  </div>
                  <span className="score-label" style={{ color: bandColor(data.priority_band) }}>
                    {data.priority_score}
                  </span>
                </div>
              </div>
            )}

            {/* Description */}
            {data.description && (
              <div className="detail-section">
                <h3>Description</h3>
                <p>{data.description}</p>
              </div>
            )}

            {/* Study note */}
            {data.study_note && (
              <div className="detail-section">
                <h3>Study Note</h3>
                <p>{data.study_note}</p>
              </div>
            )}

            {/* Mastery checklist */}
            {data.mastery_checklist && data.mastery_checklist.length > 0 && (
              <div className="detail-section">
                <h3>Mastery Checklist</h3>
                <ul className="checklist">
                  {data.mastery_checklist.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Mastery score control */}
            <div className="detail-section">
              <h3>My Mastery</h3>
              <div className="mastery-control">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={currentMastery}
                  onChange={(e) => setMastery(Number(e.target.value))}
                />
                <div className="mastery-row">
                  <span
                    className="mastery-val"
                    style={{ color: masteryColor(currentMastery) }}
                  >
                    {currentMastery}
                  </span>
                  <button onClick={handleSave} disabled={saving}>
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </div>
            </div>

            {/* Study session */}
            <div className="detail-section">
              <h3>Study Session</h3>
              {!studyResult && (
                <button
                  className="study-btn"
                  onClick={handleStudyThis}
                  disabled={studyLoading}
                >
                  {studyLoading ? 'Generating...' : 'Study This'}
                </button>
              )}
              {studyError && <p className="study-error">{studyError}</p>}
              {studyResult && (
                <>
                  <p className="study-ready">Session ready: {studyResult.topic_name}</p>
                  <div className="study-btn-row">
                    <button className="study-btn" onClick={handleCopyToClipboard}>
                      {copied ? 'Copied!' : 'Copy to Clipboard'}
                    </button>
                    <button className="study-btn study-btn-launch" onClick={handleLaunchClaude}>
                      Launch Claude
                    </button>
                  </div>
                  <span className="study-path">{studyResult.file_path}</span>
                </>
              )}
            </div>

            {/* Source references */}
            {data.source_refs && data.source_refs.length > 0 && (
              <CollapsibleSection title={`Sources (${data.source_refs.length})`}>
                {data.source_refs.map((ref, i) => (
                  <div className="source-ref" key={i}>
                    <span className="filename">{ref.filename}</span>
                    <span className="meta">
                      {ref.material_type} | lines {ref.lines?.[0]}-{ref.lines?.[1]}
                    </span>
                    {ref.quote_snippet && (
                      <span className="snippet">"{ref.quote_snippet}"</span>
                    )}
                  </div>
                ))}
              </CollapsibleSection>
            )}

            {/* Importance signals */}
            {data.importance_signals && data.importance_signals.length > 0 && (
              <CollapsibleSection title={`Signals (${data.importance_signals.length})`}>
                {data.importance_signals.map((sig, i) => (
                  <div className="signal" key={i}>
                    <div className="signal-type">{sig.type}</div>
                    <div className="signal-detail">{sig.detail}</div>
                  </div>
                ))}
              </CollapsibleSection>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function CollapsibleSection({ title, children }) {
  const [open, setOpen] = useState(true);

  return (
    <div className="detail-section">
      <div className="collapsible-header" onClick={() => setOpen(!open)}>
        <span className={`chevron ${open ? 'open' : ''}`}>&#9654;</span>
        <h3>{title}</h3>
      </div>
      {open && <div className="collapsible-body">{children}</div>}
    </div>
  );
}

function formatLevel(level) {
  if (!level) return '';
  return level.replace(/_/g, ' ');
}

function bandColor(band) {
  switch (band) {
    case 'critical': return 'var(--emphasis-critical)';
    case 'important': return 'var(--emphasis-important)';
    case 'moderate': return 'var(--emphasis-moderate)';
    default: return 'var(--text-muted)';
  }
}

function masteryColor(score) {
  if (score >= 80) return 'var(--progress-mastered)';
  if (score >= 50) return 'var(--progress-learning)';
  if (score > 0) return 'var(--progress-struggling)';
  return 'var(--text-muted)';
}
