import React, { useState } from "react";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from "chart.js";
import styles from "./Dashboard.module.css";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const API_URL = "http://192.168.56.10:5000/api/algorithm/run";

function Algorithms() {
  const [algorithm, setAlgorithm] = useState("FIFO");
  const [frames, setFrames] = useState(3);
  const [referenceString, setReferenceString] = useState("7 0 1 2 0 3 0 4 2 3 0 3 2");
  const [processId, setProcessId] = useState("process-1");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runAlgorithm = async () => {
    setLoading(true); setError(""); setResult(null);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ algorithm, frames: Number(frames), referenceString, processId }),
      });
      const data = await res.json();
      if (!data.ok) setError(data.error || "Execution failed");
      else setResult(data.result);
    } catch {
      setError("Unable to connect to backend");
    }

    setLoading(false);
  };

  const chartData = () => {
    if (!result) return {};
    const labels = result.steps.map((s, i) => `Step ${i + 1}`);
    const datasets = result.steps[0].memory.map((_, idx) => ({
      label: `Frame ${idx + 1}`,
      data: result.steps.map(s => s.memory[idx] ?? null),
      backgroundColor: `rgba(${50 + idx * 50}, 99, 132, 0.6)`
    }));
    return { labels, datasets };
  };

  return (
    <div className={styles.container}>
      <h2>Page Replacement Simulator</h2>

      <div className={styles.panel}>
        <label>Algorithm</label>
        <select value={algorithm} onChange={e => setAlgorithm(e.target.value)}>
          <option value="FIFO">FIFO</option>
          <option value="LRU">LRU</option>
          <option value="OPTIMAL">OPTIMAL</option>
        </select>

        <label>Frames</label>
        <input type="number" value={frames} min={1} onChange={e => setFrames(e.target.value)} />

        <label>Reference String</label>
        <textarea value={referenceString} onChange={e => setReferenceString(e.target.value)} rows={2} />

        <label>Process ID</label>
        <input type="text" value={processId} onChange={e => setProcessId(e.target.value)} />

        <button onClick={runAlgorithm}>{loading ? "Running..." : "Run Algorithm"}</button>
        {error && <div style={{ color: "red" }}>{error}</div>}
      </div>

      {result && (
        <div className={styles.panel}>
          <h3>Page Faults: {result.pageFaults} | Hits: {result.hits}</h3>

          <Bar data={chartData()} options={{ responsive: true, plugins: { legend: { position: "top" } } }} />

          <table className={styles.table}>
            <thead>
              <tr>
                <th>Page</th>
                <th>Action</th>
                <th>Memory</th>
                <th>Faults So Far</th>
                <th>Hits So Far</th>
              </tr>
            </thead>
            <tbody>
              {result.steps.map((step, idx) => (
                <tr key={idx}>
                  <td>{step.page}</td>
                  <td style={{ color: step.action === "MISS" ? "red" : "green" }}>{step.action}</td>
                  <td>{step.memory.join(", ")}</td>
                  <td>{step.pageFaultsSoFar}</td>
                  <td>{step.hitsSoFar}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Algorithms;
