import { motion } from "framer-motion";
import type { MotionPanelPayload } from "./types";
import { StatusBadge } from "./StatusBadge";
import { ConfidenceIndicator } from "./ConfidenceIndicator";
import { SourceCard } from "./SourceCard";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

interface Props {
  payload: MotionPanelPayload;
}

function bannerMeta(payload: MotionPanelPayload) {
  if (payload.is_abstention) {
    return { bg: "#fdeaea", fg: "#b3261e", border: "#f3bcbc", text: "No sufficient supporting guidance found", icon: "🚫" };
  }
  if (payload.current_guidance_found) {
    return { bg: "#e6f4ea", fg: "#1e7a34", border: "#bfe3c8", text: "Current guidance identified", icon: "✅" };
  }
  return {
    bg: "#fff4e5",
    fg: "#9a6300",
    border: "#f2d190",
    text: "No current guidance found; showing superseded or historical material",
    icon: "⚠️",
  };
}

export default function GuidancePanel({ payload }: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const banner = bannerMeta(payload);

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, sans-serif", padding: 4 }}>
      {/* Guidance status banner */}
      <motion.div
        key={banner.text}
        initial={reducedMotion ? false : { opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: reducedMotion ? 0 : 0.3 }}
        style={{
          background: banner.bg,
          color: banner.fg,
          border: `1px solid ${banner.border}`,
          borderRadius: 10,
          padding: "10px 14px",
          fontWeight: 700,
          fontSize: 14,
          marginBottom: 10,
        }}
      >
        {banner.icon} {banner.text}
      </motion.div>

      {/* Answer card */}
      <motion.div
        initial={reducedMotion ? false : { opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: reducedMotion ? 0 : 0.35, delay: reducedMotion ? 0 : 0.05 }}
        style={{
          background: "#ffffff",
          border: "1px solid #e1e4e8",
          borderRadius: 12,
          padding: "16px 18px",
          marginBottom: 10,
          boxShadow: "0 1px 2px rgba(16,24,40,0.04)",
        }}
      >
        <div style={{ fontSize: 15, lineHeight: 1.55, color: "#1c2530", whiteSpace: "pre-wrap" }}>
          {payload.answer_text}
        </div>

        <div
          style={{
            marginTop: 12,
            paddingTop: 10,
            borderTop: "1px dashed #e1e4e8",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 8,
          }}
        >
          <ConfidenceIndicator label={payload.confidence_label} reducedMotion={reducedMotion} />
          <span style={{ fontSize: 11, color: "#5b6570", fontWeight: 600 }}>
            {payload.generation_mode === "llm" ? "LLM-generated" : "Extractive (no LLM configured)"}
          </span>
        </div>
        <div style={{ marginTop: 8, fontSize: 11, color: "#5b6570" }}>🛈 {payload.safety_notice}</div>
      </motion.div>

      {/* Sources */}
      {payload.citations.length > 0 && (
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#1c2530", marginBottom: 6 }}>Sources</div>
          {payload.citations.map((c, i) => (
            <SourceCard key={c.chunk_id} citation={c} index={i} reducedMotion={reducedMotion} />
          ))}
        </div>
      )}
    </div>
  );
}
