import { useState, useRef, useEffect, useCallback } from 'react';

export default function ProjectSidebar({
  open,
  onToggle,
  projects,
  activeProjectId,
  onSwitch,
  onNew,
  onEdit,
  onDelete,
  onExport,
}) {
  const [confirmDelete, setConfirmDelete] = useState(null);
  const sidebarRef = useRef(null);

  useEffect(() => {
    if (!open) setConfirmDelete(null);
  }, [open]);

  const handleDelete = useCallback((id) => {
    if (confirmDelete === id) {
      onDelete(id);
      setConfirmDelete(null);
    } else {
      setConfirmDelete(id);
    }
  }, [confirmDelete, onDelete]);

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <>
      <button
        className={`sidebar-toggle${open ? ' open' : ''}`}
        onClick={onToggle}
        title={open ? 'Close sidebar' : 'Projects'}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {open ? (
            <>
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </>
          ) : (
            <>
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
              <rect x="14" y="14" width="7" height="7" rx="1" />
            </>
          )}
        </svg>
      </button>

      <div className={`project-sidebar${open ? ' open' : ''}`} ref={sidebarRef}>
        <div className="sidebar-header">
          <h3>Projects</h3>
        </div>

        <div className="project-list">
          {projects.map((p) => (
            <div
              key={p.id}
              className={`project-card${p.id === activeProjectId ? ' active' : ''}`}
              onClick={() => p.id !== activeProjectId && onSwitch(p.id)}
            >
              <div className="project-dot" />
              <div className="project-info">
                <div className="project-name">{p.name}</div>
                <div className="project-date">{formatDate(p.last_opened_at)}</div>
              </div>
              <div className="project-actions" onClick={(e) => e.stopPropagation()}>
                <button
                  className="project-action-btn"
                  onClick={() => onEdit(p)}
                  title="Edit project"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                </button>
                <button
                  className="project-action-btn"
                  onClick={() => onExport(p.id)}
                  title="Export backup"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                </button>
                <button
                  className={`project-action-btn delete${confirmDelete === p.id ? ' confirming' : ''}`}
                  onClick={() => handleDelete(p.id)}
                  title={confirmDelete === p.id ? 'Click again to confirm' : 'Delete project'}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>

        <button className="project-new-btn" onClick={onNew}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Project
        </button>
      </div>
    </>
  );
}
