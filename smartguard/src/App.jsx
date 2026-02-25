import { useState, useEffect, useCallback } from "react";

const API_BASE = "http://localhost:5000";

const GRAFANA_PANELS = {
  alarm: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=2&from=now-6h&to=now&theme=dark",
  led: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=3&from=now-6h&to=now&theme=dark",
  dms: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=4&from=now-6h&to=now&theme=dark",
  entries: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=1&theme=dark",
  dus1: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=7&from=now-6h&to=now&theme=dark",
  ds1: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=5&from=now-6h&to=now&theme=dark",
  dpir1: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=6&from=now-6h&to=now&theme=dark",
  ds2: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=8&from=now-6h&to=now&theme=dark",
  dus2: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=10&from=now-6h&to=now&theme=dark",
  sd: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=9&from=now-6h&to=now&theme=dark",
  dpir2: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=13&from=now-6h&to=now&theme=dark",
  btn: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=11&from=now-6h&to=now&theme=dark",
  dht3: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=14&from=now-6h&to=now&theme=dark",
  gsg: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=12&from=now-6h&to=now&theme=dark",
  brgb: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=15&from=now-6h&to=now&theme=dark",
  dht1: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=20&from=now-6h&to=now&theme=dark",
  dht2: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=17&from=now-6h&to=now&theme=dark",
  ir: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=18&from=now-6h&to=now&theme=dark",
  lcd: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=19&from=now-6h&to=now&theme=dark",
  dpir3: "http://127.0.0.1:3001/d-solo/ad4btn7/odbrana?orgId=1&panelId=16&from=now-6h&to=now&theme=dark",
};

// ── Hooks ────────────────────────────────────────────────────────────────────

const useSystemState = () => {
  const [state, setState] = useState({
    people_count: 0,
    is_alarm_active: false,
    is_system_armed: false,
    alarm_reason: null,
    alarm_triggers: [],
    alarm_activated_at: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchState = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/system/state`);
      const data = await res.json();
      if (data.status === "success") {
        setState(data.data);
        setError(null);
      }
    } catch (e) {
      setError("Cannot connect to server");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 2000);
    return () => clearInterval(interval);
  }, [fetchState]);

  return { state, loading, error, refetch: fetchState };
};

const useSensorData = () => {
  const [sensors, setSensors] = useState({
    ds1: null, ds2: null,
    dus1: null, dus2: null,
    dpir1: false, dpir2: false, dpir3: false,
    ir: null, gsg: null, rgb: "off",
    dht: {
      "Bedroom DHT": { temp: null, hum: null },
      "Master Bedroom DHT": { temp: null, hum: null },
      "Kitchen DHT": { temp: null, hum: null },
    }
  });

  useEffect(() => {
    const fetchSensors = () =>
      fetch(`${API_BASE}/system/sensors`)
        .then(r => r.json())
        .then(d => { if (d.status === "success") setSensors(d.data); })
        .catch(() => {});

    fetchSensors();
    const id = setInterval(fetchSensors, 2000);
    return () => clearInterval(id);
  }, []);

  return sensors;
};

// ── Helpers ──────────────────────────────────────────────────────────────────

const fmtDoor = (val) => val === 1 ? "OPEN" : val === 0 ? "CLOSED" : "—";
const fmtNum = (val, dec = 1) => val !== null && val !== undefined ? Number(val).toFixed(dec) : "—";

// ── Base Components ───────────────────────────────────────────────────────────

const StatusDot = ({ active, color = "#22c55e", pulse = false }) => (
  <span style={{
    display: "inline-block",
    width: 8, height: 8,
    borderRadius: "50%",
    background: active ? color : "#1e293b",
    boxShadow: active ? `0 0 6px ${color}, 0 0 12px ${color}40` : "none",
    transition: "all 0.4s",
    flexShrink: 0,
    animation: active && pulse ? "pulse-dot 1.4s ease-in-out infinite" : "none",
  }} />
);

const Card = ({ children, style = {} }) => (
  <div style={{
    background: "rgba(10, 15, 28, 0.85)",
    border: "1px solid rgba(255,255,255,0.06)",
    borderRadius: 14,
    padding: "20px 22px",
    backdropFilter: "blur(16px)",
    ...style,
  }}>
    {children}
  </div>
);

const SectionLabel = ({ children }) => (
  <div style={{
    fontSize: 9,
    fontFamily: "'Space Mono', monospace",
    letterSpacing: "0.2em",
    textTransform: "uppercase",
    color: "#334155",
    marginBottom: 14,
    display: "flex",
    alignItems: "center",
    gap: 8,
  }}>
    <span style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.05)" }} />
    {children}
    <span style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.05)" }} />
  </div>
);

const SensorRow = ({ label, value, unit = "", active, color = "#22c55e" }) => (
  <div style={{
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "8px 0",
    borderBottom: "1px solid rgba(255,255,255,0.03)",
  }}>
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <StatusDot active={active} color={color} />
      <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 11, color: "#475569" }}>
        {label}
      </span>
    </div>
    <span style={{
      fontFamily: "'Space Mono', monospace",
      fontSize: 12,
      color: active ? "#e2e8f0" : "#334155",
      transition: "color 0.3s",
    }}>
      {value}{unit && value !== "—" ? unit : ""}
    </span>
  </div>
);

// ── Alarm Reason Box ──────────────────────────────────────────────────────────

const AlarmReasonBox = ({ reason, triggers, activatedAt }) => {
  if (!reason) return null;

  const timeStr = activatedAt
    ? new Date(activatedAt * 1000).toLocaleTimeString("sr-RS", {
        hour: "2-digit", minute: "2-digit", second: "2-digit",
      })
    : null;

  return (
    <div style={{
      marginTop: 12,
      padding: "12px 14px",
      background: "rgba(239,68,68,0.06)",
      border: "1px solid rgba(239,68,68,0.2)",
      borderRadius: 10,
      animation: "fadeIn 0.3s ease",
    }}>
      <div style={{
        fontSize: 9, color: "#7f1d1d", letterSpacing: "0.18em",
        textTransform: "uppercase", marginBottom: 8,
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <span>⚡ Uzrok alarma</span>
        {timeStr && <span style={{ color: "#450a0a" }}>{timeStr}</span>}
      </div>
      <div style={{
        fontSize: 12, color: "#fca5a5", lineHeight: 1.6,
        fontFamily: "'Space Mono', monospace",
        marginBottom: triggers?.length > 0 ? 10 : 0,
      }}>
        {reason}
      </div>
      {triggers?.length > 0 && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <span style={{
            fontSize: 9, color: "#7f1d1d", letterSpacing: "0.12em",
            alignSelf: "center", marginRight: 2,
          }}>
            SENZORI:
          </span>
          {triggers.map(s => (
            <span key={s} style={{
              padding: "3px 10px",
              background: "rgba(239,68,68,0.12)",
              border: "1px solid rgba(239,68,68,0.3)",
              borderRadius: 5, fontSize: 10, color: "#ef4444",
              fontFamily: "'Space Mono', monospace", letterSpacing: "0.08em",
            }}>
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Simulation Panel ──────────────────────────────────────────────────────────

const SCENARIOS = [
  {
    id: 1,
    icon: "💡",
    label: "Scenarij 1",
    desc: "DPIR1 pokret → DL uključen 10s",
    detail: "Simulira PIR senzor na ulaznim vratima (PI1). Backend objavljuje MQTT poruku na pi1/dpir1 sa vrijednošću 1, što uzrokuje paljenje door LED-a na 10 sekundi, a zatim automatsko gašenje.",
    color: "#22c55e",
    ledDuration: 10,
  },
];

const SimulationPanel = () => {
  const [scenarioInput, setScenarioInput] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(null);
  const [totalDuration, setTotalDuration] = useState(10);

  useEffect(() => {
    if (countdown === null) return;
    if (countdown <= 0) { setCountdown(null); return; }
    const t = setTimeout(() => setCountdown(c => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

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
      const ok = data.status === "success";
      setResult({ ok, msg: data.message });

      if (ok && scenario === 1) {
        const sc = SCENARIOS.find(s => s.id === 1);
        setTotalDuration(sc?.ledDuration || 10);
        setCountdown(sc?.ledDuration || 10);
      }
    } catch {
      setResult({ ok: false, msg: "Greška pri povezivanju sa serverom" });
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    flex: 1,
    background: "rgba(15,23,42,0.9)",
    border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: 8, padding: "9px 13px",
    color: "#e2e8f0", fontFamily: "'Space Mono', monospace",
    fontSize: 12, outline: "none", width: "100%",
  };

  return (
    <Card>
      <SectionLabel>Simulacija senzora</SectionLabel>

      {/* Input + button */}
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <input
          type="number"
          min={1}
          value={scenarioInput}
          onChange={e => { setScenarioInput(e.target.value); setResult(null); }}
          onKeyDown={e => e.key === "Enter" && runScenario()}
          placeholder="Unesite broj scenarija..."
          style={inputStyle}
        />
        <button
          onClick={runScenario}
          disabled={loading || !scenarioInput}
          style={{
            background: loading || !scenarioInput ? "#1e293b" : "#6366f1",
            border: "none", borderRadius: 8, padding: "9px 20px",
            color: loading || !scenarioInput ? "#334155" : "white",
            fontFamily: "'Space Mono', monospace", fontSize: 10,
            cursor: loading || !scenarioInput ? "not-allowed" : "pointer",
            letterSpacing: "0.1em", whiteSpace: "nowrap",
            opacity: loading ? 0.6 : 1, transition: "all 0.2s",
          }}
        >
          {loading ? "..." : "POKRENI"}
        </button>
      </div>

      {/* Scenario cards — clickable */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 14 }}>
        {SCENARIOS.map(s => {
          const selected = parseInt(scenarioInput) === s.id;
          return (
            <div
              key={s.id}
              onClick={() => { setScenarioInput(String(s.id)); setResult(null); }}
              style={{
                padding: "10px 14px",
                background: selected ? "rgba(99,102,241,0.08)" : "rgba(255,255,255,0.02)",
                border: `1px solid ${selected ? "rgba(99,102,241,0.3)" : "rgba(255,255,255,0.04)"}`,
                borderRadius: 8, cursor: "pointer", transition: "all 0.2s",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: selected ? 6 : 0 }}>
                <span style={{ fontSize: 16 }}>{s.icon}</span>
                <span style={{
                  fontFamily: "'Space Mono', monospace", fontSize: 10,
                  color: selected ? "#818cf8" : "#475569", letterSpacing: "0.1em",
                }}>
                  #{s.id} — {s.label}
                </span>
                <span style={{
                  marginLeft: "auto", padding: "2px 8px",
                  background: `${s.color}18`, border: `1px solid ${s.color}40`,
                  borderRadius: 4, fontSize: 9, color: s.color,
                  fontFamily: "'Space Mono', monospace",
                }}>
                  {s.desc}
                </span>
              </div>
              {selected && (
                <div style={{
                  fontSize: 10, color: "#475569",
                  fontFamily: "'Space Mono', monospace",
                  lineHeight: 1.6, paddingLeft: 26,
                }}>
                  {s.detail}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Countdown bar — visible while LED is on */}
      {countdown !== null && (
        <div style={{
          marginBottom: 12,
          padding: "10px 14px",
          background: "rgba(34,197,94,0.06)",
          border: "1px solid rgba(34,197,94,0.2)",
          borderRadius: 8,
          animation: "fadeIn 0.3s ease",
        }}>
          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8,
          }}>
            <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 10, color: "#22c55e", letterSpacing: "0.1em" }}>
              💡 DL aktivan
            </span>
            <span style={{ fontFamily: "'Space Mono', monospace", fontSize: 14, color: "#4ade80", fontWeight: "bold" }}>
              {countdown}s
            </span>
          </div>
          <div style={{ height: 3, background: "rgba(255,255,255,0.05)", borderRadius: 2 }}>
            <div style={{
              height: "100%",
              width: `${(countdown / totalDuration) * 100}%`,
              background: "linear-gradient(90deg, #22c55e, #4ade80)",
              borderRadius: 2,
              transition: "width 1s linear",
              boxShadow: "0 0 6px rgba(34,197,94,0.4)",
            }} />
          </div>
        </div>
      )}

      {/* Result message */}
      {result && (
        <div style={{
          padding: "9px 13px", borderRadius: 7, fontSize: 11,
          fontFamily: "'Space Mono', monospace",
          background: result.ok ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)",
          border: `1px solid ${result.ok ? "rgba(34,197,94,0.25)" : "rgba(239,68,68,0.25)"}`,
          color: result.ok ? "#22c55e" : "#ef4444",
          letterSpacing: "0.04em",
          animation: "fadeIn 0.3s ease",
        }}>
          {result.ok ? "✓" : "✗"} {result.msg}
        </div>
      )}
    </Card>
  );
};

// ── Alarm Panel ──────────────────────────────────────────────────────────────

const AlarmPanel = ({ state }) => {
  const [pin, setPin] = useState("");
  const [timerVal, setTimerVal] = useState("");
  const [nVal, setNVal] = useState("");
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState("info");
  const [rgbColor, setRgbColor] = useState("off");
  const [pinLoading, setPinLoading] = useState(false);

  const showMsg = (text, type = "info") => {
    setMsg(text); setMsgType(type);
    setTimeout(() => setMsg(""), 4000);
  };

  const submitPin = async () => {
    if (pin.length !== 4) return showMsg("PIN mora imati 4 cifre", "error");
    setPinLoading(true);
    try {
      const res = await fetch(`${API_BASE}/alarm/pin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin }),
      });
      const data = await res.json();
      showMsg(data.message || "PIN prihvaćen", data.correct ? "success" : "error");
      setPin("");
    } catch {
      showMsg("Greška pri slanju PIN-a", "error");
    } finally {
      setPinLoading(false);
    }
  };

  const setTimer = async () => {
    if (!timerVal) return showMsg("Unesite sekunde", "error");
    try {
      const res = await fetch(`${API_BASE}/timer/set`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seconds: parseInt(timerVal) }),
      });
      const data = await res.json();
      showMsg(data.message || "Timer postavljen", "success");
    } catch { showMsg("Greška", "error"); }
  };

  const setIncrement = async () => {
    if (!nVal) return showMsg("Unesite vrijednost", "error");
    try {
      const res = await fetch(`${API_BASE}/timer/increment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ increment: parseInt(nVal) }),
      });
      const data = await res.json();
      showMsg(data.message || "Inkrement postavljen", "success");
    } catch { showMsg("Greška", "error"); }
  };

  const setRgb = async (color) => {
    try {
      await fetch(`${API_BASE}/rgb/set`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ color }),
      });
      setRgbColor(color);
    } catch { showMsg("Greška RGB", "error"); }
  };

  const colors = [
    { id: "red", label: "Red", hex: "#ef4444" },
    { id: "green", label: "Green", hex: "#22c55e" },
    { id: "blue", label: "Blue", hex: "#3b82f6" },
    { id: "white", label: "White", hex: "#f8fafc" },
    { id: "yellow", label: "Yellow", hex: "#eab308" },
    { id: "purple", label: "Purple", hex: "#a855f7" },
    { id: "light blue", label: "Cyan", hex: "#67e8f9" },
    { id: "off", label: "Off", hex: "#334155" },
  ];

  const inputStyle = {
    flex: 1,
    background: "rgba(15,23,42,0.9)",
    border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: 8, padding: "9px 13px",
    color: "#e2e8f0", fontFamily: "'Space Mono', monospace",
    fontSize: 12, outline: "none", width: "100%",
  };

  const btnStyle = (bg, disabled = false) => ({
    background: disabled ? "#1e293b" : bg,
    border: "none", borderRadius: 8, padding: "9px 18px",
    color: disabled ? "#334155" : "white",
    fontFamily: "'Space Mono', monospace", fontSize: 10,
    cursor: disabled ? "not-allowed" : "pointer",
    letterSpacing: "0.1em", whiteSpace: "nowrap",
    opacity: disabled ? 0.6 : 1,
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

      {/* Alarm Status */}
      <Card style={{
        border: state.is_alarm_active
          ? "1px solid rgba(239,68,68,0.35)"
          : "1px solid rgba(255,255,255,0.06)",
        background: state.is_alarm_active ? "rgba(239,68,68,0.06)" : undefined,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18 }}>
          <StatusDot active={state.is_alarm_active} color="#ef4444" pulse={state.is_alarm_active} />
          <span style={{
            fontFamily: "'Space Mono', monospace", fontSize: 12,
            color: state.is_alarm_active ? "#ef4444" : "#475569",
            letterSpacing: "0.12em",
          }}>
            {state.is_alarm_active ? "⚠ ALARM AKTIVAN" : "SISTEM SIGURAN"}
          </span>
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            <StatusDot active={state.is_system_armed} color="#f59e0b" />
            <span style={{ fontSize: 10, color: "#475569", fontFamily: "'Space Mono', monospace" }}>
              {state.is_system_armed ? "ARMED" : "DISARMED"}
            </span>
          </div>
        </div>

        <AlarmReasonBox
          reason={state.alarm_reason}
          triggers={state.alarm_triggers}
          activatedAt={state.alarm_activated_at}
        />

        <div style={{ marginTop: state.is_alarm_active ? 16 : 0 }}>
          <SectionLabel>Deaktiviraj PIN-om</SectionLabel>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <input
            type="password"
            maxLength={4}
            value={pin}
            onChange={e => setPin(e.target.value.replace(/\D/g, ""))}
            onKeyDown={e => e.key === "Enter" && submitPin()}
            placeholder="• • • •"
            disabled={pinLoading}
            style={{
              ...inputStyle,
              fontSize: 20, letterSpacing: "0.4em",
              textAlign: "center", opacity: pinLoading ? 0.5 : 1,
            }}
          />
          <button
            onClick={submitPin}
            disabled={pinLoading || pin.length !== 4}
            style={btnStyle("#3b82f6", pinLoading || pin.length !== 4)}
          >
            {pinLoading ? "..." : "SEND"}
          </button>
        </div>

        {msg && (
          <div style={{
            marginTop: 10, padding: "8px 12px", borderRadius: 7,
            fontSize: 11, fontFamily: "'Space Mono', monospace",
            background: msgType === "error" ? "rgba(239,68,68,0.08)"
              : msgType === "success" ? "rgba(34,197,94,0.08)"
              : "rgba(255,255,255,0.03)",
            border: `1px solid ${msgType === "error" ? "rgba(239,68,68,0.25)"
              : msgType === "success" ? "rgba(34,197,94,0.25)"
              : "rgba(255,255,255,0.05)"}`,
            color: msgType === "error" ? "#ef4444"
              : msgType === "success" ? "#22c55e" : "#64748b",
            letterSpacing: "0.05em",
          }}>
            {msg}
          </div>
        )}
      </Card>

      {/* People Count */}
      <Card>
        <SectionLabel>Osobe u objektu</SectionLabel>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <div style={{ fontSize: 56, fontFamily: "'Space Mono', monospace", color: "#e2e8f0", fontWeight: "bold", lineHeight: 1 }}>
            {state.people_count}
          </div>
          <span style={{ fontSize: 12, color: "#334155", fontFamily: "'Space Mono', monospace" }}>osoba</span>
        </div>
        <div style={{ marginTop: 12, height: 3, background: "rgba(255,255,255,0.05)", borderRadius: 2 }}>
          <div style={{
            height: "100%",
            width: `${Math.min(state.people_count * 10, 100)}%`,
            background: "linear-gradient(90deg, #3b82f6, #6366f1)",
            borderRadius: 2,
            transition: "width 0.6s cubic-bezier(0.4,0,0.2,1)",
          }} />
        </div>
      </Card>

      {/* Kitchen Timer */}
      <Card>
        <SectionLabel>Kuhinjski tajmer</SectionLabel>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input type="number" value={timerVal} onChange={e => setTimerVal(e.target.value)} placeholder="sekundi" style={inputStyle} />
          <button onClick={setTimer} style={btnStyle("#10b981")}>SET</button>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input type="number" value={nVal} onChange={e => setNVal(e.target.value)} placeholder="inkrement dugmeta (s)" style={inputStyle} />
          <button onClick={setIncrement} style={btnStyle("#6366f1")}>SET N</button>
        </div>
      </Card>

      {/* RGB Control */}
      <Card>
        <SectionLabel>RGB svjetlo</SectionLabel>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {colors.map(({ id, label, hex }) => (
            <button
              key={id}
              onClick={() => setRgb(id)}
              style={{
                background: rgbColor === id ? hex : "rgba(15,23,42,0.9)",
                border: `1px solid ${hex}50`,
                borderRadius: 7, padding: "6px 11px",
                color: rgbColor === id && id === "white" ? "#0f172a" : "#cbd5e1",
                fontFamily: "'Space Mono', monospace", fontSize: 10,
                cursor: "pointer", letterSpacing: "0.05em", transition: "all 0.2s",
                boxShadow: rgbColor === id ? `0 0 10px ${hex}60` : "none",
              }}
            >
              {label.toUpperCase()}
            </button>
          ))}
        </div>
      </Card>
    </div>
  );
};

// ── Grafana Panel ─────────────────────────────────────────────────────────────

const GrafanaPanel = ({ src, title, height = 220 }) => (
  <div>
    <div style={{
      fontSize: 9, fontFamily: "'Space Mono', monospace",
      letterSpacing: "0.18em", textTransform: "uppercase",
      color: "#334155", marginBottom: 8,
    }}>
      {title}
    </div>
    <div style={{ borderRadius: 10, overflow: "hidden", border: "1px solid rgba(255,255,255,0.05)", height }}>
      <iframe src={src} width="100%" height={height} frameBorder="0" style={{ display: "block" }} title={title} />
    </div>
  </div>
);

// ── Webcam ────────────────────────────────────────────────────────────────────

const WebcamPanel = () => {
  const streamUrl = "http://192.168.107.144:8080/?action=stream";
  const [offline, setOffline] = useState(false);

  return (
    <Card>
      <SectionLabel>Live Camera Feed</SectionLabel>
      <div style={{
        borderRadius: 10, overflow: "hidden", background: "#050a14",
        aspectRatio: "16/9", display: "flex", alignItems: "center", justifyContent: "center",
        border: "1px solid rgba(255,255,255,0.05)",
      }}>
        {!offline ? (
          <img
            src={streamUrl}
            alt="Webcam stream"
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            onError={() => setOffline(true)}
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10, color: "#1e293b", fontFamily: "'Space Mono', monospace", fontSize: 11 }}>
            <span style={{ fontSize: 36 }}>📷</span>
            <span>Camera offline</span>
            <span style={{ fontSize: 9, color: "#0f172a" }}>mjpeg @ {streamUrl}</span>
          </div>
        )}
      </div>
    </Card>
  );
};

// ── Main Dashboard ────────────────────────────────────────────────────────────

export default function SmartHomeDashboard() {
  const { state, loading, error } = useSystemState();
  const sensors = useSensorData();
  const [activeTab, setActiveTab] = useState("overview");
  const [clock, setClock] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "grafana", label: "Analytics" },
    { id: "camera", label: "Camera" },
    { id: "control", label: "Control" },
  ];

  const dht = sensors.dht || {};
  const bedroom = dht["Bedroom DHT"] || {};
  const masterBedroom = dht["Master Bedroom DHT"] || {};
  const kitchen = dht["Kitchen DHT"] || {};

  return (
    <div style={{
      minHeight: "100vh",
      background: "#030712",
      color: "#e2e8f0",
      fontFamily: "'Space Mono', monospace",
      position: "relative",
      overflow: "hidden",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input:focus { border-color: rgba(59,130,246,0.5) !important; box-shadow: 0 0 0 2px rgba(59,130,246,0.1) !important; }
        button:hover:not(:disabled) { opacity: 0.82; transform: translateY(-1px); transition: all 0.15s; }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 2px; }
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; box-shadow: 0 0 6px #ef4444, 0 0 12px #ef444440; }
          50% { opacity: 0.4; box-shadow: 0 0 2px #ef4444; }
        }
        @keyframes alarm-flash {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Background grid */}
      <div style={{
        position: "fixed", inset: 0, pointerEvents: "none",
        backgroundImage: `
          linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px)
        `,
        backgroundSize: "48px 48px",
      }} />

      {/* Ambient glow */}
      <div style={{
        position: "fixed", top: -300, left: "10%", width: 700, height: 700,
        borderRadius: "50%", pointerEvents: "none", transition: "background 1.5s",
        background: state.is_alarm_active
          ? "radial-gradient(circle, rgba(239,68,68,0.05) 0%, transparent 65%)"
          : "radial-gradient(circle, rgba(59,130,246,0.04) 0%, transparent 65%)",
      }} />
      <div style={{
        position: "fixed", bottom: -200, right: "5%", width: 500, height: 500,
        borderRadius: "50%", pointerEvents: "none",
        background: "radial-gradient(circle, rgba(99,102,241,0.03) 0%, transparent 65%)",
      }} />

      <div style={{ position: "relative", maxWidth: 1440, margin: "0 auto", padding: "0 28px" }}>

        {/* Header */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "22px 0", borderBottom: "1px solid rgba(255,255,255,0.05)", marginBottom: 28,
        }}>
          <div>
            <div style={{ fontSize: 9, color: "#1e293b", letterSpacing: "0.25em", marginBottom: 5 }}>
              IOT SMART HOME SYSTEM
            </div>
            <h1 style={{ fontSize: 20, fontWeight: "normal", letterSpacing: "0.08em", color: "#94a3b8" }}>
              CONTROL <span style={{ color: "#e2e8f0" }}>CENTER</span>
            </h1>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>
            {error && (
              <div style={{
                display: "flex", alignItems: "center", gap: 6, padding: "6px 12px",
                background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
                borderRadius: 7, fontSize: 10, color: "#ef4444",
              }}>
                ⚠ {error}
              </div>
            )}

            {/* Alarm reason header badge */}
            {state.is_alarm_active && state.alarm_reason && (
              <div
                title={state.alarm_reason}
                style={{
                  padding: "5px 12px",
                  background: "rgba(239,68,68,0.08)",
                  border: "1px solid rgba(239,68,68,0.22)",
                  borderRadius: 7, fontSize: 9, color: "#fca5a5",
                  maxWidth: 260, overflow: "hidden",
                  textOverflow: "ellipsis", whiteSpace: "nowrap",
                  fontFamily: "'Space Mono', monospace",
                  letterSpacing: "0.04em", cursor: "default",
                }}>
                ⚡ {state.alarm_reason}
              </div>
            )}

            {/* People badge */}
            <div style={{
              padding: "6px 14px",
              background: state.people_count > 0 ? "rgba(59,130,246,0.08)" : "rgba(10,15,28,0.9)",
              border: `1px solid ${state.people_count > 0 ? "rgba(59,130,246,0.25)" : "rgba(255,255,255,0.05)"}`,
              borderRadius: 7, fontSize: 11,
              color: state.people_count > 0 ? "#93c5fd" : "#334155",
              fontFamily: "'Space Mono', monospace",
            }}>
              👥 {state.people_count}
            </div>

            {/* Alarm badge */}
            <div style={{
              display: "flex", alignItems: "center", gap: 7, padding: "6px 14px",
              background: state.is_alarm_active ? "rgba(239,68,68,0.1)" : "rgba(10,15,28,0.9)",
              border: `1px solid ${state.is_alarm_active ? "rgba(239,68,68,0.3)" : "rgba(255,255,255,0.05)"}`,
              borderRadius: 7, transition: "all 0.4s",
              animation: state.is_alarm_active ? "alarm-flash 1.2s ease-in-out infinite" : "none",
            }}>
              <StatusDot active={state.is_alarm_active} color="#ef4444" pulse={state.is_alarm_active} />
              <span style={{ fontSize: 10, letterSpacing: "0.12em", color: state.is_alarm_active ? "#ef4444" : "#334155" }}>
                {state.is_alarm_active ? "ALARM" : "SECURE"}
              </span>
            </div>

            {/* Armed badge */}
            <div style={{
              display: "flex", alignItems: "center", gap: 7, padding: "6px 14px",
              background: "rgba(10,15,28,0.9)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 7,
            }}>
              <StatusDot active={state.is_system_armed} color="#f59e0b" />
              <span style={{ fontSize: 10, letterSpacing: "0.12em", color: state.is_system_armed ? "#f59e0b" : "#334155" }}>
                {state.is_system_armed ? "ARMED" : "DISARMED"}
              </span>
            </div>

            {/* Clock */}
            <div style={{
              padding: "6px 14px", background: "rgba(10,15,28,0.9)",
              border: "1px solid rgba(255,255,255,0.05)", borderRadius: 7,
              fontSize: 12, color: "#334155", letterSpacing: "0.05em",
            }}>
              {clock.toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 3, marginBottom: 24 }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "7px 18px",
                background: activeTab === tab.id ? "rgba(59,130,246,0.1)" : "transparent",
                border: activeTab === tab.id ? "1px solid rgba(59,130,246,0.3)" : "1px solid transparent",
                borderRadius: 7,
                color: activeTab === tab.id ? "#93c5fd" : "#334155",
                fontFamily: "'Space Mono', monospace", fontSize: 10,
                cursor: "pointer", letterSpacing: "0.12em", transition: "all 0.2s",
              }}
            >
              {tab.label.toUpperCase()}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW TAB ── */}
        {activeTab === "overview" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>

            <Card>
              <SectionLabel>System Status</SectionLabel>
              <SensorRow label="Alarm" value={state.is_alarm_active ? "ACTIVE" : "OFF"} active={state.is_alarm_active} color="#ef4444" />
              <SensorRow label="Armed" value={state.is_system_armed ? "YES" : "NO"} active={state.is_system_armed} color="#f59e0b" />
              <SensorRow label="People" value={state.people_count} active={state.people_count > 0} color="#3b82f6" />
              <SensorRow label="RGB Color" value={sensors.rgb?.toUpperCase() || "—"} active={sensors.rgb !== "off"} color="#a855f7" />
              {state.is_alarm_active && state.alarm_reason && (
                <div style={{ marginTop: 10 }}>
                  <AlarmReasonBox
                    reason={state.alarm_reason}
                    triggers={state.alarm_triggers}
                    activatedAt={state.alarm_activated_at}
                  />
                </div>
              )}
            </Card>

            <Card>
              <SectionLabel>PI1 — Front Door</SectionLabel>
              <SensorRow label="DS1 Door Sensor" value={fmtDoor(sensors.ds1)} active={sensors.ds1 === 1} color={sensors.ds1 === 1 ? "#ef4444" : "#22c55e"} />
              <SensorRow label="DPIR1 Motion" value={sensors.dpir1 ? "DETECTED" : "CLEAR"} active={sensors.dpir1} color="#f59e0b" />
              <SensorRow label="DUS1 Distance" value={fmtNum(sensors.dus1, 0)} unit=" cm" active={sensors.dus1 !== null && sensors.dus1 < 60} color="#3b82f6" />
              <SensorRow label="DB Buzzer" value={state.is_alarm_active ? "ON" : "OFF"} active={state.is_alarm_active} color="#ef4444" />
              <SensorRow label="DL Door Light" value={sensors.dl ? "ON" : "OFF"} active={!!sensors.dl} color="#22c55e" />
            </Card>

            <Card>
              <SectionLabel>PI2 — Kitchen</SectionLabel>
              <SensorRow label="DS2 Door Sensor" value={fmtDoor(sensors.ds2)} active={sensors.ds2 === 1} color={sensors.ds2 === 1 ? "#ef4444" : "#22c55e"} />
              <SensorRow label="DPIR2 Motion" value={sensors.dpir2 ? "DETECTED" : "CLEAR"} active={sensors.dpir2} color="#f59e0b" />
              <SensorRow label="DUS2 Distance" value={fmtNum(sensors.dus2, 0)} unit=" cm" active={sensors.dus2 !== null && sensors.dus2 < 60} color="#3b82f6" />
              <SensorRow label="DHT3 Temp" value={fmtNum(kitchen.temp)} unit="°C" active={kitchen.temp !== null} color="#f97316" />
              <SensorRow label="DHT3 Humidity" value={fmtNum(kitchen.hum)} unit="%" active={kitchen.hum !== null} color="#06b6d4" />
              <SensorRow label="GSG Gyroscope" value={sensors.gsg !== null ? fmtNum(sensors.gsg, 2) : "—"} unit={sensors.gsg !== null ? " g" : ""} active={sensors.gsg !== null && sensors.gsg > 0.5} color="#a855f7" />
            </Card>

            <Card>
              <SectionLabel>PI3 — Bedroom</SectionLabel>
              <SensorRow label="DHT1 Temp" value={fmtNum(bedroom.temp)} unit="°C" active={bedroom.temp !== null} color="#f97316" />
              <SensorRow label="DHT1 Humidity" value={fmtNum(bedroom.hum)} unit="%" active={bedroom.hum !== null} color="#06b6d4" />
              <SensorRow label="DHT2 Temp" value={fmtNum(masterBedroom.temp)} unit="°C" active={masterBedroom.temp !== null} color="#f97316" />
              <SensorRow label="DHT2 Humidity" value={fmtNum(masterBedroom.hum)} unit="%" active={masterBedroom.hum !== null} color="#06b6d4" />
              <SensorRow label="DPIR3 Motion" value={sensors.dpir3 ? "DETECTED" : "CLEAR"} active={sensors.dpir3} color="#f59e0b" />
              <SensorRow label="IR Remote" value={sensors.ir ? String(sensors.ir).toUpperCase() : "—"} active={sensors.ir !== null} color="#6366f1" />
              <SensorRow label="BRGB Light" value={sensors.rgb?.toUpperCase() || "—"} active={sensors.rgb !== "off"} color="#a855f7" />
            </Card>

            <Card style={{ gridColumn: "span 2" }}>
              <SectionLabel>Entry / Exit Counter</SectionLabel>
              <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
                <div>
                  <div style={{ fontSize: 80, lineHeight: 1, fontWeight: "bold", color: "#e2e8f0", letterSpacing: "-0.02em" }}>
                    {state.people_count}
                  </div>
                  <div style={{ fontSize: 11, color: "#334155", marginTop: 6, fontFamily: "'Space Mono', monospace" }}>
                    osoba trenutno unutra
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ height: 4, background: "rgba(255,255,255,0.04)", borderRadius: 2, overflow: "hidden" }}>
                    <div style={{
                      height: "100%",
                      width: `${Math.min(state.people_count * 10, 100)}%`,
                      background: "linear-gradient(90deg, #3b82f6, #6366f1)",
                      borderRadius: 2,
                      transition: "width 0.6s cubic-bezier(0.4,0,0.2,1)",
                      boxShadow: "0 0 8px rgba(99,102,241,0.4)",
                    }} />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginTop: 20 }}>
                    {[
                      { label: "Vrata 1", val: fmtDoor(sensors.ds1), alert: sensors.ds1 === 1 },
                      { label: "Vrata 2", val: fmtDoor(sensors.ds2), alert: sensors.ds2 === 1 },
                      { label: "Motion", val: (sensors.dpir1 || sensors.dpir2 || sensors.dpir3) ? "ACTIVE" : "CLEAR", alert: sensors.dpir1 || sensors.dpir2 || sensors.dpir3 },
                    ].map(({ label, val, alert }) => (
                      <div key={label} style={{
                        padding: "10px 14px",
                        background: alert ? "rgba(239,68,68,0.06)" : "rgba(255,255,255,0.02)",
                        border: `1px solid ${alert ? "rgba(239,68,68,0.2)" : "rgba(255,255,255,0.04)"}`,
                        borderRadius: 8, transition: "all 0.3s",
                      }}>
                        <div style={{ fontSize: 9, color: "#334155", letterSpacing: "0.15em", marginBottom: 4 }}>{label.toUpperCase()}</div>
                        <div style={{ fontSize: 12, color: alert ? "#ef4444" : "#475569", fontFamily: "'Space Mono', monospace" }}>{val}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>

          </div>
        )}

        {/* ── GRAFANA TAB ── */}
        {activeTab === "grafana" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card style={{ gridColumn: "span 2" }}><GrafanaPanel src={GRAFANA_PANELS.entries} title="People Count (Entries)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.led} title="Door Light (DL)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.alarm} title="ALARM (DB)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.dms} title="Door Membrane Switch (DMS)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.dus1} title="Door Ultrasonic Sensor (DUS1)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.ds1} title="Door Sensor (DS1)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.dpir1} title="Door Motion Sensor (DPIR1)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.dpir2} title="Door Motion Sensor (DPIR2)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.dus2} title="Door Ultrasonic Sensor (DUS2)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.ds2} title="Door Sensor (DS2)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.gsg} title="Gyroscope (GSG)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.btn} title="Kitchen Button (BTN)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.sd} title="Kitchen 4 Digit 7 Segment Display Timer (4SD)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.dht3} title="Kitchen Digital Humidity and Temperature Sensor (DHT3)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.brgb} title="Bedroom RGB (BRGB)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.dht1} title="Master Bedroom DHT" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.dht2} title="Bedroom DHT2" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.ir} title="Bedroom Infrared (IR)" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.lcd} title="LCD Display" height={250} /></Card>
            <Card><GrafanaPanel src={GRAFANA_PANELS.dpir3} title="Living Room Motion Sensor (DPIR3)" height={250} /></Card>
          </div>
        )}

        {/* ── CAMERA TAB ── */}
        {activeTab === "camera" && (
          <div style={{ maxWidth: 960, margin: "0 auto" }}>
            <WebcamPanel />
          </div>
        )}

        {/* ── CONTROL TAB ── */}
        {activeTab === "control" && (
          <div style={{ maxWidth: 580, margin: "0 auto", display: "flex", flexDirection: "column", gap: 14 }}>
            <AlarmPanel state={state} />
            <SimulationPanel />
          </div>
        )}

        {/* Footer */}
        <div style={{
          marginTop: 40, paddingTop: 20, paddingBottom: 28,
          borderTop: "1px solid rgba(255,255,255,0.03)",
          display: "flex", justifyContent: "space-between", alignItems: "center",
          fontSize: 9, color: "#1e293b", letterSpacing: "0.12em",
        }}>
          <span>IOT SMART HOME SYSTEM</span>
          <span>FLASK · MQTT · INFLUXDB · GRAFANA</span>
        </div>

      </div>
    </div>
  );
}