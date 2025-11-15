import React from "react";
import styles from "./VMList.module.css";

function usageClass(percentage) {
  if (percentage < 50) return styles.barGreen;
  if (percentage < 80) return styles.barYellow;
  return styles.barRed;
}

function VMList({ vms }) {
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead className={styles.thead}>
          <tr>
            <th>VM Name</th>
            <th>OS</th>
            <th>User</th>
            <th>CPU Usage</th>
            <th>Memory Usage</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {vms.map((vm) => (
            <tr key={vm.id} className={styles.row}>
              <td>
                <span className={styles.badge}>
                  <span role="img" aria-label="vm">
                    🖥️
                  </span>
                  <span>{vm.name}</span>
                </span>
              </td>
              <td>{vm.os}</td>
              <td>{vm.user}</td>
              <td>
                <div className={styles.metricCell}>
                  <div className={styles.barWrap}>
                    <div
                      className={`${styles.bar} ${usageClass(vm.cpu)}`}
                      style={{ width: `${Math.min(vm.cpu, 100)}%` }}
                    />
                  </div>
                  <span>{vm.cpu.toFixed(1)}%</span>
                </div>
              </td>
              <td>
                <div className={styles.metricCell}>
                  <div className={styles.barWrap}>
                    <div
                      className={`${styles.bar} ${usageClass(
                        Math.min((vm.memory / 64) * 100, 100)
                      )}`}
                      style={{ width: `${Math.min((vm.memory / 64) * 100, 100)}%` }}
                    />
                  </div>
                  <span>{vm.memory.toFixed(1)} GB</span>
                </div>
              </td>
              <td>
                <span
                  className={`${styles.status} ${
                    vm.status === "Running" ? styles.statusRunning : styles.statusIdle
                  }`}
                >
                  {vm.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default VMList;


