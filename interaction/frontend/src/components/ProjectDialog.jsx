import { useState, useRef, useCallback, useEffect } from 'react';

export default function ProjectDialog({ open, mode, project, onClose, onSubmit, submitting }) {
  const [name, setName] = useState('');
  const [sourcePath, setSourcePath] = useState('');
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setName(project?.name || '');
      setSourcePath(project?.source_base_path || '');
      setFile(null);
      setDragOver(false);
    }
  }, [open, project]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.name.endsWith('.json')) {
      setFile(dropped);
    }
  }, []);

  const handleFileSelect = useCallback((e) => {
    const selected = e.target.files[0];
    if (selected) setFile(selected);
  }, []);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (!name.trim()) return;
    if (mode === 'create' && !file) return;

    const formData = new FormData();
    formData.append('name', name.trim());
    formData.append('source_base_path', sourcePath.trim());
    if (file) formData.append('topic_map', file);

    onSubmit(formData);
  }, [name, sourcePath, file, mode, onSubmit]);

  if (!open) return null;

  const isFirstTime = mode === 'create' && !onClose;

  return (
    <div className="project-overlay" onClick={isFirstTime ? undefined : onClose}>
      <div className="project-dialog" onClick={(e) => e.stopPropagation()}>
        <h2>{mode === 'create' ? 'New Project' : 'Edit Project'}</h2>
        {isFirstTime && (
          <p className="dialog-subtitle">
            Create your first project to get started. Upload a topic map JSON file and give it a name.
          </p>
        )}

        <form onSubmit={handleSubmit}>
          <label>
            Project Name
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. EE450 Week 1-8"
              autoFocus
            />
          </label>

          {mode === 'create' && (
            <label>
              Topic Map File
              <div
                className={`drop-zone${dragOver ? ' drag-over' : ''}${file ? ' has-file' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                {file ? (
                  <span className="drop-filename">{file.name}</span>
                ) : (
                  <span>Drop a .json file here or click to browse</span>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
              </div>
            </label>
          )}

          <label>
            Source Material Path
            <input
              type="text"
              value={sourcePath}
              onChange={(e) => setSourcePath(e.target.value)}
              placeholder="/path/to/course-repo"
            />
            <span className="hint">
              Base path to course repository. Expected subdirectories: discussion, exam, homework, lecture, student, textbook
            </span>
          </label>

          <div className="dialog-actions">
            {!isFirstTime && (
              <button type="button" className="btn-ghost" onClick={onClose}>
                Cancel
              </button>
            )}
            <button
              type="submit"
              className="btn-primary"
              disabled={submitting || !name.trim() || (mode === 'create' && !file)}
            >
              {submitting ? 'Saving...' : mode === 'create' ? 'Create Project' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
