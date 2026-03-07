import { useState, useCallback, useEffect } from 'react';
import { useTopicData } from './hooks/useTopicData';
import { useProjects } from './hooks/useProjects';
import TopicGraph from './components/TopicGraph';
import NodeDetail from './components/NodeDetail';
import Toolbar from './components/Toolbar';
import ProjectSidebar from './components/ProjectSidebar';
import ProjectDialog from './components/ProjectDialog';

export default function App() {
  const {
    graphData, metadata, loading, error,
    fetchTopicDetail, updateMastery, searchTopics,
    generateStudySession, launchClaude, reload,
  } = useTopicData();

  const {
    projects, activeProjectId, loading: projectsLoading,
    createProject, switchProject, updateProject, deleteProject, exportProject,
    refreshProjects,
  } = useProjects();

  const [lens, setLens] = useState('emphasis');
  const [focusPath, setFocusPath] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [highlightIds, setHighlightIds] = useState(new Set());

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showProjectDialog, setShowProjectDialog] = useState(false);
  const [projectDialogMode, setProjectDialogMode] = useState('create');
  const [editingProject, setEditingProject] = useState(null);
  const [dialogSubmitting, setDialogSubmitting] = useState(false);

  const activeProject = projects.find((p) => p.id === activeProjectId) || null;
  const hasProjects = projects.length > 0;
  const isFirstTime = !projectsLoading && !hasProjects;

  // Build a node lookup for breadcrumb labels
  const nodeMap = graphData
    ? new Map(graphData.nodes.map((n) => [n.id, n]))
    : new Map();

  // Reset graph state when switching projects
  const resetGraphState = useCallback(() => {
    setFocusPath([]);
    setSelectedNode(null);
    setDetailData(null);
    setHighlightIds(new Set());
  }, []);

  const handleNavigate = useCallback(
    async (nodeId) => {
      setFocusPath((prev) => [...prev, nodeId]);
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
        setFocusPath([]);
        setSelectedNode(null);
        setDetailData(null);
      } else {
        const next = focusPath.slice(0, index + 1);
        setFocusPath(next);
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

  // Project handlers
  const handleProjectSwitch = useCallback(async (id) => {
    await switchProject(id);
    resetGraphState();
    reload();
    setSidebarOpen(false);
  }, [switchProject, resetGraphState, reload]);

  const handleProjectCreate = useCallback(async (formData) => {
    setDialogSubmitting(true);
    try {
      await createProject(formData);
      resetGraphState();
      reload();
      setShowProjectDialog(false);
    } finally {
      setDialogSubmitting(false);
    }
  }, [createProject, resetGraphState, reload]);

  const handleProjectEdit = useCallback(async (formData) => {
    if (!editingProject) return;
    setDialogSubmitting(true);
    try {
      await updateProject(editingProject.id, {
        name: formData.get('name'),
        source_base_path: formData.get('source_base_path'),
      });
      setShowProjectDialog(false);
      setEditingProject(null);
    } finally {
      setDialogSubmitting(false);
    }
  }, [editingProject, updateProject]);

  const handleProjectDelete = useCallback(async (id) => {
    await deleteProject(id);
    resetGraphState();
    reload();
  }, [deleteProject, resetGraphState, reload]);

  const openNewDialog = useCallback(() => {
    setProjectDialogMode('create');
    setEditingProject(null);
    setShowProjectDialog(true);
  }, []);

  const openEditDialog = useCallback((project) => {
    setProjectDialogMode('edit');
    setEditingProject(project);
    setShowProjectDialog(true);
  }, []);

  // First-time setup: show project creation
  if (isFirstTime) {
    return (
      <div className="canvas">
        <div className="brand">
          <h1>Topic Map</h1>
          <span>Welcome</span>
        </div>
        <ProjectDialog
          open={true}
          mode="create"
          project={null}
          onClose={null}
          onSubmit={handleProjectCreate}
          submitting={dialogSubmitting}
        />
      </div>
    );
  }

  // Still loading projects
  if (projectsLoading) {
    return (
      <div className="canvas" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
          Loading...
        </p>
      </div>
    );
  }

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

  const breadcrumbs = focusPath.map((id) => {
    const node = nodeMap.get(id);
    return { id, label: node ? node.topic : id };
  });

  return (
    <div className="canvas">
      <ProjectSidebar
        open={sidebarOpen}
        onToggle={() => setSidebarOpen((v) => !v)}
        projects={projects}
        activeProjectId={activeProjectId}
        onSwitch={handleProjectSwitch}
        onNew={openNewDialog}
        onEdit={openEditDialog}
        onDelete={handleProjectDelete}
        onExport={exportProject}
      />

      <div className="brand">
        <h1>Topic Map</h1>
        <span>{activeProject?.name || metadata?.course_name || ''}</span>
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
        onStudyThis={generateStudySession}
        onLaunchClaude={launchClaude}
      />

      {showProjectDialog && (
        <ProjectDialog
          open={true}
          mode={projectDialogMode}
          project={editingProject}
          onClose={() => { setShowProjectDialog(false); setEditingProject(null); }}
          onSubmit={projectDialogMode === 'create' ? handleProjectCreate : handleProjectEdit}
          submitting={dialogSubmitting}
        />
      )}
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
