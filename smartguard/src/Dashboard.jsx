const SimulationPanel = () => {
  const [scenarioInput, setScenarioInput] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runScenario = async () => {
    const scenario = parseInt(scenarioInput);
    if (!scenario) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/simulate/sensor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario }),
      });
      const data = await res.json();
      setResult({ ok: data.status === "success", msg: data.message });
    } catch {
      setResult({ ok: false, msg: "Greška pri povezivanju sa serverom" });
    } finally {
      setLoading(false);
    }
  };

  const scenarios = [
    { id: 1, label: "Scenarij 1", desc: "DPIR1 detektuje pokret → DL pali 10s" },
  ];

  return (
    <Card>
      <SectionLabel>Simulacija senzora</SectionLabel>
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <input
          type="number"
          min={1}
          value={scenarioInput}
          onChange={e => setScenarioInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && runScenario()}
          placeholder="Broj scenarija..."
          style={{
            flex: 1,
            background: "rgba(15,23,42,0.9)",
            border: "1px solid rgba(255,255,255,0.07)",
            borderRadius: 8,
            padding: "9px 13px",
            color: "#e2e8f0",
            fontFamily: "'Space Mono', monospace",
            fontSize: 12,
            outline: "none",
          }}
        />
        <button
          onClick={runScenario}
          disabled={loading || !scenarioInput}
          style={{
            background: loading || !scenarioInput ? "#1e293b" : "#6366f1",
            border: "none", borderRadius: 8, padding: "9px 18px",
            color: loading || !scenarioInput ? "#334155" : "white",
            fontFamily: "'Space Mono', monospace", fontSize: 10,
            cursor: loading || !scenarioInput ? "not-allowed" : "pointer",
            letterSpacing: "0.1em", opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "..." : "POKRENI"}
        </button>
      </div>

      {/* Scenario reference */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: result ? 12 : 0 }}>
        {scenarios.map(s => (
          <div
            key={s.id}
            onClick={() => setScenarioInput(String(s.id))}
            style={{
              padding: "8px 12px",
              background: scenarioInput == s.id ? "rgba(99,102,241,0.1)" : "rgba(255,255,255,0.02)",
              border: `1px solid ${scenarioInput == s.id ? "rgba(99,102,241,0.3)" : "rgba(255,255,255,0.04)"}`,
              borderRadius: 7, cursor: "pointer", transition: "all 0.2s",
              display: "flex", alignItems: "center", gap: 12,
            }}
          >
            <span style={{
              fontFamily: "'Space Mono', monospace", fontSize: 10,
              color: scenarioInput == s.id ? "#818cf8" : "#334155",
              minWidth: 80,
            }}>
              #{s.id}
            </span>
            <span style={{ fontSize: 11, color: "#475569" }}>{s.desc}</span>
          </div>
        ))}
      </div>

      {result && (
        <div style={{
          padding: "8px 12px", borderRadius: 7, fontSize: 11,
          fontFamily: "'Space Mono', monospace",
          background: result.ok ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)",
          border: `1px solid ${result.ok ? "rgba(34,197,94,0.25)" : "rgba(239,68,68,0.25)"}`,
          color: result.ok ? "#22c55e" : "#ef4444",
          letterSpacing: "0.05em",
        }}>
          {result.msg}
        </div>
      )}
    </Card>
  );
};