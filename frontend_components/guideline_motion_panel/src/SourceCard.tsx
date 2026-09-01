import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Citation } from "./types";
import { StatusBadge } from "./StatusBadge";

interface Props {
  citation: Citation;
  index: number;
  reducedMotion: boolean;
}

export function SourceCard({ citation, index, reducedMotion }: Props) {
  const [expanded, setExpanded] = useState(false);
  const isSuperseded = citation.status === "Superseded" || citation.status === "Historical";

  return (
    <motion.div
      initial={reducedMotion ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reducedMotion ? 0 : 0.3, delay: reducedMotion ? 0 : index * 0.06 }}
      style={{
        border: "1px solid #e1e4e8",
        borderRadius: 10,
        padding: "12px 14px",
        marginBottom: 8,
        background: "#ffffff",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: "#1c2530" }}>
            {citation.title} <span style={{ fontWeight: 500, color: "#5b6570" }}>— v{citation.version}</span>
          </div>
          <div style={{ fontSize: 12, color: "#5b6570", marginTop: 2 }}>
            {citation.document_type} · Effective {citation.effective_date}
            {citation.section ? ` · ${citation.section}` : ""}
          </div>
        </div>
        <StatusBadge status={citation.status} reducedMotion={reducedMotion} />
      </div>

      <div style={{ fontSize: 12, color: "#5b6570", fontStyle: "italic", marginTop: 6 }}>
        Why this source: {citation.relevance_explanation}
      </div>

      {isSuperseded && (
        <div
          style={{
            marginTop: 8,
            fontSize: 12,
            color: "#9a6300",
            background: "#fff4e5",
            border: "1px solid #f2d190",
            borderRadius: 6,
            padding: "6px 8px",
          }}
        >
          ⚠️ This source is {citation.status.toLowerCase()} and is shown because historical guidance
          was requested or relevant.
        </div>
      )}

      <button
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        style={{
          marginTop: 8,
          background: "none",
          border: "none",
          color: "#0b3d5c",
          fontSize: 12,
          fontWeight: 600,
          cursor: "pointer",
          padding: 0,
        }}
      >
        {expanded ? "Hide excerpt ▲" : "Show supporting excerpt ▼"}
      </button>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="excerpt"
            initial={reducedMotion ? false : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={reducedMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
            transition={{ duration: reducedMotion ? 0 : 0.25, ease: "easeInOut" }}
            style={{ overflow: "hidden" }}
          >
            <div
              style={{
                marginTop: 8,
                fontSize: 12,
                color: "#1c2530",
                background: "#f7f8fa",
                borderRadius: 6,
                padding: "8px 10px",
                fontFamily: "monospace",
              }}
            >
              chunk_id: {citation.chunk_id}
              {citation.excerpt ? (
                <div style={{ marginTop: 6, fontFamily: "inherit" }}>{citation.excerpt}</div>
              ) : null}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
