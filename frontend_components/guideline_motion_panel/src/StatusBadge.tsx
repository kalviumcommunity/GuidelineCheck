import { motion } from "framer-motion";
import type { GuidanceStatus } from "./types";

const STATUS_STYLE: Record<GuidanceStatus, { bg: string; fg: string; border: string; icon: string }> = {
  Current: { bg: "#e6f4ea", fg: "#1e7a34", border: "#bfe3c8", icon: "✅" },
  Superseded: { bg: "#fff4e5", fg: "#9a6300", border: "#f2d190", icon: "⚠️" },
  Historical: { bg: "#eef0f2", fg: "#54606b", border: "#d5dade", icon: "🕘" },
  Draft: { bg: "#eef2ff", fg: "#3949ab", border: "#c9d0f5", icon: "📝" },
};

interface Props {
  status: GuidanceStatus;
  reducedMotion: boolean;
}

export function StatusBadge({ status, reducedMotion }: Props) {
  const style = STATUS_STYLE[status] ?? STATUS_STYLE.Historical;

  return (
    <motion.span
      initial={reducedMotion ? false : { opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: reducedMotion ? 0 : 0.25, ease: "easeOut" }}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        fontSize: 12,
        fontWeight: 700,
        padding: "3px 10px",
        borderRadius: 999,
        background: style.bg,
        color: style.fg,
        border: `1px solid ${style.border}`,
        whiteSpace: "nowrap",
      }}
    >
      <span aria-hidden="true">{style.icon}</span>
      {status}
    </motion.span>
  );
}
