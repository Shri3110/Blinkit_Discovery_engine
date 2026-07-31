import { useState, useEffect } from 'react';
import { Search, Sparkles, MessageSquare, Database, Users, BarChart2, CheckCircle2, AlertTriangle, AlertCircle, TrendingUp, Download, ArrowRight, ChevronRight, FileText } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import ReactMarkdown from 'react-markdown';

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

  useEffect(() => {
    fetch(`${API_BASE}/api/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Error fetching stats:", err));

    fetch(`${API_BASE}/api/reviews?limit=15`)
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
      setReport(`**Error**: Failed to generate insight. ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Transform Personas data (Top 5 only)
  const topPersonas = stats?.segments 
    ? [...stats.segments].sort((a, b) => b.value - a.value).slice(0, 5) 
    : [];

  return (
    <div className="app-container">
      <header className="header">
        <div>
          <h1>Blinkit AI Discovery Engine</h1>
          <p>Product intelligence powered by unstructured user feedback.</p>
        </div>
      </header>

      {/* High Level KPI Cards */}
      {stats && (
        <section className="kpi-row">
          <div className="kpi-card">
            <span className="kpi-label">Analyzed Feedback</span>
            <span className="kpi-value">{stats.total_reviews}</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Extracted Themes</span>
            <span className="kpi-value">{stats.topics_identified}</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Identified Personas</span>
            <span className="kpi-value">{stats.user_segments}</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Top Pain Point</span>
            <span className="kpi-value" style={{color: '#f43f5e', fontSize: '1.25rem'}}>Delivery Times</span>
          </div>
        </section>
      )}

      {/* AI Search & Prompts */}
      <section className="glass-panel full-width" style={{ marginBottom: '24px' }}>
        <form onSubmit={handleQuery} className="search-container">
          <input 
            type="text" 
            className="search-input"
            placeholder="Ask anything about user pain points, feature requests, or delivery..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="primary-button" disabled={loading || !query}>
            {loading ? 'Synthesizing...' : <><Sparkles size={18} /> Discover</>}
          </button>
        </form>

        <div className="prompt-pills">
          <span className="prompt-pill" onClick={() => { setQuery("Why do users abandon their carts?"); handleQuery(new Event('submit')); }}>
            "Why do users abandon their carts?"
          </span>
          <span className="prompt-pill" onClick={() => { setQuery("What do people think about delivery times?"); handleQuery(new Event('submit')); }}>
            "What do people think about delivery times?"
          </span>
          <span className="prompt-pill" onClick={() => { setQuery("Are there complaints about missing items in electronics?"); handleQuery(new Event('submit')); }}>
            "Are there complaints about missing items in electronics?"
          </span>
        </div>
      </section>

      {/* Loading & Report */}
      {loading && (
        <div className="loading full-width">
          <Sparkles className="spinner" size={18} /> Querying Vector DB & Generating Insights...
        </div>
      )}

      {report && (
        <section className="ai-report-card full-width">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h2><Sparkles size={20} color="#F8CB46" /> Executive Insight</h2>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="secondary-button" onClick={() => alert("Simulated: Exporting to PRD...")}>
                <FileText size={16} /> Export PRD
              </button>
              <button className="secondary-button" onClick={() => alert("Simulated: Creating Jira Ticket...")}>
                <CheckCircle2 size={16} /> Create Ticket
              </button>
            </div>
          </div>
          
          <div className="markdown-body">
            <ReactMarkdown>{report}</ReactMarkdown>
          </div>
        </section>
      )}

      {/* Visual Analytics */}
      <div className="dashboard-grid" style={{ marginTop: '32px' }}>
        
        {/* Top Personas Horizontal Bar Chart */}
        <section className="glass-panel">
          <h2><Users size={20} color="#3b82f6" /> Top 5 User Personas</h2>
          <div style={{ width: '100%', height: 280, marginTop: '20px' }}>
            <ResponsiveContainer>
              <BarChart data={topPersonas} layout="vertical" margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={true} vertical={false} />
                <XAxis type="number" stroke="#a1a1aa" hide />
                <YAxis dataKey="name" type="category" stroke="#f8fafc" width={140} tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px', color: '#f8fafc' }} cursor={{fill: 'rgba(255,255,255,0.05)'}}/>
                <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Top Topics by Volume (Replacing Heatmap) */}
        <section className="glass-panel">
          <h2><BarChart2 size={20} color="#10b981" /> Feedback by Topic</h2>
          <div style={{ width: '100%', height: 280, marginTop: '20px' }}>
            {heatmapData.length > 0 ? (
              <ResponsiveContainer>
                <BarChart data={heatmapData} margin={{ top: 20, right: 0, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="segment" stroke="#a1a1aa" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#a1a1aa" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px', color: '#f8fafc' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}/>
                  <Bar dataKey="Pricing" stackId="a" fill="#3b82f6" />
                  <Bar dataKey="Delivery" stackId="a" fill="#10b981" />
                  <Bar dataKey="Customer Service" stackId="a" fill="#f43f5e" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p style={{ color: '#a1a1aa' }}>Loading analytics...</p>
            )}
          </div>
        </section>

      </div>

      {/* Recent Feedback Feed */}
      <section className="glass-panel full-width">
        <h2><MessageSquare size={20} color="#f59e0b" /> Verified Feedback Stream</h2>
        <div className="reviews-container">
          {reviews.map(review => {
            // Determine sentiment badge based on tags
            let sentiment = 'neutral';
            if (review.topics?.includes('Positive Feedback')) sentiment = 'positive';
            if (review.topics?.includes('App/UI Issues') || review.topics?.includes('Delivery')) sentiment = 'negative';

            return (
              <div key={review.id} className="review-card">
                <div className="review-tags" style={{ marginBottom: '4px' }}>
                  {sentiment !== 'neutral' && <span className={`badge ${sentiment}`}>{sentiment}</span>}
                  {review.segment && <span className="badge segment">{review.segment}</span>}
                </div>
                <p className="review-text">"{review.content}"</p>
              </div>
            );
          })}
          {reviews.length === 0 && <p>No feedback available. You may need to refresh.</p>}
        </div>
      </section>

    </div>
  );
}

export default App;
