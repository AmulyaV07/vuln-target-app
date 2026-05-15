import React from "react";

export default function RemediationPanel({ patchCode, verificationStatus }) {
  if (!patchCode) return null;

  const isVerified = verificationStatus === true;
  const isFailed = verificationStatus === false;

  return (
    <div className="remediation-panel">
      <h2 className="panel-title">REMEDIATION STATUS</h2>
      
      <div className={`remediation-status ${isVerified ? "success" : isFailed ? "failed" : "pending"}`}>
        {isVerified && "PATCH EFFECTIVE ✓"}
        {isFailed && "PATCH FAILED ✗"}
        {verificationStatus === null && "VERIFYING PATCH..."}
      </div>

      <div className="patch-code-container">
        <div className="patch-code-header">PATCH CODE [DELTA AGENT]</div>
        <pre className="patch-code-block">
          <code>{patchCode}</code>
        </pre>
      </div>
    </div>
  );
}
