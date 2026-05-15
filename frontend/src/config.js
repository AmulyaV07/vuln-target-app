export const API_BASE = "http://localhost:8001";
export const WS_URL = "ws://localhost:8001/ws";

export function vulnTypeToApi(label) {
  if (label === "COMMAND INJECTION") return "cmdi";
  return "sqli";
}

export function formatTime(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-GB", { hour12: false });
  } catch {
    return "--:--:--";
  }
}
