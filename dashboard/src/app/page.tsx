"use client";

import { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Cell
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
  narrative: string | null;
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
  ai_tech: "#6366f1",
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

const THEME_SECTORS: Record<string, string> = {
  "Semiconductors": "#6366f1",
  "Quantum Computing": "#8b5cf6",
  "Rare Earth": "#f59e0b",
  "Nuclear / SMR": "#ef4444",
  "Robotics & AI": "#10b981",
};

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [topics, setTopics] = useState<TopicData[]>([]);
  const [activeTab, setActiveTab] = useState<"signals" | "entities" | "topics">("signals");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, signalsRes, entitiesRes, trendsRes, topicsRes] = await Promise.all([
          fetch(`${API}/api/stats`),
          fetch(`${API}/api/signals?status=new&limit=20`),
          fetch(`${API}/api/entities?limit=100`),
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

  const topEntities = entities.sort((a, b) => b.mention_count - a.mention_count).slice(0, 8);

  return (
    <div className="min-h-screen bg-[#09090b] text-white selection:bg-indigo-500/30">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#09090b]/80 backdrop-blur-xl">
        <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
            </div>
            <span className="font-semibold text-[15px] tracking-tight">Social Arb</span>
          </div>
          <div className="flex items-center gap-6 text-[13px]">
            <div className="flex items-center gap-2 text-zinc-500">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"/>
              Live
            </div>
            <div className="text-zinc-600">{stats?.total_posts || 0} signals</div>
          </div>
        </div>
      </header>

      {loading ? (
        <div className="flex items-center justify-center h-[80vh]">
          <div className="flex items-center gap-3 text-zinc-500">
            <div className="w-4 h-4 border-2 border-zinc-700 border-t-zinc-400 rounded-full animate-spin"/>
            Loading...
          </div>
        </div>
      ) : (
        <main className="max-w-[1400px] mx-auto px-6 py-8">
          {/* Stats Row */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Total Signals"
              value={stats?.total_posts || 0}
              change={null}
            />
            <StatCard
              label="Avg Sentiment"
              value={`${(stats?.avg_sentiment || 0) > 0 ? "+" : ""}${(stats?.avg_sentiment || 0).toFixed(2)}`}
              change={null}
              color={(stats?.avg_sentiment || 0) > 0 ? "text-emerald-400" : "text-red-400"}
            />
            <StatCard
              label="Sources Active"
              value={Object.keys(stats?.source_counts || {}).length}
              change={null}
            />
            <StatCard
              label="Open Signals"
              value={signals.length}
              change={null}
              color="text-amber-400"
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="col-span-2 bg-white/[0.02] rounded-2xl p-6 border border-white/[0.06]">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-[13px] font-medium text-zinc-400">Volume vs Sentiment</h3>
                <span className="text-[11px] text-zinc-600">Last 24h</span>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  {trends.length > 0 ? (
                    <LineChart data={trends}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                      <XAxis dataKey="hour" stroke="#3f3f46" fontSize={11} tickLine={false} axisLine={false} />
                      <YAxis yAxisId="left" stroke="#3f3f46" fontSize={11} tickLine={false} axisLine={false} />
                      <YAxis yAxisId="right" orientation="right" stroke="#3f3f46" fontSize={11} tickLine={false} axisLine={false} domain={[-1, 1]} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#18181b", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 12, fontSize: 12 }}
                        itemStyle={{ color: "#a1a1aa" }}
                      />
                      <Line yAxisId="left" type="monotone" dataKey="volume" name="Volume" stroke="#6366f1" strokeWidth={2} dot={false} />
                      <Line yAxisId="right" type="monotone" dataKey="avg_sentiment" name="Sentiment" stroke="#10b981" strokeWidth={2} dot={false} />
                    </LineChart>
                  ) : (
                    <div className="flex items-center justify-center h-full text-zinc-600 text-sm">Collecting data...</div>
                  )}
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white/[0.02] rounded-2xl p-6 border border-white/[0.06]">
              <h3 className="text-[13px] font-medium text-zinc-400 mb-6">Top Entities</h3>
              <div className="space-y-3">
                {topEntities.map((e) => (
                  <div key={e.id} className="flex items-center justify-between group">
                    <div className="flex items-center gap-2.5">
                      <div className="w-1 h-1 rounded-full bg-zinc-600 group-hover:bg-indigo-500 transition-colors"/>
                      <span className="text-[13px] text-zinc-300 group-hover:text-white transition-colors">{e.name}</span>
                      {e.ticker && (
                        <span className="text-[10px] font-mono bg-white/[0.06] text-zinc-500 px-1.5 py-0.5 rounded">{e.ticker}</span>
                      )}
                    </div>
                    <span className="text-[11px] text-zinc-600 font-mono">{e.mention_count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mb-6 bg-white/[0.02] rounded-xl p-1 w-fit border border-white/[0.06]">
            {(["signals", "entities", "topics"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2 rounded-lg text-[13px] font-medium transition-all ${
                  activeTab === tab
                    ? "bg-white/[0.08] text-white shadow-sm"
                    : "text-zinc-500 hover:text-zinc-300"
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
                <EmptyState />
              ) : (
                signals.map((s) => <SignalCard key={s.id} signal={s} />)
              )}
            </div>
          )}

          {activeTab === "entities" && (
            <EntityTable entities={entities} />
          )}

          {activeTab === "topics" && (
            <TopicBreakdown topics={topics} />
          )}
        </main>
      )}
    </div>
  );
}

function StatCard({ label, value, change, color = "text-white" }: {
  label: string; value: string | number; change: string | null; color?: string;
}) {
  return (
    <div className="bg-white/[0.02] rounded-2xl p-5 border border-white/[0.06] hover:border-white/[0.1] transition-colors">
      <div className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider mb-2">{label}</div>
      <div className={`text-3xl font-bold tracking-tight ${color}`}>{value}</div>
    </div>
  );
}

function SignalCard({ signal: s }: { signal: Signal }) {
  const directionColor = s.direction === "long" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border-amber-500/20";
  const scoreWidth = Math.min((s.signal_score / 100) * 100, 100);

  return (
    <div className="bg-white/[0.02] rounded-2xl border border-white/[0.06] p-6 hover:border-white/[0.1] transition-all group">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold tracking-tight">{s.entity_name}</h3>
          {s.tickers && s.tickers !== "PRIVATE" && (
            <span className="text-[11px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-md">{s.tickers}</span>
          )}
          <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full border ${directionColor}`}>
            {s.direction.toUpperCase()}
          </span>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold tracking-tight text-white">{s.signal_score.toFixed(0)}</div>
          <div className="text-[11px] text-zinc-500">score</div>
        </div>
      </div>

      {/* Score bar */}
      <div className="h-1 bg-white/[0.04] rounded-full mb-5 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-1000"
          style={{ width: `${scoreWidth}%` }}
        />
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-5 gap-4 mb-4">
        <MetricBlock label="Gap" value={s.gap_score.toFixed(1)} color={s.gap_score > 2 ? "text-emerald-400" : "text-zinc-400"} />
        <MetricBlock label="Demand" value={s.demand_index.toFixed(1)} color="text-indigo-400" />
        <MetricBlock label="Awareness" value={s.awareness_index.toFixed(1)} color={s.awareness_index < 1 ? "text-emerald-400" : "text-amber-400"} />
        <MetricBlock label="Platforms" value={`x${s.corroboration}`} />
        <MetricBlock label="Materiality" value={`${(s.materiality * 100).toFixed(0)}%`} />
      </div>

      {/* Narrative */}
      {s.narrative && (
        <p className="text-[13px] text-zinc-500 leading-relaxed border-t border-white/[0.04] pt-4 mt-4">
          {s.narrative}
        </p>
      )}

      {/* Timestamp */}
      <div className="text-[11px] text-zinc-600 mt-3">
        {new Date(s.created_at).toLocaleString()}
      </div>
    </div>
  );
}

function MetricBlock({ label, value, color = "text-zinc-300" }: {
  label: string; value: string; color?: string;
}) {
  return (
    <div>
      <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1">{label}</div>
      <div className={`text-sm font-semibold font-mono ${color}`}>{value}</div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="bg-white/[0.02] rounded-2xl p-16 border border-white/[0.06] text-center">
      <div className="w-12 h-12 rounded-2xl bg-white/[0.04] flex items-center justify-center mx-auto mb-4">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-zinc-600">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.3-4.3"/>
        </svg>
      </div>
      <h3 className="text-sm font-medium text-zinc-400 mb-1">No active signals</h3>
      <p className="text-[13px] text-zinc-600 max-w-sm mx-auto">
        Signals appear when consumer demand outpaces financial awareness.
        Run the data pipeline to generate signals.
      </p>
    </div>
  );
}

function EntityTable({ entities }: { entities: Entity[] }) {
  return (
    <div className="bg-white/[0.02] rounded-2xl border border-white/[0.06] overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/[0.04]">
            <th className="text-left text-[11px] font-medium text-zinc-500 uppercase tracking-wider p-4">Entity</th>
            <th className="text-left text-[11px] font-medium text-zinc-500 uppercase tracking-wider p-4">Ticker</th>
            <th className="text-left text-[11px] font-medium text-zinc-500 uppercase tracking-wider p-4">Type</th>
            <th className="text-right text-[11px] font-medium text-zinc-500 uppercase tracking-wider p-4">Market Cap</th>
            <th className="text-right text-[11px] font-medium text-zinc-500 uppercase tracking-wider p-4">Mentions</th>
          </tr>
        </thead>
        <tbody>
          {entities.map((e) => (
            <tr key={e.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
              <td className="p-4 text-[13px] font-medium">{e.name}</td>
              <td className="p-4">
                {e.ticker && (
                  <span className="text-[11px] font-mono bg-white/[0.06] text-zinc-400 px-2 py-0.5 rounded">{e.ticker}</span>
                )}
              </td>
              <td className="p-4 text-[13px] text-zinc-500 capitalize">{e.type}</td>
              <td className="p-4 text-right text-[13px] text-zinc-500 font-mono">
                {e.mcap_usd ? `$${(e.mcap_usd / 1e9).toFixed(0)}B` : "-"}
              </td>
              <td className="p-4 text-right text-[13px] text-zinc-400 font-mono">{e.mention_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TopicBreakdown({ topics }: { topics: TopicData[] }) {
  const maxVolume = topics[0]?.volume || 1;

  return (
    <div className="bg-white/[0.02] rounded-2xl p-6 border border-white/[0.06]">
      <h3 className="text-[13px] font-medium text-zinc-400 mb-6">Topic Distribution</h3>
      <div className="space-y-4">
        {topics.map((t) => (
          <div key={t.topic}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: TOPIC_COLORS[t.topic] || "#52525b" }}/>
                <span className="text-[13px] text-zinc-300 capitalize">{t.topic.replace("_", " ")}</span>
              </div>
              <span className="text-[11px] text-zinc-500 font-mono">{t.volume}</span>
            </div>
            <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-1000"
                style={{
                  width: `${(t.volume / maxVolume) * 100}%`,
                  backgroundColor: TOPIC_COLORS[t.topic] || "#52525b",
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
