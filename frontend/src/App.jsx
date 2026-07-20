import { useState, useEffect } from 'react';
import { Search, Sparkles, MessageSquare, Database, Users, BarChart2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function App() {
  const [query, setQuery] = useState('');
  const [report, setReport] = useState('');
  const [evidence, setEvidence] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]);

  useEffect(() => {
    // Fetch stats and reviews on load
    fetch('http://localhost:8000/api/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Error fetching stats:", err));

    fetch('http://localhost:8000/api/reviews?limit=20')
      .then(res => res.json())
      .then(data => setReviews(data))
      .catch(err => console.error("Error fetching reviews:", err));

    fetch('http://localhost:8000/api/trends/heatmap')
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
      const res = await fetch('http://localhost:8000/api/query', {
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
      setReport("Failed to generate insight. Ensure FastAPI backend is running.");
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

        {/* Evidence Viewer */}
        <section className="glass-panel">
          <h2><MessageSquare size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle', color: '#10b981' }}/> Recent Feedback</h2>
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
            {reviews.length === 0 && <p>No reviews fetched.</p>}
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
