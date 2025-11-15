import React from "react";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import styles from "./Charts.module.css";

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Filler
);

function CpuHistoryChart({ history }) {
  const labels = history.map((h) => h.time);
  const dataValues = history.map((h) => h.usage);

  const data = {
    labels,
    datasets: [
      {
        label: "CPU Usage (%)",
        data: dataValues,
        borderColor: "#4ea1ff",
        backgroundColor: "rgba(78, 161, 255, 0.15)",
        pointRadius: 2,
        fill: true,
        tension: 0.35,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { labels: { color: "#cfe0ff" } },
      tooltip: { mode: "index", intersect: false },
    },
    scales: {
      x: { ticks: { color: "#9fb0d8" }, grid: { color: "rgba(255,255,255,0.06)" } },
      y: {
        ticks: { color: "#9fb0d8", callback: (v) => `${v}%` },
        grid: { color: "rgba(255,255,255,0.06)" },
        min: 0,
        max: 100,
      },
    },
  };

  return (
    <div className={styles.chartCard}>
      <div className={styles.title}>Overall CPU Usage (last 60s)</div>
      <Line data={data} options={options} />
    </div>
  );
}

export default CpuHistoryChart;


