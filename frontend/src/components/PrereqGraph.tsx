import dagre from "@dagrejs/dagre";
import { Background, Controls, MarkerType, ReactFlow, type Edge, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useMemo } from "react";

import type { CatalogResponse } from "../api/types";

const EDGE_STYLE: Record<string, { color: string; dash?: string; label: string }> = {
  PREREQUISITE: { color: "#dc2626", label: "tiên quyết" },
  PRE_COURSE: { color: "#2563eb", label: "học trước" },
  CO_REQUISITE: { color: "#16a34a", dash: "6 3", label: "song hành" },
};

export default function PrereqGraph({
  catalog,
  visible,
  focus,
  onFocus,
}: {
  catalog: CatalogResponse;
  visible: Set<string>;
  focus: string | null;
  onFocus: (id: string | null) => void;
}) {
  const { nodes, edges } = useMemo(() => {
    const deps = catalog.dependencies.filter(
      (d) => d.type !== "MUTUALLY_EXCLUSIVE" && visible.has(d.source) && visible.has(d.target),
    );
    // tổ tiên của môn đang chọn (chuỗi điều kiện)
    const chain = new Set<string>();
    if (focus) {
      const stack = [focus];
      while (stack.length) {
        const cur = stack.pop()!;
        if (chain.has(cur)) continue;
        chain.add(cur);
        for (const d of deps) if (d.target === cur) stack.push(d.source);
      }
    }
    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: "LR", nodesep: 18, ranksep: 60 });
    g.setDefaultEdgeLabel(() => ({}));
    // chỉ vẽ môn có quan hệ trong phạm vi đang xem (môn đứng riêng làm đồ thị rối)
    const linked = new Set(deps.flatMap((d) => [d.source, d.target]));
    const ids = [...visible].filter((id) => linked.has(id));
    for (const id of ids) g.setNode(id, { width: 170, height: 46 });
    for (const d of deps) g.setEdge(d.source, d.target);
    dagre.layout(g);
    const byId = Object.fromEntries(catalog.courses.map((c) => [c.course.id, c.course]));
    const nodes: Node[] = ids.map((id) => {
      const p = g.node(id);
      const hi = chain.has(id);
      return {
        id,
        position: { x: p.x - 85, y: p.y - 23 },
        data: { label: `${id} · ${byId[id]?.name ?? ""}` },
        style: {
          width: 170,
          fontSize: 11,
          padding: 4,
          borderRadius: 8,
          border: hi ? "2px solid #dc2626" : "1px solid #cbd5e1",
          background: id === focus ? "#fee2e2" : hi ? "#fff7ed" : "#fff",
          opacity: focus && !hi ? 0.45 : 1,
        },
      };
    });
    const edges: Edge[] = deps.map((d, i) => {
      const st = EDGE_STYLE[d.type] ?? EDGE_STYLE.PRE_COURSE;
      const hi = chain.has(d.source) && chain.has(d.target);
      return {
        id: `e${i}`,
        source: d.source,
        target: d.target,
        markerEnd: { type: MarkerType.ArrowClosed, color: st.color },
        style: { stroke: st.color, strokeDasharray: st.dash, strokeWidth: hi ? 2.5 : 1, opacity: focus && !hi ? 0.25 : 1 },
      };
    });
    return { nodes, edges };
  }, [catalog, visible, focus]);

  const standalone = [...visible].length - nodes.length;
  return (
    <div className="relative h-[560px] rounded-xl border border-slate-200 bg-white" data-testid="prereq-graph">
      {standalone > 0 && (
        <div className="absolute top-2 right-3 z-10 rounded bg-white/90 px-2 py-1 text-[11px] text-slate-500">
          {standalone} môn không có điều kiện trong phạm vi này được ẩn
        </div>
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        nodesDraggable={false}
        onNodeClick={(_, n) => onFocus(n.id === focus ? null : n.id)}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} color="#f1f5f9" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

export function EdgeLegend() {
  return (
    <div className="flex flex-wrap gap-4 text-xs text-slate-500">
      {Object.values(EDGE_STYLE).map((s) => (
        <span key={s.label} className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-6" style={{ background: s.color }} />
          {s.label}
        </span>
      ))}
    </div>
  );
}
