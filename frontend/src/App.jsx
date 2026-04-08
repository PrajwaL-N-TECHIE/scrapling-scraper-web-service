import React, { useState } from 'react';
import axios from 'axios';
import { 
  Search, Upload, Download, Loader2, 
  Info, Package, Trash2, Copy, Check, ExternalLink
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = 'http://localhost:8000';

function App() {
  const [url, setUrl] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [batchUrls, setBatchUrls] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  const ensureProtocol = (u) => {
    if (!u) return u;
    if (u.startsWith('http://') || u.startsWith('https://')) return u;
    // Handle cases like 'https.www.' which might be a typo for 'https://www.'
    if (u.startsWith('https.')) return u.replace('https.', 'https://');
    return `https://${u}`;
  };

  const handleSingleScrape = async () => {
    if (!url) return;
    const sanitizedUrl = ensureProtocol(url.trim());
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_BASE}/scrape`, { url: sanitizedUrl });
      setResults([response.data, ...results]);
      setUrl('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Scraping failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBatchScrape = async () => {
    const urls = batchUrls.split('\n')
      .map(u => u.trim())
      .filter(Boolean)
      .map(u => ensureProtocol(u));
      
    if (!urls.length) return;
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_BASE}/bulk-scrape`, { urls });
      setResults([...response.data, ...results]);
      setBatchUrls('');
    } catch (err) {
      console.error('Batch Error:', err);
      setError('Batch processing failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post(`${API_BASE}/upload-csv`, formData);
      setResults([...response.data, ...results]);
    } catch (err) {
      console.error('Upload Error:', err);
      setError('File upload failed.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const downloadCSV = () => {
    if (!results.length) return;
    const headers = ['Company Name', 'Industry', 'About', 'Products', 'Website', 'LinkedIn', 'Twitter', 'Facebook', 'Instagram', 'YouTube'];
    const csvContent = "data:text/csv;charset=utf-8," 
      + headers.join(",") + "\n"
      + results.map(r => [
          `"${(r.company_name || '').replaceAll('"', '""')}"`,
          `"${(r.industry || '').replaceAll('"', '""')}"`,
          `"${(r.about || '').replaceAll('"', '""')}"`,
          `"${(r.products || '').replaceAll('"', '""')}"`,
          `"${(r.website || '').replaceAll('"', '""')}"`,
          `"${(r.socials?.linkedin || '').replaceAll('"', '""')}"`,
          `"${(r.socials?.twitter || '').replaceAll('"', '""')}"`,
          `"${(r.socials?.facebook || '').replaceAll('"', '""')}"`,
          `"${(r.socials?.instagram || '').replaceAll('"', '""')}"`,
          `"${(r.socials?.youtube || '').replaceAll('"', '""')}"`
        ].join(",")).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `scraped_data_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="container" style={{ paddingBottom: '10rem' }}>
      <header style={{ textAlign: 'center', marginBottom: '5rem' }}>
        <motion.h1 
          className="primary-gradient" 
          style={{ fontSize: '4.5rem', marginBottom: '1.2rem', fontWeight: '900', letterSpacing: '-0.02em' }}
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
        >
          AI Data Enlarger
        </motion.h1>
        <motion.p 
          style={{ color: '#64748b', fontSize: '1.4rem', maxWidth: '700px', margin: '0 auto', fontWeight: '500' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          Hyper-accurate company intelligence powered by Scrapling & Llama 3.3
        </motion.p>
      </header>

      <div className="grid-layout">
        <motion.div 
          className="glass-card"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '2rem', fontSize: '1.8rem', fontWeight: '800' }}>
            <div style={{ background: 'rgba(129, 140, 248, 0.15)', padding: '0.6rem', borderRadius: '12px' }}>
              <Search size={28} color="#818cf8" />
            </div> 
            Single URL Analysis
          </h2>
          <div style={{ display: 'flex', gap: '0.8rem' }}>
            <input 
              type="text" 
              placeholder="https://example.com" 
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSingleScrape()}
            />
            <button 
              className="btn-primary" 
              onClick={handleSingleScrape}
              disabled={loading || !url}
            >
              {loading ? <Loader2 className="animate-spin" /> : "Analyze"}
            </button>
          </div>
          {error && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ color: '#fb7185', marginTop: '1.2rem', fontSize: '1rem', fontWeight: '600' }}>{error}</motion.p>}
        </motion.div>

        <motion.div 
          className="glass-card"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '2rem', fontSize: '1.8rem', fontWeight: '800' }}>
            <div style={{ background: 'rgba(192, 132, 252, 0.15)', padding: '0.6rem', borderRadius: '12px' }}>
              <Upload size={28} color="#c084fc" />
            </div>
            Batch Intelligence
          </h2>
          <textarea 
            rows="2"
            placeholder="Paste URLs (one per line)..."
            value={batchUrls}
            onChange={(e) => setBatchUrls(e.target.value)}
            style={{ marginBottom: '1.5rem' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label className="btn-primary" style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', boxShadow: 'none' }}>
              <input type="file" hidden accept=".csv, .txt" onChange={handleFileUpload} />
              <Upload size={20} />
              Upload Source
            </label>
            <button 
              className="btn-primary" 
              onClick={handleBatchScrape}
              disabled={loading || !batchUrls}
            >
              Start Batch
            </button>
          </div>
        </motion.div>
      </div>

      <AnimatePresence>
        {results.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ marginTop: '6rem' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end', marginBottom: '2.5rem', padding: '0 1rem' }}>
              <div>
                <h2 style={{ fontSize: '2.2rem', fontWeight: '800', marginBottom: '0.5rem' }}>Extraction Results</h2>
                <p style={{ color: '#64748b', fontSize: '1.1rem' }}>Identified {results.length} companies from the sources provided.</p>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button 
                  className="btn-primary" 
                  onClick={() => setResults([])} 
                  style={{ background: 'rgba(251, 113, 133, 0.1)', color: '#fb7185', border: '1px solid rgba(251, 113, 133, 0.2)', boxShadow: 'none' }}
                >
                  <Trash2 size={20} />
                  Clear Data
                </button>
                <button className="btn-primary" onClick={downloadCSV}>
                  <Download size={20} /> Download Intelligence
                </button>
              </div>
            </div>

            <div className="results-grid">
              {results.map((res, i) => (
                <motion.div 
                  key={`${res.website}-${i}`}
                  className="info-card glass-card"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <div className="card-header">
                    <h3 className="card-title">{res.company_name}</h3>
                    <span className="badge badge-success">{res.industry}</span>
                  </div>

                  <div className="card-section">
                    <span className="card-label"><Info size={16} color="#818cf8" /> About the Company</span>
                    <p className="card-content">{res.about}</p>
                  </div>

                  <div className="card-section">
                    <span className="card-label"><Package size={16} color="#c084fc" /> Core Products & Services</span>
                    <p className="card-content" style={{ color: '#64748b', fontStyle: res.products === 'N/A' ? 'italic' : 'normal' }}>
                      {res.products}
                    </p>
                  </div>

                  {res.socials && Object.values(res.socials).some(v => v !== 'N/A') && (
                    <div className="card-section">
                      <span className="card-label">Social Presence</span>
                      <div style={{ display: 'flex', gap: '0.8rem', marginTop: '0.5rem' }}>
                        {res.socials.linkedin !== 'N/A' && <a href={res.socials.linkedin} target="_blank" rel="noreferrer" title="LinkedIn"><ExternalLink size={20} color="#0077b5" /></a>}
                        {res.socials.twitter !== 'N/A' && <a href={res.socials.twitter} target="_blank" rel="noreferrer" title="Twitter"><ExternalLink size={20} color="#1da1f2" /></a>}
                        {res.socials.facebook !== 'N/A' && <a href={res.socials.facebook} target="_blank" rel="noreferrer" title="Facebook"><ExternalLink size={20} color="#1877f2" /></a>}
                        {res.socials.instagram !== 'N/A' && <a href={res.socials.instagram} target="_blank" rel="noreferrer" title="Instagram"><ExternalLink size={20} color="#e4405f" /></a>}
                        {res.socials.youtube !== 'N/A' && <a href={res.socials.youtube} target="_blank" rel="noreferrer" title="YouTube"><ExternalLink size={20} color="#ff0000" /></a>}
                      </div>
                    </div>
                  )}

                  <div className="card-footer">
                    <button 
                      className="copy-btn" 
                      onClick={() => copyToClipboard(`${res.company_name}\n${res.about}`, i)}
                    >
                      {copiedId === i ? <Check size={16} color="#4ade80" /> : <Copy size={16} />}
                      {copiedId === i ? 'Copied' : 'Copy Overview'}
                    </button>
                    <a href={res.website} target="_blank" rel="noopener noreferrer" className="card-link">
                      <ExternalLink size={18} />
                      {(() => {
                        try {
                          return new URL(res.website).hostname.replace('www.', '');
                        } catch {
                          return res.website?.replace('https://', '').replace('http://', '').split('/')[0] || 'Link';
                        }
                      })()}
                    </a>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {(loading && results.length === 0) && (
        <div style={{ textAlign: 'center', marginTop: '8rem' }}>
           <Loader2 size={64} className="animate-spin" style={{ color: '#818cf8', opacity: 0.8 }} />
           <p style={{ marginTop: '2rem', color: '#64748b', fontSize: '1.2rem', fontWeight: '500' }}>Assembling intelligence profiles...</p>
        </div>
      )}
    </div>
  );
}

export default App;
