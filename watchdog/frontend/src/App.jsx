import { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function App() {
  const [containers, setContainers] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || "";

  // ===============================
  // Fetch container list + history
  // ===============================
  const fetchData = async () => {
    try {
      const [statusRes, historyRes] = await Promise.all([
        axios.get(`${API_URL}/api/status`),
        axios.get(`${API_URL}/api/history`),
      ]);
      setContainers(statusRes.data.containers || []);
      setHistory(historyRes.data.data || []);
    } catch (err) {
      console.error("❌ Error fetching data", err);
    } finally {
      setLoading(false);
    }
  };

  // ===============================
  // Fetch logs + stats for selected
  // ===============================
  const fetchDetails = async (name) => {
    try {
      const [logsRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/container/${name}/logs?lines=50`),
        axios.get(`${API_URL}/api/container/${name}/stats`),
      ]);
      setLogs(logsRes.data.logs || []);
      setStats(statsRes.data || null);
    } catch (err) {
      console.error("❌ Error fetching details", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selected) {
      fetchDetails(selected.name);
      const interval = setInterval(() => fetchDetails(selected.name), 5000);
      return () => clearInterval(interval);
    }
  }, [selected]);

  // ===============================
  // UI Components
  // ===============================
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen text-xl font-semibold text-gray-400">
        Loading Watchdog Dashboard...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      {/* Header */}
      <header className="mb-8 text-center">
        <h1 className="text-3xl md:text-4xl font-bold text-green-400">
          🐾 Docker Watchdog Dashboard
        </h1>
        <p className="text-gray-400 mt-2">
          Real-time container monitoring, logs, and auto-healing.
        </p>
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        {/* ==================== Container Table ==================== */}
        <div className="bg-gray-800 p-4 rounded-2xl shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-200">
            Container Status
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="text-left py-2 px-2">Name</th>
                  <th className="text-left py-2 px-2">Status</th>
                  <th className="text-left py-2 px-2">Image</th>
                </tr>
              </thead>
              <tbody>
                {containers.map((c) => (
                  <tr
                    key={c.name}
                    className={`border-b border-gray-700 hover:bg-gray-700/50 cursor-pointer ${
                      selected?.name === c.name ? "bg-gray-700/70" : ""
                    }`}
                    onClick={() => setSelected(c)}
                  >
                    <td className="py-2 px-2">{c.name}</td>
                    <td
                      className={`py-2 px-2 font-semibold ${
                        c.status === "running"
                          ? "text-green-400"
                          : "text-red-400"
                      }`}
                    >
                      {c.status}
                    </td>
                    <td className="py-2 px-2 text-gray-400">{c.image}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ==================== Uptime History ==================== */}
        <div className="bg-gray-800 p-4 rounded-2xl shadow-lg">
          <h2 className="text-xl font-semibold mb-4 text-gray-200">
            Uptime History
          </h2>
          {history.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="timestamp" hide />
                <YAxis />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #333",
                    color: "#fff",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="service"
                  stroke="#60a5fa"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400">No history recorded yet.</p>
          )}
        </div>
      </div>

      {/* ==================== Container Detail Section ==================== */}
      {selected && (
        <div className="mt-8 bg-gray-800 p-4 rounded-2xl shadow-lg">
          {/* === Header + Action Buttons === */}
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-200">
              📦 Container:{" "}
              <span className="text-green-400">{selected.name}</span>
            </h2>

            <div className="flex gap-3">
              <button
                onClick={async () => {
                  await axios.post(
                    `${API_URL}/api/container/${selected.name}/start`
                  );
                  fetchDetails(selected.name);
                }}
                className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded-lg text-sm"
              >
                ▶ Start
              </button>

              <button
                onClick={async () => {
                  await axios.post(
                    `${API_URL}/api/container/${selected.name}/stop`
                  );
                  fetchDetails(selected.name);
                }}
                className="bg-red-600 hover:bg-red-500 px-3 py-1 rounded-lg text-sm"
              >
                ⏸ Stop
              </button>

              <button
                onClick={async () => {
                  await axios.post(
                    `${API_URL}/api/container/${selected.name}/restart`
                  );
                  fetchDetails(selected.name);
                }}
                className="bg-yellow-600 hover:bg-yellow-500 px-3 py-1 rounded-lg text-sm"
              >
                🔁 Restart
              </button>

              <button
                className="text-red-400 hover:text-red-300"
                onClick={() => setSelected(null)}
              >
                ✖ Close
              </button>
            </div>
          </div>

          {/* === Stats Section === */}
          {stats ? (
            <div className="grid md:grid-cols-3 gap-4 mb-4">
              <div className="bg-gray-900 rounded-xl p-4">
                <h3 className="text-gray-400 text-sm">CPU Usage</h3>
                <p className="text-2xl font-bold text-blue-400">
                  {stats.cpu_usage.toLocaleString()} cycles
                </p>
              </div>
              <div className="bg-gray-900 rounded-xl p-4">
                <h3 className="text-gray-400 text-sm">Memory Usage</h3>
                <p className="text-2xl font-bold text-yellow-400">
                  {stats.mem_usage} MB / {stats.mem_limit} MB
                </p>
              </div>
              <div className="bg-gray-900 rounded-xl p-4">
                <h3 className="text-gray-400 text-sm">Memory %</h3>
                <p className="text-2xl font-bold text-green-400">
                  {stats.mem_percent}%
                </p>
              </div>
            </div>
          ) : (
            <p className="text-gray-400">Loading stats...</p>
          )}

          {/* === Logs Section === */}
          <div className="mt-4">
            <h3 className="text-gray-300 mb-2 font-semibold">📜 Logs</h3>
            <div className="bg-black rounded-xl p-3 max-h-80 overflow-y-auto text-xs font-mono text-gray-300">
              {logs.length > 0 ? (
                logs.map((line, i) => <div key={i}>{line}</div>)
              ) : (
                <p className="text-gray-500">No logs available</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ==================== Recent Events ==================== */}
      <div className="mt-6 bg-gray-800 rounded-2xl shadow-lg p-4">
        <h2 className="text-xl font-semibold mb-4 text-gray-200">
          Recent Events
        </h2>
        {history.length === 0 ? (
          <p className="text-gray-400">No events recorded yet.</p>
        ) : (
          <ul className="text-sm text-gray-300 space-y-2 max-h-64 overflow-y-auto">
            {[...history].reverse().slice(0, 25).map((h, i) => (
              <li key={i}>
                <span className="text-gray-400">{h.timestamp}</span> —{" "}
                <span className="font-semibold text-blue-300">{h.service}</span>{" "}
                →{" "}
                <span
                  className={
                    h.status === "healthy"
                      ? "text-green-400"
                      : h.status === "down"
                      ? "text-red-400"
                      : "text-yellow-400"
                  }
                >
                  {h.status}
                </span>{" "}
                ({h.action})
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <footer className="text-center mt-8 text-gray-500 text-sm">
        © {new Date().getFullYear()} Docker Watchdog — Created by Ragav 🧠
      </footer>
    </div>
  );
}
