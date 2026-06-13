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

interface EntityHistory {
  hour: string;
  mentions: number;
  sentiment: number;
  intent_purchase: number;
  authors: number;
}

interface EntityIntent {
  intent: string;
  count: number;
  avg_score: number;
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

interface TopicCluster {
  topic_id: number;
  label: string;
  keywords: string;
  count: number;
  created_at: string;
}

interface BacktestStats {
  total_signals: number;
  avg_return_5d: number;
  avg_return_21d: number;
  avg_return_63d: number;
  winners_21d: number;
  measured_21d: number;
}

interface BacktestSignal {
  entity_name: string;
  tickers: string;
  return_21d: number;
  created_at: string;
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
  const [clusters, setClusters] = useState<TopicCluster[]>([]);
  const [backtestStats, setBacktestStats] = useState<BacktestStats | null>(null);
  const [backtestSignals, setBacktestSignals] = useState<BacktestSignal[]>([]);
  const [activeTab, setActiveTab] = useState<"signals" | "entities" | "topics" | "clusters" | "backtest" | "compare">("signals");
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, signalsRes, entitiesRes, trendsRes, topicsRes, clustersRes, backtestRes] = await Promise.all([
          fetch(`${API}/api/stats`),
          fetch(`${API}/api/signals?status=new&limit=20`),
          fetch(`${API}/api/entities?limit=100`),
          fetch(`${API}/api/trends?hours=24`),
          fetch(`${API}/api/topics`),
          fetch(`${API}/api/clusters?limit=20`),
          fetch(`${API}/api/backtest`),
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
        if (clustersRes.ok) setClusters(await clustersRes.json());
        if (backtestRes.ok) {
          const bt = await backtestRes.json();
          setBacktestStats(bt.stats);
          setBacktestSignals(bt.top_signals);
        }
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

  const filteredEntities = entities.filter((e) => {
    const matchesSearch = !searchQuery ||
      e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (e.ticker && e.ticker.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = typeFilter === "all" || e.type === typeFilter;
    return matchesSearch && matchesType;
  });

  const entityTypes = [...new Set(entities.map(e => e.type))];

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
            {(["signals", "entities", "compare", "clusters", "backtest"] as const).map((tab) => (
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
            <EntityTable entities={filteredEntities} entityTypes={entityTypes} searchQuery={searchQuery} setSearchQuery={setSearchQuery} typeFilter={typeFilter} setTypeFilter={setTypeFilter} />
          )}

          {activeTab === "topics" && (
            <TopicBreakdown topics={topics} />
          )}

          {activeTab === "clusters" && (
            <ClusterView clusters={clusters} />
          )}

          {activeTab === "backtest" && (
            <BacktestView stats={backtestStats} signals={backtestSignals} />
          )}

          {activeTab === "compare" && (
            <CompareView entities={entities} />
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

      {/* Anomaly Breakdown */}
      <div className="bg-white/[0.02] rounded-xl p-3 mb-4">
        <div className="text-[10px] text-zinc-500 uppercase tracking-wider mb-2">Score Breakdown</div>
        <div className="flex items-center gap-4 text-[11px]">
          <span className="text-zinc-400">
            Gap <span className="text-white font-mono">{s.gap_score.toFixed(1)}</span>
          </span>
          <span className="text-zinc-600">x</span>
          <span className="text-zinc-400">
            Materiality <span className="text-white font-mono">{(s.materiality * 100).toFixed(0)}%</span>
          </span>
          <span className="text-zinc-600">x</span>
          <span className="text-zinc-400">
            Corroboration <span className="text-white font-mono">x{s.corroboration}</span>
          </span>
          <span className="text-zinc-600">x</span>
          <span className="text-zinc-400">
            Intent <span className="text-white font-mono">{((s.intent_purchase_share || 0) * 100).toFixed(0)}%</span>
          </span>
          <span className="text-zinc-600">=</span>
          <span className="text-indigo-400 font-semibold">{s.signal_score.toFixed(0)}</span>
        </div>
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

function EntityTable({ entities, entityTypes, searchQuery, setSearchQuery, typeFilter, setTypeFilter }: {
  entities: Entity[];
  entityTypes: string[];
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  typeFilter: string;
  setTypeFilter: (t: string) => void;
}) {
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [history, setHistory] = useState<EntityHistory[]>([]);
  const [intents, setIntents] = useState<EntityIntent[]>([]);

  const loadEntityDetail = async (entity: Entity) => {
    setSelectedEntity(entity);
    try {
      const [histRes, intentRes] = await Promise.all([
        fetch(`${API}/api/entities/${entity.id}/history?hours=168`),
        fetch(`${API}/api/entities/${entity.id}/intent`),
      ]);
      if (histRes.ok) setHistory(await histRes.json());
      if (intentRes.ok) setIntents(await intentRes.json());
    } catch (e) {
      console.error("Failed to load entity detail", e);
    }
  };

  if (selectedEntity) {
    return (
      <div>
        <button
          onClick={() => setSelectedEntity(null)}
          className="text-[13px] text-zinc-500 hover:text-white mb-4 flex items-center gap-1"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m15 18-6-6 6-6"/>
          </svg>
          Back to entities
        </button>

        <div className="bg-white/[0.02] rounded-2xl border border-white/[0.06] p-6 mb-4">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-xl font-semibold">{selectedEntity.name}</h2>
            {selectedEntity.ticker && selectedEntity.ticker !== "PRIVATE" && (
              <span className="text-[11px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-md">{selectedEntity.ticker}</span>
            )}
          </div>
          <div className="flex gap-6 text-[13px] text-zinc-500">
            <span>{selectedEntity.type}</span>
            <span>{selectedEntity.mcap_usd ? `$${(selectedEntity.mcap_usd / 1e9).toFixed(0)}B` : "Private"}</span>
            <span>{selectedEntity.mention_count} mentions</span>
          </div>
        </div>

        {/* Sentiment over time */}
        <div className="bg-white/[0.02] rounded-2xl border border-white/[0.06] p-6 mb-4">
          <h3 className="text-[13px] font-medium text-zinc-400 mb-4">Sentiment & Volume (7 days)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              {history.length > 0 ? (
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                  <XAxis
                    dataKey="hour"
                    stroke="#3f3f46"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => v ? new Date(v).toLocaleDateString([], { weekday: 'short', hour: '2-digit' }) : ''}
                  />
                  <YAxis yAxisId="left" stroke="#3f3f46" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis yAxisId="right" orientation="right" stroke="#3f3f46" fontSize={11} tickLine={false} axisLine={false} domain={[-1, 1]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#18181b", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 12, fontSize: 12 }}
                    labelFormatter={(v) => v ? new Date(v).toLocaleString() : ''}
                  />
                  <Line yAxisId="left" type="monotone" dataKey="mentions" name="Mentions" stroke="#6366f1" strokeWidth={2} dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="sentiment" name="Sentiment" stroke="#10b981" strokeWidth={2} dot={false} />
                  <Line yAxisId="left" type="monotone" dataKey="intent_purchase" name="Purchase Intent" stroke="#f59e0b" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                </LineChart>
              ) : (
                <div className="flex items-center justify-center h-full text-zinc-600 text-sm">
                  No historical data yet. Run the pipeline to populate.
                </div>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* Intent breakdown */}
        {intents.length > 0 && (
          <div className="bg-white/[0.02] rounded-2xl border border-white/[0.06] p-6">
            <h3 className="text-[13px] font-medium text-zinc-400 mb-4">Intent Distribution</h3>
            <div className="grid grid-cols-2 gap-3">
              {intents.map((i) => (
                <div key={i.intent} className="flex items-center justify-between p-3 bg-white/[0.02] rounded-xl">
                  <span className="text-[13px] text-zinc-300 capitalize">{i.intent.replace(/_/g, ' ')}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[13px] font-mono text-zinc-400">{i.count}</span>
                    <span className="text-[11px] text-zinc-600">({(i.avg_score * 100).toFixed(0)}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      {/* Search and Filter Bar */}
      <div className="flex gap-3 mb-4">
        <div className="relative flex-1">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.3-4.3"/>
          </svg>
          <input
            type="text"
            placeholder="Search by name or ticker..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/[0.02] border border-white/[0.06] rounded-xl pl-10 pr-4 py-2.5 text-[13px] text-white placeholder-zinc-500 focus:outline-none focus:border-white/[0.15] transition-colors"
          />
        </div>
        <div className="flex gap-1 bg-white/[0.02] rounded-xl p-1 border border-white/[0.06]">
          <button
            onClick={() => setTypeFilter("all")}
            className={`px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all ${
              typeFilter === "all" ? "bg-white/[0.08] text-white" : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            All
          </button>
          {entityTypes.map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all capitalize ${
                typeFilter === t ? "bg-white/[0.08] text-white" : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

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
            <tr
              key={e.id}
              className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors cursor-pointer"
              onClick={() => loadEntityDetail(e)}
            >
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

function ClusterView({ clusters }: { clusters: TopicCluster[] }) {
  return (
    <div>
      <div className="bg-white/[0.02] rounded-2xl p-6 border border-white/[0.06] mb-4">
        <h3 className="text-[13px] font-medium text-zinc-400 mb-2">Emerging Themes (BERTopic)</h3>
        <p className="text-[12px] text-zinc-600 mb-6">Auto-discovered topic clusters from the last 14 days of posts. New clusters with high growth = emerging trends.</p>
        {clusters.length === 0 ? (
          <div className="text-center py-12 text-zinc-600 text-sm">
            No clusters yet. Run the nightly clustering job to generate topics.
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {clusters.map((c) => (
              <div key={c.topic_id} className="bg-white/[0.02] rounded-xl p-4 border border-white/[0.04] hover:border-white/[0.1] transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[13px] font-medium text-zinc-200">{c.label}</span>
                  <span className="text-[11px] font-mono text-zinc-500">{c.count} posts</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {c.keywords.split(",").slice(0, 6).map((kw, i) => (
                    <span key={i} className="text-[10px] bg-white/[0.06] text-zinc-500 px-2 py-0.5 rounded">
                      {kw.trim()}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function BacktestView({ stats, signals }: { stats: BacktestStats | null; signals: BacktestSignal[] }) {
  return (
    <div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white/[0.02] rounded-2xl p-5 border border-white/[0.06]">
          <div className="text-[11px] text-zinc-500 uppercase tracking-wider mb-2">Total Signals</div>
          <div className="text-3xl font-bold">{stats?.total_signals || 0}</div>
        </div>
        <div className="bg-white/[0.02] rounded-2xl p-5 border border-white/[0.06]">
          <div className="text-[11px] text-zinc-500 uppercase tracking-wider mb-2">Avg 5d Return</div>
          <div className={`text-3xl font-bold ${(stats?.avg_return_5d || 0) > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {((stats?.avg_return_5d || 0) * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-white/[0.02] rounded-2xl p-5 border border-white/[0.06]">
          <div className="text-[11px] text-zinc-500 uppercase tracking-wider mb-2">Avg 21d Return</div>
          <div className={`text-3xl font-bold ${(stats?.avg_return_21d || 0) > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {((stats?.avg_return_21d || 0) * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-white/[0.02] rounded-2xl p-5 border border-white/[0.06]">
          <div className="text-[11px] text-zinc-500 uppercase tracking-wider mb-2">Win Rate (21d)</div>
          <div className="text-3xl font-bold text-indigo-400">
            {stats?.measured_21d ? `${((stats.winners_21d / stats.measured_21d) * 100).toFixed(0)}%` : "N/A"}
          </div>
        </div>
      </div>

      <div className="bg-white/[0.02] rounded-2xl border border-white/[0.06] overflow-hidden">
        <div className="p-4 border-b border-white/[0.04]">
          <h3 className="text-[13px] font-medium text-zinc-400">Top Performing Signals</h3>
        </div>
        {signals.length === 0 ? (
          <div className="p-12 text-center text-zinc-600 text-sm">
            No backtest data yet. Signals need 21+ days to measure returns.
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.04]">
                <th className="text-left text-[11px] font-medium text-zinc-500 uppercase tracking-wider p-4">Entity</th>
                <th className="text-left text-[11px] font-medium text-zinc-500 uppercase tracking-wider p-4">Ticker</th>
                <th className="text-right text-[11px] font-medium text-zinc-500 uppercase tracking-wider p-4">21d Return</th>
                <th className="text-right text-[11px] font-medium text-zinc-500 uppercase tracking-wider p-4">Date</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s, i) => (
                <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                  <td className="p-4 text-[13px] font-medium">{s.entity_name}</td>
                  <td className="p-4 text-[11px] font-mono text-zinc-400">{s.tickers}</td>
                  <td className={`p-4 text-right text-[13px] font-mono font-medium ${s.return_21d > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {s.return_21d > 0 ? '+' : ''}{(s.return_21d * 100).toFixed(1)}%
                  </td>
                <td className="p-4 text-right text-[12px] text-zinc-500">
                  {new Date(s.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function CompareView({ entities }: { entities: Entity[] }) {
  const [selected, setSelected] = useState<number[]>([]);
  const [compareData, setCompareData] = useState<Record<number, EntityHistory[]>>({});

  const toggleEntity = async (id: number) => {
    const newSelected = selected.includes(id)
      ? selected.filter(s => s !== id)
      : [...selected, id].slice(-4);

    setSelected(newSelected);

    for (const eid of newSelected) {
      if (!compareData[eid]) {
        try {
          const res = await fetch(`${API}/api/entities/${eid}/history?hours=168`);
          if (res.ok) {
            const data = await res.json();
            setCompareData(prev => ({ ...prev, [eid]: data }));
          }
        } catch (e) {}
      }
    }
  };

  const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444"];

  return (
    <div>
      <div className="bg-white/[0.02] rounded-2xl p-6 border border-white/[0.06] mb-4">
        <h3 className="text-[13px] font-medium text-zinc-400 mb-4">Compare Entities (select up to 4)</h3>
        <div className="flex flex-wrap gap-2">
          {entities.filter(e => e.ticker && e.ticker !== "PRIVATE").slice(0, 20).map((e) => (
            <button
              key={e.id}
              onClick={() => toggleEntity(e.id)}
              className={`px-3 py-1.5 rounded-lg text-[12px] font-medium transition-all border ${
                selected.includes(e.id)
                  ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/30"
                  : "bg-white/[0.02] text-zinc-500 border-white/[0.06] hover:border-white/[0.15]"
              }`}
            >
              {e.ticker}
            </button>
          ))}
        </div>
      </div>

      {selected.length > 0 && (
        <div className="bg-white/[0.02] rounded-2xl p-6 border border-white/[0.06]">
          <h3 className="text-[13px] font-medium text-zinc-400 mb-4">Sentiment Comparison (7 days)</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                <XAxis
                  dataKey="hour"
                  stroke="#3f3f46"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => v ? new Date(v).toLocaleDateString([], { weekday: 'short' }) : ''}
                />
                <YAxis stroke="#3f3f46" fontSize={11} tickLine={false} axisLine={false} domain={[-1, 1]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#18181b", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 12, fontSize: 12 }}
                />
                <Legend />
                {selected.map((eid, i) => {
                  const entity = entities.find(e => e.id === eid);
                  const data = compareData[eid] || [];
                  return (
                    <Line
                      key={eid}
                      type="monotone"
                      data={data.map((d, idx) => ({ ...d, idx }))}
                      dataKey="sentiment"
                      name={entity?.name || `Entity ${eid}`}
                      stroke={COLORS[i % COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
