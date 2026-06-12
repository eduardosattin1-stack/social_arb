"use client";

import { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend, Cell
} from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Stats {
  total_posts: number;
  source_counts: Record<string, number>;
  avg_sentiment: number;
  positive_count: number;
  negative_count: number;
}

interface Signal {
  id: number;
  entity_name: string;
  tickers: string | null;
  direction: string;
  signal_score: number;
  gap_score: number;
  demand_index: number;
  awareness_index: number;
  velocity_z: number;
  corroboration: number;
  materiality: number;
  status: string;
  created_at: string;
}

interface Entity {
  id: number;
  name: string;
  type: string;
  ticker: string | null;
  mcap_usd: number | null;
  mono_brand: boolean;
  mention_count: number;
}

interface TrendPoint {
  hour: string;
  volume: number;
  avg_sentiment: number;
}

interface TopicData {
  topic: string;
  volume: number;
  avg_sentiment: number;
}

const TOPIC_COLORS: Record<string, string> = {
  ai_tech: "#3b82f6",
  crypto: "#f59e0b",
  electric_vehicles: "#10b981",
  fintech: "#8b5cf6",
  social_media: "#ec4899",
  gaming: "#ef4444",
  healthcare: "#06b6d4",
  climate: "#22c55e",
  retail: "#f97316",
  geopolitics: "#64748b",
};

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [topics, setTopics] = useState<TopicData[]>([]);
  const [activeTab, setActiveTab] = useState<"signals" | "entities" | "feed">("signals");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, signalsRes, entitiesRes, trendsRes, topicsRes] = await Promise.all([
          fetch(`${API}/api/stats`),
          fetch(`${API}/api/signals?status=new&limit=20`),
          fetch(`${API}/api/entities?limit=50`),
          fetch(`${API}/api/trends?hours=24`),
          fetch(`${API}/api/topics`),
        ]);

        if (statsRes.ok) setStats(await statsRes.json());
        if (signalsRes.ok) setSignals(await signalsRes.json());
        if (entitiesRes.ok) setEntities(await entitiesRes.json());
        if (trendsRes.ok) {
          const data = await trendsRes.json();
          setTrends(data.map((t: TrendPoint) => ({
            ...t,
            hour: t.hour ? new Date(t.hour).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "",
          })));
        }
        if (topicsRes.ok) setTopics(await topicsRes.json());
      } catch (e) {
        console.error("Fetch error:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const topEntities = entities.slice(0, 10);

  return (
    <div className="min-h-screen bg-[#0a0f1a] text-white">
      {/* Header */}
      <header className="border-b border-white/10 px-8 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-lg font-bold">
              SA
            </div>
            <div>
              <h1 className="text-xl font-bold">Social Arb</h1>
              <p className="text-xs text-gray-400">Social Arbitrage Signal Engine</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Live
          </div>
        </div>
      </header>

      {loading ? (
        <div className="flex items-center justify-center h-[80vh] text-gray-400">
          Loading signals...
        </div>
      ) : (
        <main className="max-w-7xl mx-auto px-8 py-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <StatCard label="Total Signals" value={stats?.total_posts || 0} />
            <StatCard
              label="Avg Sentiment"
              value={`${(stats?.avg_sentiment || 0) > 0 ? "+" : ""}${(stats?.avg_sentiment || 0).toFixed(2)}`}
              color={(stats?.avg_sentiment || 0) > 0 ? "text-emerald-400" : "text-red-400"}
            />
            <StatCard label="Active Sources" value={Object.keys(stats?.source_counts || {}).length} />
            <StatCard label="Open Signals" value={signals.length} color="text-amber-400" />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="col-span-2 bg-white/5 rounded-xl p-5 border border-white/10">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Volume vs Sentiment (24h)</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  {trends.length > 0 ? (
                    <LineChart data={trends}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="hour" stroke="#6b7280" fontSize={11} />
                      <YAxis yAxisId="left" stroke="#3b82f6" fontSize={11} />
                      <YAxis yAxisId="right" orientation="right" stroke="#10b981" domain={[-1, 1]} fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "none", borderRadius: 8 }} />
                      <Legend />
                      <Line yAxisId="left" type="monotone" dataKey="volume" name="Volume" stroke="#3b82f6" strokeWidth={2} dot={false} />
                      <Line yAxisId="right" type="monotone" dataKey="avg_sentiment" name="Sentiment" stroke="#10b981" strokeWidth={2} dot={false} />
                    </LineChart>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">No trend data</div>
                  )}
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white/5 rounded-xl p-5 border border-white/10">
              <h3 className="text-sm font-semibold text-gray-300 mb-4">Top Entities</h3>
              <div className="space-y-3">
                {topEntities.map((e) => (
                  <div key={e.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{e.name}</span>
                      {e.ticker && (
                        <span className="text-xs bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded">{e.ticker}</span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">{e.mention_count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mb-4 bg-white/5 rounded-lg p-1 w-fit">
            {(["signals", "entities", "feed"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                  activeTab === tab ? "bg-white/10 text-white" : "text-gray-400 hover:text-white"
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === "signals" && (
            <div className="space-y-3">
              {signals.length === 0 ? (
                <div className="bg-white/5 rounded-xl p-8 border border-white/10 text-center text-gray-500">
                  No active signals yet. Signals appear when demand outpaces awareness.
                </div>
              ) : (
                signals.map((s) => (
                  <div key={s.id} className="bg-white/5 rounded-xl p-5 border border-white/10 hover:border-white/20 transition">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-lg">{s.entity_name}</span>
                          {s.tickers && (
                            <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded">{s.tickers}</span>
                          )}
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            s.direction === "long" ? "bg-emerald-500/20 text-emerald-300" : "bg-amber-500/20 text-amber-300"
                          }`}>
                            {s.direction.toUpperCase()}
                          </span>
                        </div>
                        <div className="flex gap-4 text-sm text-gray-400">
                          <span>Score: <b className="text-white">{s.signal_score.toFixed(2)}</b></span>
                          <span>Gap: <b className="text-white">{s.gap_score.toFixed(2)}</b></span>
                          <span>Demand: <b className="text-white">{s.demand_index.toFixed(2)}</b></span>
                          <span>Awareness: <b className="text-white">{s.awareness_index.toFixed(2)}</b></span>
                          <span>x{s.corroboration} platforms</span>
                        </div>
                      </div>
                      <div className="text-right text-xs text-gray-500">
                        {new Date(s.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "entities" && (
            <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10 text-xs text-gray-400">
                    <th className="text-left p-3">Entity</th>
                    <th className="text-left p-3">Ticker</th>
                    <th className="text-left p-3">Type</th>
                    <th className="text-right p-3">Mcap</th>
                    <th className="text-right p-3">Mentions</th>
                  </tr>
                </thead>
                <tbody>
                  {entities.map((e) => (
                    <tr key={e.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="p-3 font-medium">{e.name}</td>
                      <td className="p-3">
                        {e.ticker && <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded">{e.ticker}</span>}
                      </td>
                      <td className="p-3 text-sm text-gray-400 capitalize">{e.type}</td>
                      <td className="p-3 text-right text-sm text-gray-400">
                        {e.mcap_usd ? `$${(e.mcap_usd / 1e9).toFixed(0)}B` : "-"}
                      </td>
                      <td className="p-3 text-right text-sm">{e.mention_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "feed" && (
            <TopicsFeed topics={topics} />
          )}
        </main>
      )}
    </div>
  );
}

function StatCard({ label, value, color = "text-white" }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="bg-white/5 rounded-xl p-4 border border-white/10">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

function TopicsFeed({ topics }: { topics: TopicData[] }) {
  return (
    <div className="bg-white/5 rounded-xl p-5 border border-white/10">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Topic Breakdown</h3>
      <div className="space-y-3">
        {topics.map((t) => (
          <div key={t.topic}>
            <div className="flex justify-between text-sm mb-1">
              <span className="capitalize">{t.topic.replace("_", " ")}</span>
              <span className="text-gray-400">{t.volume}</span>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.min((t.volume / (topics[0]?.volume || 1)) * 100, 100)}%`,
                  backgroundColor: TOPIC_COLORS[t.topic] || "#64748b",
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
