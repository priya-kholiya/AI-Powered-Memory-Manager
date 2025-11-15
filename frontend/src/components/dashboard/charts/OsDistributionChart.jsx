import React from "react";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { Pie } from "react-chartjs-2";
import styles from "./Charts.module.css";

ChartJS.register(ArcElement, Tooltip, Legend);

function OsDistributionChart({ distribution }) {
  const labels = Object.keys(distribution);
  const dataValues = Object.values(distribution);

  const data = {
    labels,
    datasets: [
      {
        label: "OS Distribution",
        data: dataValues,
        backgroundColor: ["#4ea1ff", "#7bd389", "#f2cc60", "#f29e6d", "#ff6b6b", "#b084f4"],
        borderColor: "#0f1524",
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { position: "bottom", labels: { color: "#cfe0ff" } },
      tooltip: {
        callbacks: {
          label: (ctx) => ` ${ctx.label}: ${ctx.raw ?? 0}%`,
        },
      },
    },
  };

  return (
    <div className={styles.chartCard}>
      <div className={styles.title}>OS Distribution</div>
      <Pie data={data} options={options} />
    </div>
  );
}

export default OsDistributionChart;


