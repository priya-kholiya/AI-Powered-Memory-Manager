import React, { useEffect, useMemo, useState } from "react";
import styles from "./Dashboard.module.css";
import StatCard from "./StatCard";
import VMList from "./VMList";
import CpuHistoryChart from "./charts/CpuHistoryChart";
import MemoryUsageChart from "./charts/MemoryUsageChart";
import OsDistributionChart from "./charts/OsDistributionChart";

const MOCK_RESPONSE = {
  summary: {
    activeVMs: 7,
    totalVMs: 10,
    totalUsers: 12,
    overallCpuUsage: 62.5,
    overallMemoryUsageGB: 48.2,
    totalMemoryGB: 128,
  },
  vmList: [
    { id: "vm-001", name: "AI-Trainer-1", os: "Ubuntu 22.04", user: "ml_team", cpu: 85.2, memory: 16.4, status: "Running" },
    { id: "vm-002", name: "Red-Team-Node", os: "Kali Linux 2024.2", user: "sec_ops", cpu: 45.0, memory: 8.1, status: "Running" },
    { id: "vm-003", name: "Dev-Sandbox-A", os: "Kali Linux 2024.2", user: "dev_user_1", cpu: 12.7, memory: 4.0, status: "Running" },
    { id: "vm-004", name: "QA-Testbed", os: "Ubuntu 22.04", user: "qa_user", cpu: 22.1, memory: 6.2, status: "Idle" },
    { id: "vm-005", name: "AI-Trainer-2", os: "Ubuntu 22.04", user: "ml_team", cpu: 91.5, memory: 24.8, status: "Running" },
  ],
  cpuHistory: [
    { time: "10:50:00", usage: 58 },
    { time: "10:50:05", usage: 60 },
    { time: "10:50:10", usage: 61 },
    { time: "10:50:15", usage: 65 },
    { time: "10:50:20", usage: 62.5 },
  ],
};

async function fetchVitals() {
  try {
    const res = await fetch("http://192.168.56.10:5000/api/vitals");


    if (!res.ok) {
      throw new Error("Backend error");
    }

    return await res.json();

  } catch (err) {
    console.error("Vitals fetch failed:", err);
    return MOCK_RESPONSE; // fallback so dashboard keeps working
  }
}

function Dashboard() {
  const [data, setData] = useState(MOCK_RESPONSE);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      const payload = await fetchVitals();
      if (mounted) {
        setData(payload);
        setLoading(false);
      }
    };

    load();
    const timer = setInterval(load, 3000);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  // Avoid crash if backend returns unexpected structure
  const safeVmList = Array.isArray(data?.vmList) ? data.vmList : [];

  const osDistribution = useMemo(() => {
    const counts = safeVmList.reduce((acc, vm) => {
      acc[vm.os] = (acc[vm.os] || 0) + 1;
      return acc;
    }, {});

    const total = safeVmList.length || 1;

    return Object.fromEntries(
      Object.entries(counts).map(([k, v]) => [k, Math.round((v / total) * 100)])
    );
  }, [safeVmList]);

  const topMemoryVms = useMemo(
    () => [...safeVmList].sort((a, b) => b.memory - a.memory).slice(0, 5),
    [safeVmList]
  );

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <div className={styles.title}>Dynamic AI Memory Manager Dashboard</div>
          <div className={styles.subtitle}>
            Live resource utilization across virtual machines
          </div>
        </div>

        <div className={styles.footerNote}>
          Backend endpoint: <code>/api/vitals</code>
        </div>
      </div>

      <div className={styles.cardsRow}>
        <StatCard title="Active VMs" value={data.summary.activeVMs} />
        <StatCard title="Overall CPU" value={data.summary.overallCpuUsage.toFixed(1)} unit="%" />
        <StatCard
          title="Memory Usage"
          value={data.summary.overallMemoryUsageGB.toFixed(1)}
          unit={`GB / ${data.summary.totalMemoryGB} GB`}
        />
        <StatCard title="Users Logged In" value={data.summary.totalUsers} />
      </div>

      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <div className={styles.panelTitle}>Active Virtual Machines</div>
          <div className={styles.subtitle}>
            Showing {safeVmList.length} of {data.summary.totalVMs}
          </div>
        </div>

        {loading ? <div>Loading...</div> : <VMList vms={safeVmList} />}
      </div>

      <div className={styles.chartsGrid}>
        <CpuHistoryChart history={data.cpuHistory} />
        <OsDistributionChart distribution={osDistribution} />
      </div>

      <div className={styles.panel}>
        <MemoryUsageChart topVms={topMemoryVms} />
      </div>
    </div>
  );
}

export default Dashboard;
