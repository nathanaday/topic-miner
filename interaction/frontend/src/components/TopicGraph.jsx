import { useRef, useEffect } from 'react';
import * as d3 from 'd3';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RADIUS = { concept: 26, subtopic: 14, learning_outcome: 8 };
const LABEL_PX_THRESHOLD = 12;
const RECONCILE_DEBOUNCE_MS = 120;

const EMPHASIS = {
  critical: '#79c0ff',
  important: '#58a6ff',
  moderate: '#1f6feb',
  low: '#30363d',
};

const PROGRESS_THRESHOLDS = [
  [80, '#3fb950'],
  [50, '#d29922'],
  [0, '#f85149'],
];

function nodeRadius(level) {
  return RADIUS[level] || 8;
}

function nodeColor(node, lens) {
  if (lens === 'emphasis') {
    return EMPHASIS[node.priority_band] || EMPHASIS.low;
  }
  const m = node.student_mastery_score;
  if (m == null) return '#30363d';
  for (const [threshold, color] of PROGRESS_THRESHOLDS) {
    if (m >= threshold) return color;
  }
  return '#30363d';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TopicGraph({ data, lens, depthOffset, highlightIds, onNodeClick }) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const simRef = useRef(null);
  const reconcileRef = useRef(null);
  const labelVisRef = useRef(null);
  const lensRef = useRef(lens);
  const depthRef = useRef(depthOffset);
  const highlightRef = useRef(highlightIds);
  const currentKRef = useRef(1);

  useEffect(() => { lensRef.current = lens; }, [lens]);
  useEffect(() => { depthRef.current = depthOffset; }, [depthOffset]);
  useEffect(() => { highlightRef.current = highlightIds; }, [highlightIds]);

  // -----------------------------------------------------------------------
  // Main D3 setup -- runs once when data loads
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (!data || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const svg = d3
      .select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    svg.selectAll('*').remove();

    // -- Defs -----------------------------------------------------------
    const defs = svg.append('defs');
    const glowFilter = defs.append('filter').attr('id', 'glow');
    glowFilter.append('feGaussianBlur').attr('stdDeviation', '3.5').attr('result', 'blur');
    const glowMerge = glowFilter.append('feMerge');
    glowMerge.append('feMergeNode').attr('in', 'blur');
    glowMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    const hlFilter = defs.append('filter').attr('id', 'highlight-ring');
    hlFilter.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'blur');
    const hlMerge = hlFilter.append('feMerge');
    hlMerge.append('feMergeNode').attr('in', 'blur');
    hlMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    const g = svg.append('g');
    const linkGroup = g.append('g');
    const nodeGroup = g.append('g');

    // -- Build lookup structures from full data -------------------------
    const allNodes = new Map();
    data.nodes.forEach((n) => {
      n.radius = nodeRadius(n.level);
      allNodes.set(n.id, n);
    });

    const allLinks = new Map();
    data.links.forEach((l) => {
      allLinks.set(`${l.source}__${l.target}`, l);
    });

    // -- Position roots on a circle -------------------------------------
    const roots = data.nodes.filter((n) => n.depth === 0);
    const step = (2 * Math.PI) / (roots.length || 1);
    const orbit = Math.min(width, height) * 0.35;
    roots.forEach((node, i) => {
      node.x = width / 2 + Math.cos(i * step) * orbit;
      node.y = height / 2 + Math.sin(i * step) * orbit;
    });

    // -- Position cache (survives add/remove cycles) --------------------
    const posCache = new Map();

    // -- Active set tracking --------------------------------------------
    let currentActiveIds = new Set();
    let currentMaxDepth = -1;

    // Mutable D3 selections (updated by rebindSVG)
    let linkEls = linkGroup.selectAll('line');
    let nodeGs = nodeGroup.selectAll('.node-group');

    // -- Drag behavior (defined once, references simRef) ----------------
    const dragBehavior = d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simRef.current?.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simRef.current?.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    // -- Compute which nodes/links should be active ---------------------
    function computeActiveNodes(maxDepth) {
      const active = new Set();
      for (const [id, node] of allNodes) {
        if (node.depth <= maxDepth) {
          active.add(id);
        }
      }
      return active;
    }

    function computeActiveLinks(activeIds) {
      const links = [];
      for (const [, link] of allLinks) {
        const sid = typeof link.source === 'object' ? link.source.id : link.source;
        const tid = typeof link.target === 'object' ? link.target.id : link.target;
        if (activeIds.has(sid) && activeIds.has(tid)) {
          links.push(link);
        }
      }
      return links;
    }

    // -- SVG data-join with enter/exit ----------------------------------
    function rebindSVG(nodes, links) {
      // Links
      const linkSel = linkGroup
        .selectAll('line')
        .data(links, (d) => `${typeof d.source === 'object' ? d.source.id : d.source}__${typeof d.target === 'object' ? d.target.id : d.target}`);

      linkSel.exit().remove();

      const linkEnter = linkSel
        .enter()
        .append('line')
        .attr('stroke', 'rgba(255,255,255,0.07)')
        .attr('stroke-width', 0.6);

      linkEls = linkEnter.merge(linkSel);

      // Nodes
      const nodeSel = nodeGroup
        .selectAll('.node-group')
        .data(nodes, (d) => d.id);

      nodeSel.exit().remove();

      const nodeEnter = nodeSel
        .enter()
        .append('g')
        .attr('class', 'node-group')
        .attr('cursor', 'pointer')
        .attr('transform', (d) => `translate(${d.x || 0},${d.y || 0})`)
        .on('click', (event, d) => {
          event.stopPropagation();
          onNodeClick(d);
        })
        .call(dragBehavior);

      // Highlight ring
      nodeEnter
        .append('circle')
        .attr('class', 'highlight-ring')
        .attr('r', (d) => d.radius + 5)
        .attr('fill', 'none')
        .attr('stroke', '#d29922')
        .attr('stroke-width', 2)
        .attr('filter', 'url(#highlight-ring)')
        .style('opacity', 0);

      // Main circle with entrance animation
      nodeEnter
        .append('circle')
        .attr('class', 'node-circle')
        .attr('r', 0)
        .attr('fill', (d) => nodeColor(d, lensRef.current))
        .attr('stroke', 'rgba(255,255,255,0.08)')
        .attr('stroke-width', 0.5)
        .attr('filter', (d) => (d.priority_band === 'critical' ? 'url(#glow)' : null))
        .transition()
        .duration(400)
        .ease(d3.easeElasticOut.amplitude(1).period(0.45))
        .attr('r', (d) => d.radius);

      // Label
      nodeEnter
        .append('text')
        .attr('class', 'node-label')
        .attr('x', (d) => d.radius + 6)
        .attr('y', 0)
        .attr('dy', '0.35em')
        .attr('fill', '#e6edf3')
        .attr('font-size', (d) => (d.depth === 0 ? '12px' : '10px'))
        .attr('font-weight', (d) => (d.depth === 0 ? 600 : 400))
        .attr('font-family', "'Figtree', sans-serif")
        .text((d) => (d.topic.length > 36 ? d.topic.slice(0, 34) + '...' : d.topic))
        .style('opacity', 0)
        .transition()
        .delay(200)
        .duration(250)
        .style('opacity', (d) => {
          const k = currentKRef.current;
          return d.radius * k > LABEL_PX_THRESHOLD ? 1 : 0;
        });

      // Subtitle
      nodeEnter
        .append('text')
        .attr('class', 'node-subtitle')
        .attr('x', (d) => d.radius + 6)
        .attr('y', 14)
        .attr('fill', '#484f58')
        .attr('font-size', '8px')
        .attr('font-family', "'Figtree', sans-serif")
        .text((d) => (d.depth > 0 ? d.root_topic : ''))
        .style('opacity', 0);

      // Hover (on entering nodes)
      nodeEnter
        .on('mouseenter', function (event, d) {
          d3.select(this)
            .select('.node-circle')
            .transition()
            .duration(150)
            .attr('r', d.radius * 1.25)
            .attr('stroke', '#d29922')
            .attr('stroke-width', 1.5);

          linkEls
            .transition()
            .duration(150)
            .attr('stroke', (l) => {
              const sid = typeof l.source === 'object' ? l.source.id : l.source;
              const tid = typeof l.target === 'object' ? l.target.id : l.target;
              return sid === d.id || tid === d.id ? '#d29922' : 'rgba(255,255,255,0.03)';
            })
            .attr('stroke-width', (l) => {
              const sid = typeof l.source === 'object' ? l.source.id : l.source;
              const tid = typeof l.target === 'object' ? l.target.id : l.target;
              return sid === d.id || tid === d.id ? 1.5 : 0.4;
            });

          nodeGs
            .transition()
            .duration(150)
            .style('opacity', (n) => {
              if (n.id === d.id) return 1;
              if (n.parent_id === d.id || d.parent_id === n.id) return 0.85;
              return 0.12;
            });
        })
        .on('mouseleave', function () {
          nodeGs
            .select('.node-circle')
            .transition()
            .duration(200)
            .attr('r', (d) => d.radius)
            .attr('stroke', 'rgba(255,255,255,0.08)')
            .attr('stroke-width', 0.5);

          linkEls
            .transition()
            .duration(200)
            .attr('stroke', 'rgba(255,255,255,0.07)')
            .attr('stroke-width', 0.6);

          nodeGs.transition().duration(200).style('opacity', 1);
        });

      nodeGs = nodeEnter.merge(nodeSel);

      updateLabelVisibility();
    }

    // -- Label visibility (lightweight, no layout change) ---------------
    function updateLabelVisibility() {
      const k = currentKRef.current;
      const hl = highlightRef.current;

      nodeGs.select('.node-label')
        .style('opacity', (d) => (d.radius * k > LABEL_PX_THRESHOLD ? 1 : 0));

      nodeGs.select('.node-subtitle')
        .style('opacity', (d) => (d.radius * k > 20 && d.depth > 0 ? 0.55 : 0));

      nodeGs.select('.highlight-ring')
        .style('opacity', (d) => (hl && hl.has(d.original_id) ? 1 : 0));
    }

    labelVisRef.current = updateLabelVisibility;

    // -- Reconcile simulation (add/remove nodes) ------------------------
    function reconcile(newMaxDepth) {
      if (newMaxDepth === currentMaxDepth) return;
      currentMaxDepth = newMaxDepth;

      const newActiveIds = computeActiveNodes(newMaxDepth);

      // Determine entering and exiting
      const entering = new Set();
      const exiting = new Set();

      for (const id of newActiveIds) {
        if (!currentActiveIds.has(id)) entering.add(id);
      }
      for (const id of currentActiveIds) {
        if (!newActiveIds.has(id)) exiting.add(id);
      }

      if (entering.size === 0 && exiting.size === 0) return;

      // Cache positions of exiting nodes
      for (const id of exiting) {
        const node = allNodes.get(id);
        if (node && node.x != null) {
          posCache.set(id, { x: node.x, y: node.y });
        }
      }

      // Position entering nodes
      for (const id of entering) {
        const node = allNodes.get(id);
        const cached = posCache.get(id);
        if (cached) {
          node.x = cached.x;
          node.y = cached.y;
        } else if (node.parent_id) {
          const parent = allNodes.get(node.parent_id);
          if (parent && parent.x != null) {
            node.x = parent.x + (Math.random() - 0.5) * 30;
            node.y = parent.y + (Math.random() - 0.5) * 30;
          } else {
            node.x = width / 2 + (Math.random() - 0.5) * 100;
            node.y = height / 2 + (Math.random() - 0.5) * 100;
          }
        }
      }

      currentActiveIds = newActiveIds;
      const activeNodes = [...newActiveIds].map((id) => allNodes.get(id));
      const activeLinks = computeActiveLinks(newActiveIds);

      // Update simulation
      sim.nodes(activeNodes);
      sim.force('link').links(activeLinks);

      // Scale alpha based on how many nodes are entering
      const enterRatio = entering.size / Math.max(newActiveIds.size, 1);
      sim.alpha(Math.min(0.35, 0.08 + enterRatio * 0.25)).restart();

      rebindSVG(activeNodes, activeLinks);
    }

    reconcileRef.current = reconcile;

    // -- Simulation -----------------------------------------------------
    function getMaxDepth() {
      return Math.floor(currentKRef.current * 0.8) + depthRef.current;
    }

    const initialMaxDepth = getMaxDepth();
    const initialActiveIds = computeActiveNodes(initialMaxDepth);
    const initialNodes = [...initialActiveIds].map((id) => allNodes.get(id));
    const initialLinks = computeActiveLinks(initialActiveIds);
    currentActiveIds = initialActiveIds;
    currentMaxDepth = initialMaxDepth;

    const sim = d3
      .forceSimulation(initialNodes)
      .force(
        'link',
        d3.forceLink(initialLinks)
          .id((d) => d.id)
          .distance((d) => {
            const target = typeof d.target === 'object' ? d.target : allNodes.get(d.target);
            if (!target) return 100;
            if (target.depth === 1) return 130;
            if (target.depth === 2) return 60;
            return 40;
          })
          .strength(0.4),
      )
      .force(
        'charge',
        d3.forceManyBody().strength((d) => {
          if (d.depth === 0) return -350;
          if (d.depth === 1) return -40;
          return -15;
        }),
      )
      .force('center', d3.forceCenter(width / 2, height / 2).strength(0.04))
      .force('collision', d3.forceCollide().radius((d) => d.radius + 3))
      .alpha(0.9)
      .alphaDecay(0.018)
      .on('tick', () => {
        linkEls
          .attr('x1', (d) => d.source.x)
          .attr('y1', (d) => d.source.y)
          .attr('x2', (d) => d.target.x)
          .attr('y2', (d) => d.target.y);
        nodeGs.attr('transform', (d) => `translate(${d.x},${d.y})`);
      });

    simRef.current = sim;

    // Initial SVG bindings
    rebindSVG(initialNodes, initialLinks);

    // -- Zoom -----------------------------------------------------------
    let reconcileTimer = null;

    const zoom = d3.zoom()
      .scaleExtent([0.15, 12])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        currentKRef.current = event.transform.k;

        clearTimeout(reconcileTimer);
        reconcileTimer = setTimeout(() => {
          const newMaxDepth = getMaxDepth();
          reconcile(newMaxDepth);
          updateLabelVisibility();
        }, RECONCILE_DEBOUNCE_MS);
      });

    svg.call(zoom);
    svg.call(
      zoom.transform,
      d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(0.75)
        .translate(-width / 2, -height / 2),
    );

    // Click background to deselect
    svg.on('click', () => onNodeClick(null));

    return () => {
      clearTimeout(reconcileTimer);
      sim.stop();
    };
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  // -----------------------------------------------------------------------
  // Lens change -- update colors only
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (!svgRef.current || !data) return;
    d3.select(svgRef.current)
      .selectAll('.node-circle')
      .transition()
      .duration(350)
      .attr('fill', (d) => nodeColor(d, lens))
      .attr('filter', (d) =>
        lens === 'emphasis' && d.priority_band === 'critical' ? 'url(#glow)' : null,
      );
  }, [lens, data]);

  // -----------------------------------------------------------------------
  // Depth offset change -- reconcile simulation
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (reconcileRef.current) {
      const maxD = Math.floor(currentKRef.current * 0.8) + depthOffset;
      reconcileRef.current(maxD);
    }
  }, [depthOffset]);

  // -----------------------------------------------------------------------
  // Search highlight change
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (labelVisRef.current) labelVisRef.current();
  }, [highlightIds]);

  return (
    <div ref={containerRef} className="graph-container">
      <svg ref={svgRef} />
    </div>
  );
}
