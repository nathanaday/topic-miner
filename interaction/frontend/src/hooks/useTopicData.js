import { useState, useEffect, useCallback } from 'react';

const API = '/api';

export function useTopicData() {
  const [graphData, setGraphData] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [graphRes, metaRes] = await Promise.all([
          fetch(`${API}/graph`),
          fetch(`${API}/metadata`),
        ]);

        if (!graphRes.ok || !metaRes.ok) {
          throw new Error('Failed to load topic data');
        }

        const graph = await graphRes.json();
        const meta = await metaRes.json();

        if (!cancelled) {
          setGraphData(graph);
          setMetadata(meta);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      }
    }

    load();
    return () => { cancelled = true; };
  }, [reloadKey]);

  const reload = useCallback(() => {
    setGraphData(null);
    setMetadata(null);
    setReloadKey((k) => k + 1);
  }, []);

  const fetchTopicDetail = useCallback(async (id) => {
    const res = await fetch(`${API}/topics/${encodeURIComponent(id)}`);
    if (!res.ok) throw new Error('Topic not found');
    return res.json();
  }, []);

  const updateMastery = useCallback(async (id, score) => {
    const res = await fetch(`${API}/topics/${encodeURIComponent(id)}/mastery`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mastery_score: score }),
    });
    if (!res.ok) throw new Error('Failed to update mastery');
    setGraphData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        nodes: prev.nodes.map((n) =>
          n.original_id === id ? { ...n, student_mastery_score: score } : n,
        ),
      };
    });
    return res.json();
  }, []);

  const searchTopics = useCallback(async (query) => {
    if (!query || query.length < 2) return [];
    const res = await fetch(`${API}/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) return [];
    return res.json();
  }, []);

  const generateStudySession = useCallback(async (id) => {
    const res = await fetch(`${API}/topics/${encodeURIComponent(id)}/study-session`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to generate study session');
    }
    return res.json();
  }, []);

  const launchClaude = useCallback(async (filePath) => {
    const res = await fetch(`${API}/launch-claude`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to launch Claude');
    }
    return res.json();
  }, []);

  return {
    graphData,
    metadata,
    loading,
    error,
    fetchTopicDetail,
    updateMastery,
    searchTopics,
    generateStudySession,
    launchClaude,
    reload,
  };
}
