import { useRef, useEffect } from 'react';
import * as d3 from 'd3';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const LABEL_PX_THRESHOLD = 12;

const RADIUS_OVERVIEW = 40;
const RADIUS_FOCUSED = 36;
const RADIUS_CHILD = 20;

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

export default function TopicGraph({ data, lens, focusPath, highlightIds, onNavigate, onBack }) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const simRef = useRef(null);
  const reconcileRef = useRef(null);
  const labelVisRef = useRef(null);
  const lensRef = useRef(lens);
  const focusPathRef = useRef(focusPath);
  const highlightRef = useRef(highlightIds);
  const currentKRef = useRef(1);
  const onNavigateRef = useRef(onNavigate);
  const onBackRef = useRef(onBack);

  useEffect(() => { lensRef.current = lens; }, [lens]);
  useEffect(() => { focusPathRef.current = focusPath; }, [focusPath]);
  useEffect(() => { highlightRef.current = highlightIds; }, [highlightIds]);
  useEffect(() => { onNavigateRef.current = onNavigate; }, [onNavigate]);
  useEffect(() => { onBackRef.current = onBack; }, [onBack]);

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
      allNodes.set(n.id, n);
    });

    const allLinks = new Map();
    data.links.forEach((l) => {
      allLinks.set(`${l.source}__${l.target}`, l);
    });

    // Children lookup: parent_id -> [child nodes]
    const childrenOf = new Map();
    data.nodes.forEach((n) => {
      if (n.parent_id) {
        if (!childrenOf.has(n.parent_id)) childrenOf.set(n.parent_id, []);
        childrenOf.get(n.parent_id).push(n);
      }
    });

    // -- Position roots on a circle -------------------------------------
    const roots = data.nodes.filter((n) => n.depth === 0);
    const step = (2 * Math.PI) / (roots.length || 1);
    const orbit = Math.min(width, height) * 0.2;
    roots.forEach((node, i) => {
      node.x = width / 2 + Math.cos(i * step) * orbit;
      node.y = height / 2 + Math.sin(i * step) * orbit;
    });

    // -- Position cache (survives add/remove cycles) --------------------
    const posCache = new Map();

    // Cache for overview node positions specifically
    const overviewPosCache = new Map();

    // -- Active set tracking --------------------------------------------
    let currentActiveIds = new Set();
    let currentFocusKey = '__initial__';

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

    // -- Compute active set based on focus path -------------------------
    function computeActiveSet(fp) {
      const activeIds = new Set();
      const activeLinks = [];

      if (fp.length === 0) {
        // Overview: only depth-0 nodes, no links
        for (const [id, node] of allNodes) {
          if (node.depth === 0) activeIds.add(id);
        }
      } else {
        const focusedId = fp[fp.length - 1];
        activeIds.add(focusedId);
        const children = childrenOf.get(focusedId) || [];
        for (const child of children) {
          activeIds.add(child.id);
        }
        // Links between focused node and its children (fresh copies with string IDs
        // so d3 forceLink can resolve them against the current simulation nodes)
        for (const [, link] of allLinks) {
          const sid = typeof link.source === 'object' ? link.source.id : link.source;
          const tid = typeof link.target === 'object' ? link.target.id : link.target;
          if (activeIds.has(sid) && activeIds.has(tid)) {
            activeLinks.push({ source: sid, target: tid });
          }
        }
      }

      return { activeIds, activeLinks };
    }

    // -- Assign radii based on focus mode -------------------------------
    function assignRadii(fp) {
      if (fp.length === 0) {
        // Overview mode: all roots get large radius
        for (const [, node] of allNodes) {
          if (node.depth === 0) node.radius = RADIUS_OVERVIEW;
        }
      } else {
        const focusedId = fp[fp.length - 1];
        for (const [id, node] of allNodes) {
          if (id === focusedId) {
            node.radius = RADIUS_FOCUSED;
          } else {
            node.radius = RADIUS_CHILD;
          }
        }
      }
    }

    // -- SVG data-join with enter/exit ----------------------------------
    function rebindSVG(nodes, links, fp) {
      const focusedId = fp.length > 0 ? fp[fp.length - 1] : null;

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
          onNavigateRef.current(d.id);
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

      // Main circle -- radius set immediately so hover interactions stay consistent
      nodeEnter
        .append('circle')
        .attr('class', 'node-circle')
        .attr('r', (d) => d.radius)
        .attr('fill', (d) => nodeColor(d, lensRef.current))
        .attr('stroke', 'rgba(255,255,255,0.08)')
        .attr('stroke-width', 0.5)
        .attr('filter', (d) => (d.priority_band === 'critical' ? 'url(#glow)' : null))
        .style('opacity', 0)
        .transition('enter')
        .duration(350)
        .ease(d3.easeQuadOut)
        .style('opacity', 1);

      // Label -- always visible in overview (nodes are large enough)
      nodeEnter
        .append('text')
        .attr('class', 'node-label')
        .attr('x', (d) => d.radius + 6)
        .attr('y', 0)
        .attr('dy', '0.35em')
        .attr('fill', '#e6edf3')
        .attr('font-size', (d) => (d.id === focusedId ? '13px' : '11px'))
        .attr('font-weight', (d) => (d.id === focusedId ? 700 : 500))
        .attr('font-family', "'Figtree', sans-serif")
        .text((d) => (d.topic.length > 36 ? d.topic.slice(0, 34) + '...' : d.topic))
        .style('opacity', 0)
        .transition()
        .delay(200)
        .duration(250)
        .style('opacity', 1);

      // Subtitle (root topic name for non-root nodes)
      nodeEnter
        .append('text')
        .attr('class', 'node-subtitle')
        .attr('x', (d) => d.radius + 6)
        .attr('y', 14)
        .attr('fill', '#484f58')
        .attr('font-size', '8px')
        .attr('font-family', "'Figtree', sans-serif")
        .text((d) => (d.depth > 0 && d.id !== focusedId ? d.root_topic : ''))
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

      // Update existing nodes -- transition radius changes
      nodeSel.select('.node-circle')
        .transition()
        .duration(350)
        .attr('r', (d) => d.radius);

      nodeSel.select('.highlight-ring')
        .attr('r', (d) => d.radius + 5);

      nodeSel.select('.node-label')
        .attr('x', (d) => d.radius + 6);

      nodeSel.select('.node-subtitle')
        .attr('x', (d) => d.radius + 6);

      nodeGs = nodeEnter.merge(nodeSel);

      updateLabelVisibility();
    }

    // -- Label visibility -----------------------------------------------
    function updateLabelVisibility() {
      const k = currentKRef.current;
      const hl = highlightRef.current;
      const fp = focusPathRef.current;
      const isOverview = fp.length === 0;

      nodeGs.select('.node-label')
        .style('opacity', (d) => {
          if (isOverview) return 1; // always show in overview
          return d.radius * k > LABEL_PX_THRESHOLD ? 1 : 0;
        });

      nodeGs.select('.node-subtitle')
        .style('opacity', (d) => {
          if (isOverview) return 0;
          return d.radius * k > 20 && d.depth > 0 ? 0.55 : 0;
        });

      nodeGs.select('.highlight-ring')
        .style('opacity', (d) => (hl && hl.has(d.original_id) ? 1 : 0));
    }

    labelVisRef.current = updateLabelVisibility;

    // -- Reconcile simulation (switch active set) -----------------------
    function reconcile(fp) {
      const focusKey = fp.length === 0 ? '__overview__' : fp[fp.length - 1];
      if (focusKey === currentFocusKey) return;

      // If leaving overview, cache overview positions
      if (currentFocusKey === '__overview__') {
        for (const id of currentActiveIds) {
          const node = allNodes.get(id);
          if (node && node.x != null) {
            overviewPosCache.set(id, { x: node.x, y: node.y });
          }
        }
      }

      // Cache positions of all currently active nodes
      for (const id of currentActiveIds) {
        const node = allNodes.get(id);
        if (node && node.x != null) {
          posCache.set(id, { x: node.x, y: node.y });
        }
      }

      currentFocusKey = focusKey;
      assignRadii(fp);

      const { activeIds, activeLinks } = computeActiveSet(fp);

      // Position entering nodes
      if (fp.length === 0) {
        // Returning to overview -- restore cached overview positions
        for (const id of activeIds) {
          const node = allNodes.get(id);
          const cached = overviewPosCache.get(id);
          if (cached) {
            node.x = cached.x;
            node.y = cached.y;
          }
        }
      } else {
        const focusedId = fp[fp.length - 1];
        const focusedNode = allNodes.get(focusedId);

        // Focused node: use cached position or center
        const cachedFocus = posCache.get(focusedId) || overviewPosCache.get(focusedId);
        if (cachedFocus) {
          focusedNode.x = cachedFocus.x;
          focusedNode.y = cachedFocus.y;
        } else {
          focusedNode.x = width / 2;
          focusedNode.y = height / 2;
        }

        // Children: spawn from focused node position
        for (const id of activeIds) {
          if (id === focusedId) continue;
          const node = allNodes.get(id);
          const cached = posCache.get(id);
          if (cached) {
            node.x = cached.x;
            node.y = cached.y;
          } else {
            node.x = focusedNode.x + (Math.random() - 0.5) * 60;
            node.y = focusedNode.y + (Math.random() - 0.5) * 60;
          }
        }
      }

      currentActiveIds = activeIds;
      const activeNodes = [...activeIds].map((id) => allNodes.get(id));

      // IMPORTANT: set nodes before links so d3 forceLink can resolve IDs
      sim.nodes(activeNodes);

      // Reconfigure simulation forces based on mode
      if (fp.length === 0) {
        // Overview: moderate repulsion, strong center pull, no links
        sim.force('link').links([]);
        sim.force('charge').strength(-250);
        sim.force('center').strength(0.12);
        sim.force('collision').radius((d) => d.radius + 4);
      } else {
        // Focused view: parent + children
        sim.force('link')
          .links(activeLinks)
          .distance(120)
          .strength(0.5);
        sim.force('charge').strength(-200);
        sim.force('center').strength(0.04);
        sim.force('collision').radius((d) => d.radius + 4);
      }

      sim.alpha(0.5).restart();

      rebindSVG(activeNodes, activeLinks, fp);
    }

    reconcileRef.current = reconcile;

    // -- Simulation -----------------------------------------------------
    const initialFp = focusPathRef.current;
    assignRadii(initialFp);
    const { activeIds: initialActiveIds, activeLinks: initialLinks } = computeActiveSet(initialFp);
    const initialNodes = [...initialActiveIds].map((id) => allNodes.get(id));
    currentActiveIds = initialActiveIds;
    currentFocusKey = initialFp.length === 0 ? '__overview__' : initialFp[initialFp.length - 1];

    const isOverview = initialFp.length === 0;

    const sim = d3
      .forceSimulation(initialNodes)
      .force(
        'link',
        d3.forceLink(initialLinks)
          .id((d) => d.id)
          .distance(isOverview ? 200 : 120)
          .strength(isOverview ? 0 : 0.5),
      )
      .force(
        'charge',
        d3.forceManyBody().strength(isOverview ? -250 : -200),
      )
      .force('center', d3.forceCenter(width / 2, height / 2).strength(isOverview ? 0.12 : 0.04))
      .force('collision', d3.forceCollide().radius((d) => d.radius + (isOverview ? 4 : 4)))
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
    rebindSVG(initialNodes, initialLinks, initialFp);

    // -- Zoom -----------------------------------------------------------
    const zoom = d3.zoom()
      .scaleExtent([0.15, 12])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        currentKRef.current = event.transform.k;
        updateLabelVisibility();
      });

    svg.call(zoom);
    svg.call(
      zoom.transform,
      d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(0.75)
        .translate(-width / 2, -height / 2),
    );

    // Click background to go back
    svg.on('click', () => {
      if (focusPathRef.current.length > 0) {
        onBackRef.current();
      }
    });

    return () => {
      sim.stop();
    };
  }, [data]); // eslint-disable-line react-hooks/exhaustive-deps

  // -----------------------------------------------------------------------
  // Focus path change -- reconcile simulation
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (reconcileRef.current) {
      reconcileRef.current(focusPath);
    }
  }, [focusPath]);

  // -----------------------------------------------------------------------
  // Lens change -- update colors only (skip on initial mount)
  // -----------------------------------------------------------------------
  const lensInitRef = useRef(true);
  useEffect(() => {
    if (lensInitRef.current) {
      lensInitRef.current = false;
      return;
    }
    if (!svgRef.current || !data) return;
    // Sync latest scores into D3-bound node data before recoloring
    const scoreMap = new Map(data.nodes.map((n) => [n.id, n.student_mastery_score]));
    const circles = d3.select(svgRef.current).selectAll('.node-circle');
    circles.each(function (d) {
      if (scoreMap.has(d.id)) {
        d.student_mastery_score = scoreMap.get(d.id);
      }
    });
    circles
      .transition('lens')
      .duration(350)
      .attr('fill', (d) => nodeColor(d, lens))
      .attr('filter', (d) =>
        lens === 'emphasis' && d.priority_band === 'critical' ? 'url(#glow)' : null,
      );
  }, [lens, data]);

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
