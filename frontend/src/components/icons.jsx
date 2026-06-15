// Inline SVG icon set (stroke = currentColor). Keeps the bundle dependency-free.
const S = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' }

export const IconLive = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M12 2v6m0 8v6M4.9 4.9l4.2 4.2m5.8 5.8 4.2 4.2M2 12h6m8 0h6M4.9 19.1l4.2-4.2m5.8-5.8 4.2-4.2" /></svg>
)
export const IconCalls = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M5 4h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" /><path d="M8 9h8M8 13h6M8 17h4" /></svg>
)
export const IconKnowledge = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M4 5a2 2 0 0 1 2-2h13v18H6a2 2 0 0 1-2-2V5Z" /><path d="M19 17H6a2 2 0 0 0-2 2" /></svg>
)
export const IconExperiments = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M9 3h6M10 3v6l-5 8a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-8V3" /><path d="M7.5 14h9" /></svg>
)
export const IconPersonas = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><circle cx="9" cy="8" r="3" /><path d="M3 20a6 6 0 0 1 12 0" /><path d="M16 5.5a3 3 0 0 1 0 5M21 20a6 6 0 0 0-5-5.9" /></svg>
)
export const IconOverview = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></svg>
)
export const IconPhone = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M6.6 3h3l1.5 4-2 1.2a12 12 0 0 0 4.7 4.7l1.2-2 4 1.5v3a2 2 0 0 1-2.2 2A16 16 0 0 1 4.6 5.2 2 2 0 0 1 6.6 3Z" /></svg>
)
export const IconMic = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><rect x="9" y="2" width="6" height="12" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" /></svg>
)
export const IconStop = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
)
export const IconBack = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M15 18l-6-6 6-6" /></svg>
)
export const IconSearch = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.2-3.2" /></svg>
)
export const IconArrow = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M5 12h14M13 6l6 6-6 6" /></svg>
)
// decision action icons
export const IconAsk = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M9 9a3 3 0 1 1 4 2.8c-.8.4-1 .9-1 1.7M12 17h.01" /></svg>
)
export const IconAnswer = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M21 12a8 8 0 0 1-11.5 7.2L4 20l.8-5.5A8 8 0 1 1 21 12Z" /></svg>
)
export const IconClose = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M20 6 9 17l-5-5" /></svg>
)
export const IconEscalate = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><path d="M12 3 2 20h20L12 3Z" /><path d="M12 10v4M12 17h.01" /></svg>
)
export const IconDisqualify = (p) => (
  <svg viewBox="0 0 24 24" {...S} {...p}><circle cx="12" cy="12" r="9" /><path d="m15 9-6 6M9 9l6 6" /></svg>
)
