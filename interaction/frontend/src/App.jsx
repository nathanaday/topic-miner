import { useState, useCallback } from 'react';
import { useTopicData } from './hooks/useTopicData';
import TopicGraph from './components/TopicGraph';
import NodeDetail from './components/NodeDetail';
import Toolbar from './components/Toolbar';

export default function App() {
  const { graphData, metadata, loading, error, fetchTopicDetail, updateMastery, searchTopics } =
    useTopicData();

  const [lens, setLens] = useState('emphasis');
  const [depthOffset, setDepthOffset] = useState(1);
  const [selectedNode, setSelectedNode] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [highlightIds, setHighlightIds] = useState(new Set());

  const handleNodeClick = useCallback(
    async (node) => {
      if (!node) {
        setSelectedNode(null);
        setDetailData(null);
        return;
      }
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
    },
    [fetchTopicDetail],
  );

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

  const visibleCount = graphData
    ? graphData.nodes.filter((n) => {
        const maxD = Math.floor(1 * 0.8) + depthOffset;
        return n.depth <= maxD;
      }).length
    : 0;

  return (
    <div className="canvas">
      <div className="brand">
        <h1>Topic Map</h1>
        <span>{metadata?.course_name || ''}</span>
      </div>

      <Toolbar
        lens={lens}
        onLensChange={setLens}
        depthOffset={depthOffset}
        onDepthChange={setDepthOffset}
        onSearch={handleSearch}
      />

      <TopicGraph
        data={graphData}
        lens={lens}
        depthOffset={depthOffset}
        highlightIds={highlightIds}
        onNodeClick={handleNodeClick}
      />

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
