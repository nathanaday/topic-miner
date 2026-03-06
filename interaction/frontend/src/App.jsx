import { useState, useCallback, useEffect } from 'react';
import { useTopicData } from './hooks/useTopicData';
import TopicGraph from './components/TopicGraph';
import NodeDetail from './components/NodeDetail';
import Toolbar from './components/Toolbar';

export default function App() {
  const { graphData, metadata, loading, error, fetchTopicDetail, updateMastery, searchTopics } =
    useTopicData();

  const [lens, setLens] = useState('emphasis');
  const [focusPath, setFocusPath] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [highlightIds, setHighlightIds] = useState(new Set());

  // Build a node lookup for breadcrumb labels
  const nodeMap = graphData
    ? new Map(graphData.nodes.map((n) => [n.id, n]))
    : new Map();

  const handleNavigate = useCallback(
    async (nodeId) => {
      setFocusPath((prev) => [...prev, nodeId]);
      // Auto-show detail for the focused node
      const node = nodeMap.get(nodeId);
      if (node) {
        setSelectedNode(node);
        setDetailLoading(true);
        try {
          const full = await fetchTopicDetail(node.original_id || node.id);
          setDetailData(full);
        } catch {
          setDetailData(node);
        } finally {
          setDetailLoading(false);
        }
      }
    },
    [fetchTopicDetail, nodeMap],
  );

  const handleBack = useCallback(() => {
    setFocusPath((prev) => {
      if (prev.length === 0) return prev;
      const next = prev.slice(0, -1);
      // If going back to overview, close detail panel
      if (next.length === 0) {
        setSelectedNode(null);
        setDetailData(null);
      }
      return next;
    });
  }, []);

  const handleBreadcrumbJump = useCallback(
    async (index) => {
      if (index < 0) {
        // Jump to overview
        setFocusPath([]);
        setSelectedNode(null);
        setDetailData(null);
      } else {
        const next = focusPath.slice(0, index + 1);
        setFocusPath(next);
        // Auto-show detail for the node we jumped to
        const nodeId = next[next.length - 1];
        const node = nodeMap.get(nodeId);
        if (node) {
          setSelectedNode(node);
          setDetailLoading(true);
          try {
            const full = await fetchTopicDetail(node.original_id || node.id);
            setDetailData(full);
          } catch {
            setDetailData(node);
          } finally {
            setDetailLoading(false);
          }
        }
      }
    },
    [focusPath, fetchTopicDetail, nodeMap],
  );

  // When focusPath changes to a non-empty value, auto-fetch detail for the focused node
  useEffect(() => {
    if (focusPath.length === 0) return;
    const nodeId = focusPath[focusPath.length - 1];
    const node = nodeMap.get(nodeId);
    if (node && (!selectedNode || selectedNode.id !== nodeId)) {
      setSelectedNode(node);
      setDetailLoading(true);
      fetchTopicDetail(node.original_id || node.id)
        .then((full) => setDetailData(full))
        .catch(() => setDetailData(node))
        .finally(() => setDetailLoading(false));
    }
  }, [focusPath]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleClose = useCallback(() => {
    setSelectedNode(null);
    setDetailData(null);
  }, []);

  const handleMasteryUpdate = useCallback(
    async (id, score) => {
      await updateMastery(id, score);
      if (detailData && (detailData.id === id || detailData.original_id === id)) {
        setDetailData((prev) => ({ ...prev, student_mastery_score: score }));
      }
    },
    [updateMastery, detailData],
  );

  const handleSearch = useCallback(
    async (query) => {
      if (!query || query.length < 2) {
        setHighlightIds(new Set());
        return;
      }
      const results = await searchTopics(query);
      setHighlightIds(new Set(results.map((r) => r.id)));
    },
    [searchTopics],
  );

  if (loading) {
    return (
      <div className="canvas" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
          Loading topic map...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="canvas" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--progress-struggling)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
          {error}
        </p>
      </div>
    );
  }

  // Build breadcrumb labels from focusPath
  const breadcrumbs = focusPath.map((id) => {
    const node = nodeMap.get(id);
    return { id, label: node ? node.topic : id };
  });

  return (
    <div className="canvas">
      <div className="brand">
        <h1>Topic Map</h1>
        <span>{metadata?.course_name || ''}</span>
      </div>

      <Toolbar
        lens={lens}
        onLensChange={setLens}
        breadcrumbs={breadcrumbs}
        onBreadcrumbJump={handleBreadcrumbJump}
        onSearch={handleSearch}
      />

      <TopicGraph
        data={graphData}
        lens={lens}
        focusPath={focusPath}
        highlightIds={highlightIds}
        onNavigate={handleNavigate}
        onBack={handleBack}
      />

      {focusPath.length > 0 && (
        <button className="back-button" onClick={handleBack}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          {focusPath.length === 1
            ? 'Back to Overview'
            : `Back to ${nodeMap.get(focusPath[focusPath.length - 2])?.topic || 'parent'}`}
        </button>
      )}

      <Legend lens={lens} />

      <div className="node-count">
        <strong>{graphData?.nodes?.length ?? 0}</strong> total nodes
      </div>

      <NodeDetail
        open={!!selectedNode}
        data={detailData}
        loading={detailLoading}
        onClose={handleClose}
        onMasteryUpdate={handleMasteryUpdate}
      />
    </div>
  );
}

function Legend({ lens }) {
  const items =
    lens === 'emphasis'
      ? [
          { color: 'var(--emphasis-critical)', label: 'Critical' },
          { color: 'var(--emphasis-important)', label: 'Important' },
          { color: 'var(--emphasis-moderate)', label: 'Moderate' },
          { color: 'var(--emphasis-low)', label: 'Low' },
        ]
      : [
          { color: 'var(--progress-mastered)', label: 'Mastered' },
          { color: 'var(--progress-learning)', label: 'Learning' },
          { color: 'var(--progress-struggling)', label: 'Struggling' },
          { color: 'var(--progress-none)', label: 'Not started' },
        ];

  return (
    <div className="legend">
      {items.map((item) => (
        <div className="legend-item" key={item.label}>
          <div className="legend-dot" style={{ background: item.color }} />
          {item.label}
        </div>
      ))}
    </div>
  );
}
