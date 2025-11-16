import React from "react";
import styles from "./StatCard.module.css";

function StatCard({ title, value, unit,link }) {
  return (
    <div className={styles.card}>
      <div className={styles.label}>{title}</div>
      <div className={styles.valueRow}>
        <div className={styles.value}>{value}</div>
        {unit ? <div className={styles.unit}>{unit}</div> : null}
        {link && <div className={styles.cardLink}>{link}</div>}

      </div>
    </div>
  );
}

export default StatCard;


