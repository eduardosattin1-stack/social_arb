import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend, PieChart, Pie, Cell
} from 'recharts';
import './App.css';

interface Post {
  id: number;
  source: string;
  post_id: string;
  content: string;
  author: string;
  timestamp: string;
  region: string;
  sentiment: number;
  topic: string;
  url: string;
  score: number;
  num_comments: number;
}

interface Stats {
  total_posts: number;
  source_counts: Record<string, number>;
  avg_sentiment: number;
  positive_count: number;
  negative_count: number;
}

interface TrendPoint {
  hour: string;
  volume: number;
  avg_sentiment: number;
}

interface RegionData {
  region: string;
  volume: number;
  avg_sentiment: number;
}

interface TopicData {
  topic: string;
  volume: number;
  avg_sentiment: number;
}

const TOPIC_COLORS: Record<string, string> = {
  ai_tech: '#3b82f6',
  crypto: '#f59e0b',
  electric_vehicles: '#10b981',
  fintech: '#8b5cf6',
  social_media: '#ec4899',
  gaming: '#ef4444',
  healthcare: '#06b6d4',
  climate: '#22c55e',
  retail: '#f97316',
  geopolitics: '#64748b',
};

const REGION_COLORS: Record<string, string> = {
  Americas: '#3b82f6',
  Europe: '#8b5cf6',
  Asia: '#10b981',
  Global: '#64748b',
};

function App() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [regions, setRegions] = useState<RegionData[]>([]);
  const [topics, setTopics] = useState<TopicData[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [postsRes, statsRes, trendsRes, regionsRes, topicsRes] = await Promise.all([
        fetch('http://localhost:8000/api/posts?limit=20'),
        fetch('http://localhost:8000/api/stats'),
        fetch('http://localhost:8000/api/trends?hours=24'),
        fetch('http://localhost:8000/api/regions'),
        fetch('http://localhost:8000/api/topics'),
      ]);

      if (postsRes.ok) setPosts(await postsRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
      if (trendsRes.ok) {
        const data = await trendsRes.json();
        setTrends(data.map((t: TrendPoint) => ({
          ...t,
          hour: t.hour ? new Date(t.hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
        })));
      }
      if (regionsRes.ok) setRegions(await regionsRes.json());
      if (topicsRes.ok) setTopics(await topicsRes.json());
    } catch (error) {
      console.error("Failed to fetch data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      <aside className="sidebar glass">
        <div className="brand">
          <div className="brand-icon">⚡</div>
          Social Arb
        </div>
        <nav className="nav-menu">
          <div className="nav-item active">Dashboard</div>
          <div className="nav-item">Geomap</div>
          <div className="nav-item">Analytics</div>
          <div className="nav-item">Alerts</div>
          <div className="nav-item">Settings</div>
        </nav>
        <div className="sidebar-footer">
          <div className="db-status">
            <span className="status-dot"></span>
            PostgreSQL Connected
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="header">
          <div>
            <h1>Global Radar</h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              Live monitoring across social and news networks.
            </p>
          </div>
          <div className="live-indicator">
            <span className="status-dot live"></span>
            Live Updates Active
          </div>
        </header>

        {loading ? (
          <div className="loading">Initializing Radar...</div>
        ) : (
          <div className="animate-fade-in">
            {/* Stats Grid */}
            <div className="dashboard-grid">
              <div className="card stat-card">
                <h3>Total Signals</h3>
                <div className="stat-value">{stats?.total_posts || 0}</div>
                <div className="stat-sub">intercepted</div>
              </div>
              <div className="card stat-card">
                <h3>Avg Sentiment</h3>
                <div className={`stat-value ${(stats?.avg_sentiment || 0) > 0 ? 'trend-up' : 'trend-down'}`}>
                  {(stats?.avg_sentiment || 0) > 0 ? '+' : ''}{(stats?.avg_sentiment || 0).toFixed(2)}
                </div>
                <div className="stat-sub">
                  <span style={{ color: 'var(--success-color)' }}>+{stats?.positive_count || 0}</span>
                  {' / '}
                  <span style={{ color: 'var(--danger-color)' }}>{stats?.negative_count || 0}</span>
                </div>
              </div>
              <div className="card stat-card">
                <h3>Data Sources</h3>
                <div className="stat-value">{Object.keys(stats?.source_counts || {}).length}</div>
                <div className="stat-sub">active feeds</div>
              </div>
              <div className="card stat-card">
                <h3>Top Topic</h3>
                <div className="stat-value" style={{ fontSize: '1.5rem' }}>
                  {topics[0]?.topic?.replace('_', ' ') || 'N/A'}
                </div>
                <div className="stat-sub">{topics[0]?.volume || 0} signals</div>
              </div>
            </div>

            {/* Charts Row */}
            <div className="dashboard-grid" style={{ gridTemplateColumns: '2fr 1fr' }}>
              <div className="card">
                <h2>Sentiment vs Volume (24h)</h2>
                <div style={{ height: '300px', marginTop: '1rem' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    {trends.length > 0 ? (
                      <LineChart data={trends}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="hour" stroke="#94a3b8" fontSize={12} />
                        <YAxis yAxisId="left" stroke="#3b82f6" />
                        <YAxis yAxisId="right" orientation="right" stroke="#10b981" domain={[-1, 1]} />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
                        <Legend />
                        <Line yAxisId="left" type="monotone" dataKey="volume" name="Volume" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4 }} />
                        <Line yAxisId="right" type="monotone" dataKey="avg_sentiment" name="Sentiment" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} />
                      </LineChart>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
                        Collecting data...
                      </div>
                    )}
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="card">
                <h2>Signal Origin</h2>
                <div style={{ height: '300px', marginTop: '1rem' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    {regions.length > 0 ? (
                      <BarChart data={regions} layout="vertical">
                        <XAxis type="number" hide />
                        <YAxis dataKey="region" type="category" stroke="#94a3b8" axisLine={false} tickLine={false} />
                        <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
                        <Bar dataKey="volume" radius={[0, 4, 4, 0]} barSize={24}>
                          {regions.map((entry) => (
                            <Cell key={entry.region} fill={REGION_COLORS[entry.region] || '#64748b'} />
                          ))}
                        </Bar>
                      </BarChart>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
                        No region data yet
                      </div>
                    )}
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Topics & Live Feed */}
            <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr', marginTop: '2rem' }}>
              {/* Topic Breakdown */}
              <div className="card">
                <h2>Trending Topics</h2>
                <div className="topics-list">
                  {topics.map((topic) => (
                    <div key={topic.topic} className="topic-item">
                      <div className="topic-bar-container">
                        <div
                          className="topic-bar"
                          style={{
                            width: `${Math.min((topic.volume / (topics[0]?.volume || 1)) * 100, 100)}%`,
                            backgroundColor: TOPIC_COLORS[topic.topic] || '#64748b',
                          }}
                        />
                      </div>
                      <div className="topic-info">
                        <span className="topic-name">{topic.topic.replace('_', ' ')}</span>
                        <span className="topic-count">{topic.volume}</span>
                      </div>
                    </div>
                  ))}
                  {topics.length === 0 && (
                    <p style={{ color: 'var(--text-secondary)', padding: '2rem', textAlign: 'center' }}>
                      Analyzing topics...
                    </p>
                  )}
                </div>
              </div>

              {/* Live Feed */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2>Live Feed</h2>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Auto-refresh 30s</div>
                </div>
                <div className="posts-list">
                  {posts.map(post => {
                    const sentimentColor = post.sentiment > 0.1
                      ? 'var(--success-color)'
                      : post.sentiment < -0.1
                        ? 'var(--danger-color)'
                        : 'var(--text-secondary)';
                    return (
                      <div key={post.id} className="post-item" style={{ borderLeft: `4px solid ${sentimentColor}` }}>
                        <div className="post-meta">
                          <div>
                            <span className="post-source">{post.source}</span>
                            <span className="post-topic" style={{ backgroundColor: TOPIC_COLORS[post.topic] || '#64748b' }}>
                              {post.topic?.replace('_', ' ') || 'general'}
                            </span>
                          </div>
                          <div style={{ color: sentimentColor, fontWeight: 'bold', fontSize: '0.875rem' }}>
                            {post.sentiment > 0 ? '+' : ''}{post.sentiment?.toFixed(2) || '0.00'}
                          </div>
                        </div>
                        <div className="post-content">{post.content}</div>
                        <div className="post-footer">
                          <span>{post.author}</span>
                          <span>{post.region}</span>
                          <span>{new Date(post.timestamp).toLocaleTimeString()}</span>
                        </div>
                      </div>
                    );
                  })}
                  {posts.length === 0 && (
                    <p style={{ color: 'var(--text-secondary)', padding: '2rem', textAlign: 'center' }}>
                      No signals intercepted yet.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
