import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE, WS_URL, vulnTypeToApi } from "./config";
import AgentLog from "./components/AgentLog";
import AttackPanel from "./components/AttackPanel";
import BreachAlert from "./components/BreachAlert";
import JournalView from "./components/JournalView";
import StatusBar from "./components/StatusBar";
import RemediationPanel from "./components/RemediationPanel";

function statusToLabel(status) {
  const map = {
    idle: "IDLE",
    running: "SCANNING",
    breached: "BREACHED",
    failed: "FAILED",
  };
  return map[status] || status.toUpperCase();
}

export default function App() {
  const [targetUrl, setTargetUrl] = useState("http://localhost:5001");
  const [targetFile, setTargetFile] = useState("C:\\Users\\amuly\\OneDrive\\Desktop\\divayjainki\\target\\app.py");
  const [scanMode, setScanMode] = useState("dast");
  const [vulnLabel, setVulnLabel] = useState("SQL INJECTION");
  const [messages, setMessages] = useState([]);
  const [journalEntries, setJournalEntries] = useState([]);
  const [scanStatus, setScanStatus] = useState("IDLE");
  const [rawStatus, setRawStatus] = useState("idle");
  const [wsConnected, setWsConnected] = useState(false);
  const [webhookConnected] = useState(false);
  const [breachTrigger, setBreachTrigger] = useState(0);
  const [currentAgent, setCurrentAgent] = useState("—");
  const [phase, setPhase] = useState("STANDBY");
  const [patchCode, setPatchCode] = useState(null);
  const [verificationStatus, setVerificationStatus] = useState(null);

  const wsRef = useRef(null);
  const pollRef = useRef(null);

  const isScanning = rawStatus === "running";

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/status`);
      const data = await res.json();
      console.log("[App] status poll:", data);
      setRawStatus(data.status);
      setScanStatus(statusToLabel(data.status));
      if (data.status === "running") setPhase("RED SWARM ACTIVE");
      else if (data.status === "breached") setPhase("BREACH");
      else if (data.status === "failed") setPhase("EXHAUSTED");
      else setPhase("STANDBY");
    } catch (err) {
      console.error("[App] status fetch failed:", err);
    }
  }, []);

  const fetchJournal = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/journal`);
      const data = await res.json();
      setJournalEntries(data.entries || []);
    } catch (err) {
      console.error("[App] journal fetch failed:", err);
    }
  }, []);

  const handleWsMessage = useCallback((event) => {
    try {
      const data = JSON.parse(event.data);
      console.log("[App] ws message:", data);

      setMessages((prev) => [...prev, data]);
      setCurrentAgent(data.agent || "—");

      if (data.level === "breach") {
        setBreachTrigger(Date.now());
        setScanStatus("BREACHED");
        setRawStatus("breached");
        setPhase("BREACH");
      }
      
      if (data.message && data.message.startsWith("REMEDIATION_DATA|")) {
        const parts = data.message.split("|");
        const isEffective = parts[1] === "True";
        const code = parts.slice(2).join("|");
        setVerificationStatus(isEffective);
        setPatchCode(code);
        setPhase("REMEDIATION COMPLETE");
      }

      if (data.agent === "ALPHA") setPhase("RECON");
      if (data.agent === "BETA") setPhase("EXPLOIT");
      if (data.agent === "GAMMA") setPhase("ANALYSIS");
      if (data.agent === "DELTA") setPhase("PATCHING");
      if (data.agent === "EPSILON") setPhase("VERIFYING");
    } catch (err) {
      console.error("[App] ws parse error:", err);
    }
  }, []);

  useEffect(() => {
    console.log("[App] connecting WebSocket:", WS_URL);
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[App] WebSocket connected");
      setWsConnected(true);
    };

    ws.onmessage = handleWsMessage;

    ws.onclose = () => {
      console.log("[App] WebSocket closed");
      setWsConnected(false);
    };

    ws.onerror = (err) => {
      console.error("[App] WebSocket error:", err);
      setWsConnected(false);
    };

    fetchStatus();

    return () => {
      ws.close();
    };
  }, [handleWsMessage, fetchStatus]);

  useEffect(() => {
    if (isScanning || rawStatus === "breached") {
      fetchJournal();
      pollRef.current = setInterval(() => {
        fetchJournal();
        fetchStatus();
      }, 3000);
    } else {
      fetchJournal();
    }

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [isScanning, rawStatus, fetchJournal, fetchStatus]);

  const handleLaunch = async () => {
    console.log("[App] launching attack:", targetUrl, vulnLabel);
    setMessages([]);
    setJournalEntries([]);
    setScanStatus("SCANNING");
    setRawStatus("running");
    setPhase("RED SWARM ACTIVE");
    setPatchCode(null);
    setVerificationStatus(null);

    try {
      const res = await fetch(`${API_BASE}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_url: targetUrl.trim(),
          target_file: targetFile.trim(),
          scan_mode: scanMode,
          vuln_type: vulnTypeToApi(vulnLabel),
        }),
      });
      const data = await res.json();
      console.log("[App] scan response:", data);

      if (data.status === "already_running") {
        setScanStatus("SCANNING");
        return;
      }

      fetchStatus();
      fetchJournal();
    } catch (err) {
      console.error("[App] scan failed:", err);
      setScanStatus("FAILED");
      setRawStatus("failed");
    }
  };

  return (
    <div className="war-room">
      <div className="scanline-overlay" aria-hidden="true" />
      <div className="scanline-beam" aria-hidden="true" />

      <BreachAlert trigger={breachTrigger} />

      <div className="panels">
        <aside className="panel panel-left">
          <h1 className="hero-title">PROJECT ZERO-DAY</h1>
          <AttackPanel
            targetUrl={targetUrl}
            setTargetUrl={setTargetUrl}
            targetFile={targetFile}
            setTargetFile={setTargetFile}
            scanMode={scanMode}
            setScanMode={setScanMode}
            vulnLabel={vulnLabel}
            setVulnLabel={setVulnLabel}
            scanStatus={scanStatus}
            webhookConnected={webhookConnected}
            wsConnected={wsConnected}
            onLaunch={handleLaunch}
            isScanning={isScanning}
          />
          <StatusBar
            currentAgent={currentAgent}
            phase={phase}
            attemptCount={journalEntries.length}
          />
        </aside>

        <main className="panel panel-center">
          <h2 className="panel-title">AGENT FEED</h2>
          <AgentLog messages={messages} />
        </main>

        <aside className="panel panel-right">
          <h2 className="panel-title">ATTACK JOURNAL</h2>
          <JournalView entries={journalEntries} />
          {patchCode && (
            <RemediationPanel 
              patchCode={patchCode} 
              verificationStatus={verificationStatus} 
            />
          )}
        </aside>
      </div>
    </div>
  );
}
