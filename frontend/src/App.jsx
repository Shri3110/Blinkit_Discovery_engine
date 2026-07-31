import { useState, useEffect } from 'react';
import { Search, Sparkles, MessageSquare, Database, Users, BarChart2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const rawApiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE = rawApiBase.replace(/\/$/, '');

function App() {
  const [query, setQuery] = useState('');
  const [report, setReport] = useState('');
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]);
  
  const COLORS = ['#8b5cf6', '#ec4899', '#10b981', '#F8CB46', '#3b82f6', '#f43f5e', '#f97316', '#14b8a6'];
  const sentimentData = stats ? [
    { name: 'Positive', value: stats.positive || 0, fill: '#10b981' },
    { name: 'Neutral', value: stats.neutral || 0, fill: '#94a3b8' },
    { name: 'Negative', value: stats.negative || 0, fill: '#f43f5e' }
  ] : [];

  useEffect(() => {
    // Fetch stats and reviews on load
    fetch(`${API_BASE}/api/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Error fetching stats:", err));

    fetch(`${API_BASE}/api/reviews?limit=20`)
      .then(res => res.json())
      .then(data => setReviews(data))
      .catch(err => console.error("Error fetching reviews:", err));

    fetch(`${API_BASE}/api/trends/heatmap`)
      .then(res => res.json())
      .then(data => setHeatmapData(data))
      .catch(err => console.error("Error fetching heatmap:", err));
  }, []);

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query) return;
    
    setLoading(true);
    setReport('');
    
    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      const data = await res.json();
      setReport(data.report);
      if (data.evidence) {
        setEvidence(data.evidence);
      }
    } catch (err) {
      console.error(err);
      setReport(`Failed to generate insight. Error: ${err.message}. Ensure VITE_API_URL is correct and backend is running.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Blinkit AI Discovery Engine</h1>
        <p>Uncovering deeper user insights with RAG & Vector Search</p>
      </header>

      {/* KPI Dashboard */}
      {stats && (
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '16px', marginBottom: '32px' }}>
          <div className="glass-panel stat-card" style={{ padding: '16px' }}>
            <div className="stat-value">{stats.total_reviews || 0}</div>
            <div className="stat-label">Total Reviews</div>
          </div>
          <div className="glass-panel stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ color: '#10b981' }}>{stats.positive || 0}</div>
            <div className="stat-label">Positive</div>
          </div>
          <div className="glass-panel stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ color: '#f43f5e' }}>{stats.negative || 0}</div>
            <div className="stat-label">Negative</div>
          </div>
          <div className="glass-panel stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ color: '#94a3b8' }}>{stats.neutral || 0}</div>
            <div className="stat-label">Neutral</div>
          </div>
          <div className="glass-panel stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ color: '#8b5cf6' }}>{stats.topics_identified || 0}</div>
            <div className="stat-label">Topics Found</div>
          </div>
          <div className="glass-panel stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ color: '#F8CB46' }}>{stats.user_segments || 0}</div>
            <div className="stat-label">Segments</div>
          </div>
          <div className="glass-panel stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ color: '#3b82f6' }}>{stats.sources_analysed || 0}</div>
            <div className="stat-label">Sources</div>
          </div>
        </section>
      )}

      {/* RAG Query Panel */}
      <section className="glass-panel full-width" style={{ marginBottom: '32px' }}>
        <h2><Sparkles size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle', color: '#8b5cf6' }}/> Ask the AI</h2>
        <form onSubmit={handleQuery} className="search-container">
          <input 
            type="text" 
            className="search-input"
            placeholder="e.g., Why do users hesitate to buy electronics?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="primary-button" disabled={loading || !query}>
            {loading ? 'Analyzing...' : <><Search size={18} /> Generate Insight</>}
          </button>
        </form>

        {loading && <div className="loading" style={{ color: '#94a3b8' }}>Synthesizing RAG context with Groq...</div>}
        
        {report && (
          <div className="insight-report">
            <pre>{report}</pre>

          </div>
        )}
      </section>

      {/* Cross-Category Heatmap */}
      <section className="glass-panel full-width" style={{ marginBottom: '32px' }}>
        <h2><BarChart2 size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle', color: '#ec4899' }}/> Topics Discussed by User Segment (Heatmap)</h2>
        <div style={{ width: '100%', height: 350, marginTop: '20px' }}>
          {heatmapData.length > 0 ? (
            <ResponsiveContainer>
              <BarChart data={heatmapData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="segment" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }} />
                <Legend />
                <Bar dataKey="Quality" stackId="a" fill="#8b5cf6" />
                <Bar dataKey="Pricing" stackId="a" fill="#ec4899" />
                <Bar dataKey="Delivery" stackId="a" fill="#10b981" />
                <Bar dataKey="Customer Service" stackId="a" fill="#F8CB46" />
                <Bar dataKey="Product Availability" stackId="a" fill="#3b82f6" />
                <Bar dataKey="App/UI Issues" stackId="a" fill="#f43f5e" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ color: '#94a3b8' }}>Loading heatmap data...</p>
          )}
        </div>
      </section>

      {/* New Visualizations Row */}
      {stats && (
        <div className="dashboard-grid">
          {/* Sentiment Overview */}
          <section className="glass-panel">
            <h2><BarChart2 size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle', color: '#10b981' }}/> Sentiment Overview</h2>
            <div style={{ width: '100%', height: 300, marginTop: '20px' }}>
              <ResponsiveContainer>
                <BarChart data={sentimentData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }} cursor={{fill: 'rgba(255,255,255,0.05)'}}/>
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* User Personas Donut */}
          <section className="glass-panel">
            <h2><Users size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle', color: '#8b5cf6' }}/> User Personas Distribution</h2>
            <div style={{ width: '100%', height: 300, marginTop: '20px' }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={stats.segments}
                    cx="50%"
                    cy="50%"
                    innerRadius={80}
                    outerRadius={110}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {stats.segments.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }} />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}/>
                </PieChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
      )}

      <div className="dashboard-grid">
        {/* Suggested Queries Panel */}
        <section className="glass-panel">
          <h2><Sparkles size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle', color: '#F8CB46' }}/> Suggested Queries</h2>
          <p style={{ marginBottom: '16px' }}>Click a query to instantly run a RAG search against user feedback:</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button 
              onClick={() => { setQuery("Why do users abandon their carts?"); handleQuery(new Event('submit')); }}
              className="search-input" 
              style={{ cursor: 'pointer', textAlign: 'left', border: '1px solid rgba(248, 203, 70, 0.3)' }}
            >
              "Why do users abandon their carts?"
            </button>
            <button 
              onClick={() => { setQuery("What do people think about the delivery times?"); handleQuery(new Event('submit')); }}
              className="search-input" 
              style={{ cursor: 'pointer', textAlign: 'left', border: '1px solid rgba(248, 203, 70, 0.3)' }}
            >
              "What do people think about the delivery times?"
            </button>
            <button 
              onClick={() => { setQuery("Are there complaints about missing items in electronics?"); handleQuery(new Event('submit')); }}
              className="search-input" 
              style={{ cursor: 'pointer', textAlign: 'left', border: '1px solid rgba(248, 203, 70, 0.3)' }}
            >
              "Are there complaints about missing items in electronics?"
            </button>
            <button 
              onClick={() => { setQuery("What features do bachelor users request the most?"); handleQuery(new Event('submit')); }}
              className="search-input" 
              style={{ cursor: 'pointer', textAlign: 'left', border: '1px solid rgba(248, 203, 70, 0.3)' }}
            >
              "What features do bachelor users request the most?"
            </button>
          </div>
        </section>

        {/* Evidence Viewer (Conditionally rendered) */}
        {evidence.length > 0 && (
          <section className="glass-panel" style={{ marginBottom: '32px' }}>
            <h2><MessageSquare size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle', color: '#10b981' }}/> Query Evidence</h2>
            <div className="reviews-container">
              {evidence.map(review => (
                <div key={review.id || review.content} className="review-card">
                  <p className="review-text">"{review.content}"</p>
                  <div className="review-tags">
                    {review.segment && <span className="badge segment">{review.segment}</span>}
                    {review.topic && <span className="badge topic">{review.topic}</span>}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Recent Feedback */}
        <section className="glass-panel">
          <h2><MessageSquare size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle', color: '#3b82f6' }}/> Recent Feedback</h2>
          <div className="reviews-container">
            {reviews.map(review => (
              <div key={review.id} className="review-card">
                <p className="review-text">"{review.content}"</p>
                <div className="review-tags">
                  {review.segment && <span className="badge segment">{review.segment}</span>}
                  {review.topics && review.topics.map(topic => (
                    <span key={topic} className="badge topic">{topic}</span>
                  ))}
                </div>
              </div>
            ))}
            {reviews.length === 0 && <p>No feedback available. You may need to refresh the page.</p>}
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
