import { useState, useEffect, useCallback } from 'react';

const API = '/api';

export function useProjects() {
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await fetch(`${API}/projects`);
      if (!res.ok) throw new Error('Failed to load projects');
      const data = await res.json();
      setProjects(data.projects || []);
      setActiveProjectId(data.active_project_id || null);
    } catch {
      setProjects([]);
      setActiveProjectId(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const createProject = useCallback(async (formData) => {
    const res = await fetch(`${API}/projects`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create project');
    }
    const project = await res.json();
    await fetchProjects();
    return project;
  }, [fetchProjects]);

  const switchProject = useCallback(async (id) => {
    const res = await fetch(`${API}/projects/${id}/activate`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to switch project');
    const project = await res.json();
    setActiveProjectId(id);
    return project;
  }, []);

  const updateProject = useCallback(async (id, data) => {
    const res = await fetch(`${API}/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update project');
    const project = await res.json();
    await fetchProjects();
    return project;
  }, [fetchProjects]);

  const deleteProject = useCallback(async (id) => {
    const res = await fetch(`${API}/projects/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete project');
    await fetchProjects();
  }, [fetchProjects]);

  const exportProject = useCallback(async (id) => {
    const res = await fetch(`${API}/projects/${id}/export`);
    if (!res.ok) throw new Error('Failed to export project');
    const blob = await res.blob();
    const disposition = res.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="(.+)"/);
    const filename = match ? match[1] : 'topic_map_backup.json';
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, []);

  return {
    projects,
    activeProjectId,
    loading,
    createProject,
    switchProject,
    updateProject,
    deleteProject,
    exportProject,
    refreshProjects: fetchProjects,
  };
}
