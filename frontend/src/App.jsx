import { useState, useEffect } from 'react';
import { Sparkles, MessageSquare, Users, BarChart2, CheckCircle2, TrendingUp, AlertTriangle, User, Download, Copy } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import ReactMarkdown from 'react-markdown';

const rawApiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE = rawApiBase.replace(/\/$/, '');

function App() {
  const [query, setQuery] = useState('');
  const [report, setReport] = useState('');
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
    } catch (err) {
      console.error(err);
      setReport(`**Error**: Failed to generate insight. ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Helper to parse the report into sections
  const parseReport = (rawReport) => {
    if (!rawReport) return { sections: {}, evidenceMetrics: null };

    // 1. Separate Evidence Layer from the main report
    const evidenceSplit = rawReport.split('--- Evidence Layer ---');
    const mainReportText = evidenceSplit[0].trim();
    let evidenceMetrics = null;

    if (evidenceSplit.length > 1) {
      const evidenceText = evidenceSplit[1];
      evidenceMetrics = {
        confidence: evidenceText.match(/Confidence Score:\s*(\d+%)/)?.[1] || 'N/A',
        count: evidenceText.match(/Evidence Count:\s*(\d+)/)?.[1] || '0',
        supporting: evidenceText.match(/Supporting Review Count:\s*(\d+)/)?.[1] || '0',
        sources: evidenceText.match(/Source Distribution:\s*(.+)/)?.[1] || 'Unknown'
      };
    }

    // 2. Parse main report by Headings
    const sections = {};
    const lines = mainReportText.split('\n');
    let currentHeader = 'Intro';
    sections[currentHeader] = [];

    lines.forEach(line => {
      // The prompt outputs headers like "- Key Findings" or "Key Findings:"
      // We look for known headers
      const lowerLine = line.toLowerCase().replace(/^- /g, '').trim();
      
      if (lowerLine.includes('key finding')) {
        currentHeader = 'Key Findings';
        sections[currentHeader] = [];
      } else if (lowerLine.includes('pain point')) {
        currentHeader = 'Pain Points';
        sections[currentHeader] = [];
      } else if (lowerLine.includes('product opportunit')) {
        currentHeader = 'Product Opportunities';
        sections[currentHeader] = [];
      } else if (lowerLine.includes('recommend')) {
        currentHeader = 'Recommended Actions';
        sections[currentHeader] = [];
      } else if (line.trim() !== '') {
        sections[currentHeader].push(line);
      }
    });

    // Format section text
    Object.keys(sections).forEach(key => {
      sections[key] = sections[key].join('\n');
    });

    return { sections, evidenceMetrics, rawMainText: mainReportText };
  };

  const parsedData = parseReport(report);
  
  const getCleanReport = () => {
    if (!parsedData.evidenceMetrics) return report;
    return `${parsedData.rawMainText}\n\n--- Evidence Layer ---\nConfidence Score: ${parsedData.evidenceMetrics.confidence}\nSupporting Reviews: ${parsedData.evidenceMetrics.supporting}`;
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(getCleanReport());
    alert('Report copied to clipboard!');
  };

  const downloadReport = () => {
    const blob = new Blob([getCleanReport()], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Blinkit_AI_Report.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Transform Personas data (Top 5 only)
  const processedCount = stats?.processed_reviews || 1;
  const topPersonas = stats?.segments 
    ? [...stats.segments].sort((a, b) => b.value - a.value).slice(0, 5).map(p => ({
        ...p,
        label: `${p.name} (${p.value} | ${((p.value / processedCount) * 100).toFixed(1)}%)`,
        percentage: ((p.value / processedCount) * 100).toFixed(1)
      }))
    : [];

  const PersonaTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '12px', color: '#f8fafc', fontSize: '13px' }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 'bold' }}>{data.name}</p>
          <p style={{ margin: '4px 0', color: '#a1a1aa' }}>Reviews: <span style={{ color: '#f8fafc' }}>{data.value}</span></p>
          <p style={{ margin: '0', color: '#a1a1aa' }}>Share: <span style={{ color: '#f8fafc' }}>{data.percentage}%</span></p>
        </div>
      );
    }
    return null;
  };

  const TopicTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const totalReviews = payload.reduce((sum, entry) => sum + (entry.value || 0), 0);
      return (
        <div style={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '12px', color: '#f8fafc', fontSize: '13px', minWidth: '160px' }}>
          <p style={{ margin: '0 0 12px 0', fontWeight: 'bold', borderBottom: '1px solid #27272a', paddingBottom: '8px' }}>{label}</p>
          {payload.map((entry, index) => {
            const val = entry.value || 0;
            const percentage = totalReviews > 0 ? ((val / totalReviews) * 100).toFixed(0) : 0;
            if (val === 0) return null;
            return (
              <div key={index} style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <div style={{ width: '8px', height: '8px', backgroundColor: entry.color, borderRadius: '50%' }}></div>
                  <span style={{ color: '#a1a1aa' }}>{entry.name}</span>
                </div>
                <div style={{ paddingLeft: '14px' }}>
                  <span style={{ color: '#f8fafc', marginRight: '8px' }}>{val} Reviews</span>
                  <span style={{ color: '#f8fafc', fontWeight: 'bold' }}>{percentage}%</span>
                </div>
              </div>
            );
          })}
        </div>
      );
    }
    return null;
  };

  let aiSummary = "";
  if (topPersonas.length > 0 && heatmapData.length > 0) {
    const largestPersona = topPersonas[0];
    const personaTopics = heatmapData.find(h => h.segment === largestPersona.name);
    if (personaTopics) {
      let maxCount = 0;
      let topTopic = "";
      Object.entries(personaTopics).forEach(([key, val]) => {
        if (key !== 'segment' && typeof val === 'number' && val > maxCount) {
          maxCount = val;
          topTopic = key;
        }
      });
      if (topTopic) {
        aiSummary = `${largestPersona.name}s represent the largest user segment (${largestPersona.percentage}%). ${topTopic}-related feedback dominates this persona, indicating a high-impact opportunity for product improvements.`;
      }
    }
  }

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
          <div className="kpi-card" title={stats.last_updated ? `Last Updated: ${new Date(stats.last_updated).toLocaleString()}` : ''}>
            <span className="kpi-label">Total Raw Reviews</span>
            <span className="kpi-value">{stats.total_reviews}</span>
            {stats.last_updated && (
              <span style={{ fontSize: '0.75rem', color: '#a1a1aa', marginTop: '4px', display: 'block' }}>
                Updated: {new Date(stats.last_updated).toLocaleString()}
              </span>
            )}
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Reviews Processed</span>
            <span className="kpi-value">{stats.processed_reviews}</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Extracted Themes</span>
            <span className="kpi-value">{stats.topics_identified}</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Identified Personas</span>
            <span className="kpi-value">{stats.user_segments}</span>
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

      {/* Loading */}
      {loading && (
        <div className="loading full-width">
          <Sparkles className="spinner" size={18} /> Synthesizing millions of data points into product insights...
        </div>
      )}

      {/* Structured AI Report */}
      {report && !loading && (
        <section className="ai-report-container full-width">
          <div className="insight-cards-grid">
            
            {/* Key Findings */}
            {(parsedData.sections['Key Findings'] || parsedData.sections['Intro']) && (
              <div className="insight-card">
                <div className="insight-card-header" style={{ color: '#10B981' }}>
                  🟢 Key Findings
                </div>
                <div>
                  <ReactMarkdown>{parsedData.sections['Key Findings'] || parsedData.sections['Intro']}</ReactMarkdown>
                </div>
              </div>
            )}

            {/* Pain Points */}
            {parsedData.sections['Pain Points'] && (
              <div className="insight-card">
                <div className="insight-card-header" style={{ color: '#f43f5e' }}>
                  🔴 Top Pain Points
                </div>
                <div>
                  <ReactMarkdown>{parsedData.sections['Pain Points']}</ReactMarkdown>
                </div>
              </div>
            )}

            {/* Product Opportunities */}
            {parsedData.sections['Product Opportunities'] && (
              <div className="insight-card">
                <div className="insight-card-header" style={{ color: '#F8CB46' }}>
                  💡 Product Opportunities
                </div>
                <div>
                  <ReactMarkdown>{parsedData.sections['Product Opportunities']}</ReactMarkdown>
                </div>
              </div>
            )}

            {/* Recommended Actions */}
            {parsedData.sections['Recommended Actions'] && (
              <div className="insight-card">
                <div className="insight-card-header" style={{ color: '#3b82f6' }}>
                  ✅ Recommended Actions
                </div>
                <div>
                  <ReactMarkdown>{parsedData.sections['Recommended Actions']}</ReactMarkdown>
                </div>
              </div>
            )}
            
            {/* Fallback if parsing completely fails */}
            {Object.keys(parsedData.sections).length <= 1 && !parsedData.sections['Key Findings'] && (
              <div className="insight-card" style={{ gridColumn: '1 / -1' }}>
                <div className="insight-card-header" style={{ color: '#F8CB46' }}>
                  <Sparkles size={16} /> Insight Analysis
                </div>
                <div>
                  <ReactMarkdown>{parsedData.rawMainText}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>

          {/* Parsed Evidence Metrics Bar */}
          {parsedData.evidenceMetrics && (
            <div className="evidence-metrics-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '16px' }}>
                <div className="metric-badge" title="AI confidence based on consistency of supporting reviews">
                  <span className="metric-label">Confidence</span>
                  <span className="metric-value highlight">{parsedData.evidenceMetrics.confidence}</span>
                </div>
                <div className="metric-badge">
                  <span className="metric-label">Supporting Reviews</span>
                  <span className="metric-value">{parsedData.evidenceMetrics.supporting}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={copyToClipboard} className="secondary-button" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '13px' }}>
                  <Copy size={14} /> Copy Summary
                </button>
                <button onClick={downloadReport} className="primary-button" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '13px' }}>
                  <Download size={14} /> Download Report
                </button>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Visual Analytics */}
      <div className="dashboard-grid" style={{ marginTop: '32px' }}>
        
        {/* Top Personas Horizontal Bar Chart */}
        <section className="glass-panel">
          <h2><Users size={20} color="#3b82f6" /> Top 5 User Personas</h2>
          <div style={{ width: '100%', height: 280, marginTop: '20px' }}>
            {topPersonas.length > 0 ? (
              <ResponsiveContainer>
                <BarChart data={topPersonas} layout="vertical" margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={true} vertical={false} />
                  <XAxis type="number" stroke="#a1a1aa" hide />
                  <YAxis dataKey="label" type="category" stroke="#f8fafc" width={220} tick={{ fontSize: 12 }} />
                  <Tooltip content={<PersonaTooltip />} cursor={{fill: 'rgba(255,255,255,0.05)'}}/>
                  <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <strong style={{ color: '#a1a1aa' }}>Insufficient processed reviews to generate meaningful visualization.</strong>
              </div>
            )}
          </div>
        </section>

        {/* Top Topics by Volume (Replacing Heatmap) */}
        <section className="glass-panel">
          <h2><BarChart2 size={20} color="#10b981" /> Topic Distribution by Persona</h2>
          <div style={{ width: '100%', height: 280, marginTop: '20px' }}>
            {heatmapData.length > 0 ? (
              <ResponsiveContainer>
                <BarChart data={heatmapData} margin={{ top: 20, right: 10, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="segment" stroke="#a1a1aa" tick={{ fontSize: 11 }} label={{ value: 'Persona', position: 'insideBottom', offset: -10, fill: '#a1a1aa' }} />
                  <YAxis stroke="#a1a1aa" tick={{ fontSize: 11 }} label={{ value: 'Review Count', angle: -90, position: 'insideLeft', fill: '#a1a1aa', offset: 15 }} />
                  <Tooltip content={<TopicTooltip />} cursor={{fill: 'rgba(255,255,255,0.05)'}} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '20px' }}/>
                  <Bar dataKey="Pricing" stackId="a" fill="#3b82f6" />
                  <Bar dataKey="Delivery" stackId="a" fill="#10b981" />
                  <Bar dataKey="Customer Service" stackId="a" fill="#f43f5e" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <strong style={{ color: '#a1a1aa' }}>Insufficient processed reviews to generate meaningful visualization.</strong>
              </div>
            )}
          </div>
        </section>

      </div>

      {/* AI Summary */}
      <section className="glass-panel full-width" style={{ marginTop: '24px', marginBottom: '24px' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '0 0 16px 0', fontSize: '1.1rem', color: '#f8fafc' }}>
          <Sparkles size={18} color="#F8CB46" /> Executive AI Summary
        </h3>
        <p style={{ color: '#e4e4e7', lineHeight: '1.6', margin: 0 }}>
          {stats?.processed_reviews > 0 && aiSummary ? aiSummary : <strong style={{ color: '#a1a1aa' }}>Insufficient processed reviews to generate an executive summary.</strong>}
        </p>
      </section>


    </div>
  );
}

export default App;
