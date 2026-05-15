export default function AttackPanel({
  targetUrl,
  setTargetUrl,
  targetFile,
  setTargetFile,
  scanMode,
  setScanMode,
  vulnLabel,
  setVulnLabel,
  scanStatus,
  webhookConnected,
  wsConnected,
  onLaunch,
  isScanning,
}) {
  console.log("[AttackPanel] scanStatus:", scanStatus, "scanning:", isScanning);

  const badgeClass = scanStatus.toLowerCase();

  return (
    <div className="attack-panel">
      <label className="terminal-label" htmlFor="scan-mode">
        SCAN MODE
      </label>
      <select
        id="scan-mode"
        className="terminal-select"
        value={scanMode}
        onChange={(e) => setScanMode(e.target.value)}
        disabled={isScanning}
      >
        <option value="dast">DAST (LIVE URL)</option>
        <option value="sast">SAST (LOCAL FILE)</option>
      </select>

      <label className="terminal-label" htmlFor="target-input">
        {scanMode === "dast" ? "TARGET URL" : "TARGET FILE PATH"}
      </label>
      {scanMode === "dast" ? (
        <input
          id="target-input"
          className="terminal-input"
          type="text"
          value={targetUrl}
          onChange={(e) => setTargetUrl(e.target.value)}
          disabled={isScanning}
        />
      ) : (
        <input
          id="target-input"
          className="terminal-input"
          type="text"
          value={targetFile}
          onChange={(e) => setTargetFile(e.target.value)}
          disabled={isScanning}
        />
      )}

      <label className="terminal-label" htmlFor="vuln-type">
        VULNERABILITY TYPE
      </label>
      <select
        id="vuln-type"
        className="terminal-select"
        value={vulnLabel}
        onChange={(e) => setVulnLabel(e.target.value)}
        disabled={isScanning}
      >
        <option value="SQL INJECTION">SQL INJECTION</option>
        <option value="COMMAND INJECTION">COMMAND INJECTION</option>
      </select>

      <button
        type="button"
        className={`launch-btn${isScanning ? " scanning" : ""}`}
        onClick={onLaunch}
        disabled={isScanning}
      >
        LAUNCH ATTACK
      </button>

      <div className="webhook-row">
        <span
          className={`webhook-dot${webhookConnected ? " connected" : ""}`}
          title={webhookConnected ? "Ngrok connected" : "Ngrok not connected"}
        />
        <span className="webhook-label">
          WEBHOOK {webhookConnected ? "ONLINE" : "OFFLINE"}
        </span>
      </div>

      <div className={`status-badge ${badgeClass}`}>{scanStatus}</div>

      <p className={`ws-indicator${wsConnected ? " live" : ""}`}>
        WS {wsConnected ? "CONNECTED" : "DISCONNECTED"}
      </p>
    </div>
  );
}
