import React, { useState, useEffect, useRef } from "react";
import { Line, Pie } from "react-chartjs-2";
import 'chart.js/auto';
import styles from "./AlgorithmsVisualizer.module.css";

function AlgorithmsVisualizer({ steps, autoPlaySpeed = 1000 }) {
  const [currentStep, setCurrentStep] = useState(0);
  const intervalRef = useRef(null);

  const step = steps[currentStep] || {};

  // Frame visualization
  const frameBoxes = (step.memory || []).map((page, idx) => {
    let color = "lightgray";
    if (page === step.page) {
      color = step.action === "HIT" ? "lightgreen" : "lightcoral";
    }
    return (
      <div
        key={idx}
        className={styles.frameBox}
        style={{ backgroundColor: color }}
      >
        {page}
      </div>
    );
  });

  // Page Faults Line Chart
  const faultsData = {
    labels: steps.slice(0, currentStep + 1).map((_, i) => i + 1),
    datasets: [
      {
        label: "Page Faults",
        data: steps.slice(0, currentStep + 1).map(s => s.pageFaultsSoFar),
        borderColor: "red",
        fill: false,
      },
      {
        label: "Hits",
        data: steps.slice(0, currentStep + 1).map(s => s.hitsSoFar),
        borderColor: "green",
        fill: false,
      },
    ],
  };

  // Hits vs Misses Pie
  const pieData = {
    labels: ["Hits", "Misses"],
    datasets: [
      {
        data: [step.hitsSoFar || 0, step.pageFaultsSoFar || 0],
        backgroundColor: ["green", "red"],
      },
    ],
  };

  // Auto-play logic
  useEffect(() => {
    if (steps.length === 0) return;

    const startAutoPlay = () => {
      intervalRef.current = setInterval(() => {
        setCurrentStep(s => {
          if (s >= steps.length - 1) {
            clearInterval(intervalRef.current);
            return s;
          }
          return s + 1;
        });
      }, autoPlaySpeed);
    };

    startAutoPlay();

    return () => clearInterval(intervalRef.current);
  }, [steps, autoPlaySpeed]);

  const handlePrev = () => setCurrentStep(s => Math.max(s - 1, 0));
  const handleNext = () => setCurrentStep(s => Math.min(s + 1, steps.length - 1));

  return (
    <div className={styles.container}>
      <div className={styles.controls}>
        <button onClick={handlePrev}>Previous</button>
        <button onClick={handleNext}>Next</button>
        <span>Step: {currentStep + 1} / {steps.length}</span>
      </div>

      <div className={styles.frameContainer}>
        <h4>Memory Frames</h4>
        <div className={styles.frameRow}>{frameBoxes}</div>
        <div>
          <strong>Current Page:</strong> {step.page} ({step.action})
        </div>
      </div>

      <div className={styles.charts}>
        <div className={styles.chart}>
          <h4>Page Faults & Hits Over Time</h4>
          <Line data={faultsData} />
        </div>
        <div className={styles.chart}>
          <h4>Hits vs Misses</h4>
          <Pie data={pieData} />
        </div>
      </div>
    </div>
  );
}

export default AlgorithmsVisualizer;
