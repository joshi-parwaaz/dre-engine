import { useState, useEffect } from 'react'

interface AuditEvent {
  timestamp: string
  session_id: string
  severity: 'INFO' | 'WARN' | 'CRITICAL'
  event_type: string
  assertion_id: string
  user_anchor: string
  details: Record<string, any>
}

interface AuditSummary {
  total_events: number
  by_severity: {
    INFO: number
    WARN: number
    CRITICAL: number
  }
  halt_count: number
  override_count: number
  last_24hrs: number
}

interface AuditLogProps {
  onClose: () => void
}

export default function AuditLog({ onClose }: AuditLogProps) {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [summary, setSummary] = useState<AuditSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [severityFilter, setSeverityFilter] = useState<string>('ALL')
  const [page, setPage] = useState(0)
  const limit = 50

  useEffect(() => {
    fetchSummary()
    fetchEvents()
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(() => {
      fetchSummary()
      fetchEvents()
    }, 10000)
    
    return () => clearInterval(interval)
  }, [page])

  const fetchSummary = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/audit/summary')
      const data = await res.json()
      setSummary(data)
    } catch (err) {
      console.error('Failed to fetch audit summary:', err)
    }
  }

  const fetchEvents = async () => {
    try {
      setLoading(true)
      const offset = page * limit
      const res = await fetch(`http://127.0.0.1:8000/api/audit/recent?limit=${limit}&offset=${offset}`)
      const data = await res.json()
      setEvents(data.events || [])
    } catch (err) {
      console.error('Failed to fetch audit events:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredEvents = severityFilter === 'ALL' 
    ? events 
    : events.filter(e => e.severity === severityFilter)

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return '#ef4444'
      case 'WARN': return '#f59e0b'
      case 'INFO': return '#10b981'
      default: return '#6b7280'
    }
  }

  const formatTimestamp = (iso: string) => {
    const date = new Date(iso)
    return date.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div style={{
      position: 'fixed',
      right: 0,
      top: 0,
      height: '100vh',
      width: '600px',
      background: 'rgba(10, 10, 20, 0.95)',
      backdropFilter: 'blur(20px)',
      borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
      boxShadow: '-10px 0 40px rgba(0, 0, 0, 0.5)',
      overflowY: 'auto',
      zIndex: 1000,
      animation: 'slideIn 0.3s ease-out',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>

      {/* Header */}
      <div style={{ 
        padding: '1.5rem', 
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        position: 'sticky',
        top: 0,
        background: 'rgba(10, 10, 20, 0.95)',
        backdropFilter: 'blur(20px)',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#fff', margin: 0 }}>
            🔍 Audit Log
          </h2>
          <button 
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: 'none',
              color: '#fff',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            ✕ Close
          </button>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', marginTop: '1rem' }}>
            <div style={{ 
              background: 'rgba(239, 68, 68, 0.1)', 
              padding: '0.75rem', 
              borderRadius: '8px',
              border: '1px solid rgba(239, 68, 68, 0.3)'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#ef4444', marginBottom: '0.25rem' }}>CRITICAL</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#fff' }}>
                {summary.by_severity.CRITICAL}
              </div>
            </div>
            <div style={{ 
              background: 'rgba(245, 158, 11, 0.1)', 
              padding: '0.75rem', 
              borderRadius: '8px',
              border: '1px solid rgba(245, 158, 11, 0.3)'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#f59e0b', marginBottom: '0.25rem' }}>WARNINGS</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#fff' }}>
                {summary.by_severity.WARN}
              </div>
            </div>
            <div style={{ 
              background: 'rgba(16, 185, 129, 0.1)', 
              padding: '0.75rem', 
              borderRadius: '8px',
              border: '1px solid rgba(16, 185, 129, 0.3)'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#10b981', marginBottom: '0.25rem' }}>LAST 24 HRS</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#fff' }}>
                {summary.last_24hrs}
              </div>
            </div>
            <div style={{ 
              background: 'rgba(107, 114, 128, 0.1)', 
              padding: '0.75rem', 
              borderRadius: '8px',
              border: '1px solid rgba(107, 114, 128, 0.3)'
            }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>OVERRIDES</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#fff' }}>
                {summary.override_count}
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
          {['ALL', 'CRITICAL', 'WARN', 'INFO'].map(sev => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              style={{
                background: severityFilter === sev ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#fff',
                padding: '0.4rem 0.8rem',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: severityFilter === sev ? '600' : '400'
              }}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Event List */}
      <div style={{ padding: '1rem' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#9ca3af' }}>
            Loading events...
          </div>
        ) : filteredEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#9ca3af' }}>
            No events found
          </div>
        ) : (
          filteredEvents.map((event, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '0.75rem'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                <div>
                  <span style={{ 
                    background: getSeverityColor(event.severity),
                    color: '#fff',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: '600',
                    marginRight: '0.5rem'
                  }}>
                    {event.severity}
                  </span>
                  <span style={{ 
                    color: '#9ca3af',
                    fontSize: '0.75rem'
                  }}>
                    {event.event_type}
                  </span>
                </div>
                <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>
                  {formatTimestamp(event.timestamp)}
                </span>
              </div>
              
              <div style={{ fontSize: '0.85rem', color: '#e5e7eb', marginBottom: '0.5rem' }}>
                <strong>Assertion:</strong> {event.assertion_id}
              </div>
              
              <div style={{ fontSize: '0.85rem', color: '#9ca3af' }}>
                <strong>User:</strong> {event.user_anchor}
              </div>
              
              {event.details && Object.keys(event.details).length > 0 && (
                <details style={{ marginTop: '0.5rem' }}>
                  <summary style={{ 
                    cursor: 'pointer', 
                    fontSize: '0.75rem', 
                    color: '#6b7280',
                    userSelect: 'none'
                  }}>
                    View Details
                  </summary>
                  <pre style={{ 
                    background: 'rgba(0, 0, 0, 0.3)',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    color: '#9ca3af',
                    marginTop: '0.5rem',
                    overflow: 'auto',
                    maxHeight: '200px'
                  }}>
                    {JSON.stringify(event.details, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          ))
        )}

        {/* Pagination */}
        {!loading && filteredEvents.length > 0 && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            gap: '0.5rem',
            marginTop: '1rem',
            paddingBottom: '1rem'
          }}>
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              style={{
                background: page === 0 ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: page === 0 ? '#6b7280' : '#fff',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                cursor: page === 0 ? 'not-allowed' : 'pointer',
                fontSize: '0.85rem'
              }}
            >
              ← Previous
            </button>
            <span style={{ 
              display: 'flex', 
              alignItems: 'center', 
              color: '#9ca3af',
              fontSize: '0.85rem'
            }}>
              Page {page + 1}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={filteredEvents.length < limit}
              style={{
                background: filteredEvents.length < limit ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: filteredEvents.length < limit ? '#6b7280' : '#fff',
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                cursor: filteredEvents.length < limit ? 'not-allowed' : 'pointer',
                fontSize: '0.85rem'
              }}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
