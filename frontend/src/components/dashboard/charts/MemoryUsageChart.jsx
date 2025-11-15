import React from "react";
import {
  Chart as ChartJS,
  BarElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import styles from "./Charts.module.css";

ChartJS.register(BarElement, LinearScale, CategoryScale, Tooltip, Legend);

function MemoryUsageChart({ topVms }) {
  const labels = topVms.map((vm) => vm.name);
  const dataValues = topVms.map((vm) => vm.memory);

  const data = {
    labels,
    datasets: [
      {
        label: "Memory (GB)",
        data: dataValues,
        backgroundColor: ["#4ea1ff", "#7bd389", "#f2cc60", "#f29e6d", "#ff6b6b"],
        borderRadius: 8,
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
      x: { ticks: { color: "#9fb0d8" }, grid: { display: false } },
      y: {
        ticks: { color: "#9fb0d8", callback: (v) => `${v} GB` },
        grid: { color: "rgba(255,255,255,0.06)" },
        beginAtZero: true,
      },
    },
  };

  return (
    <div className={styles.chartCard}>
      <div className={styles.title}>Top 5 Memory Usage by VM</div>
      <Bar data={data} options={options} />
    </div>
  );
}

export default MemoryUsageChart;


