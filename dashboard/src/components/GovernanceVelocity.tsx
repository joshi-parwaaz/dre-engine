import { useEffect, useState, useCallback } from 'react'

interface AuditEvent {
  timestamp: string
  event_type: string
  severity: string
}

interface VelocityProps {
  recentHours?: number
}

export default function GovernanceVelocity({ recentHours = 24 }: VelocityProps) {
  const [auditData, setAuditData] = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)

  const fetchAuditData = useCallback(async () => {
    try {
      const response = await fetch('/api/audit/recent?limit=100')
      if (response.ok) {
        const data = await response.json()
        console.log('📊 GovernanceVelocity: Fetched audit data', data)
        console.log('📊 Events count:', data.events?.length || 0)
        setAuditData(data.events || [])
      }
    } catch (error) {
      console.error('Failed to fetch audit data:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Fetch once on mount
    void fetchAuditData();
    
    // Expose refresh function for parent to call on file changes
    (window as any).refreshGovernanceVelocity = fetchAuditData;
    
    return () => {
      delete (window as any).refreshGovernanceVelocity
    }
  }, [fetchAuditData])

  // Group events by hour
  const hourlyBuckets = Array.from({ length: recentHours }, (_, i) => {
    const hourAgo = new Date(Date.now() - (recentHours - i - 1) * 3600000)
    return {
      hour: hourAgo.getHours(),
      label: hourAgo.toLocaleTimeString('en-US', { hour: '2-digit', hour12: false }),
      checks: 0,
      halts: 0,
      overrides: 0
    }
  })

  auditData.forEach(event => {
    const eventTime = new Date(event.timestamp)
    const hoursDiff = Math.floor((Date.now() - eventTime.getTime()) / 3600000)
    
    if (hoursDiff < recentHours) {
      const bucket = hourlyBuckets[recentHours - hoursDiff - 1]
      if (bucket) {
        // Count HALTs and OVERRIDEs
        if (event.event_type === 'HALT') {
          bucket.halts++
          bucket.checks++
        }
        if (event.event_type === 'OVERRIDE') {
          bucket.overrides++
        }
        // Count other governance events as checks
        if (event.event_type === 'GOVERNANCE_CHECK' || event.event_type === 'CHECK') {
          bucket.checks++
        }
      }
    }
  })

  const maxChecks = Math.max(...hourlyBuckets.map(b => b.checks), 1)
  const totalChecks = hourlyBuckets.reduce((sum, b) => sum + b.checks, 0)
  const totalHalts = hourlyBuckets.reduce((sum, b) => sum + b.halts, 0)
  const totalOverrides = hourlyBuckets.reduce((sum, b) => sum + b.overrides, 0)
  const bypassRate = totalHalts > 0 ? ((totalOverrides / totalHalts) * 100).toFixed(1) : '0.0'

  // Also count raw totals from audit data for comparison
  const rawHaltCount = auditData.filter(e => e.event_type === 'HALT').length
  const rawOverrideCount = auditData.filter(e => e.event_type === 'OVERRIDE' || e.event_type === 'OVERRIDE_REQUEST').length

  console.log('📊 GovernanceVelocity metrics:', { 
    totalChecks, 
    totalHalts, 
    totalOverrides, 
    bypassRate,
    rawHaltCount,
    rawOverrideCount,
    auditDataLength: auditData.length 
  })
  console.log('📊 Hourly buckets:', hourlyBuckets)
  console.log('📊 Sample event:', auditData[0])

  return (
    <div className="fade-in" style={{ 
      padding: '2rem 0', 
      pointerEvents: 'auto',
      height: '100%'
    }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ 
          fontSize: '1.25rem', 
          fontWeight: '400',
          color: 'var(--text-primary)',
          marginBottom: '0.5rem',
          letterSpacing: '0.3px'
        }}>
          Governance Velocity
        </h3>
        <p style={{ 
          fontSize: '0.85rem', 
          color: 'var(--text-secondary)',
          margin: 0
        }}>
          Cycles vs Bypasses - Monitor Standards Adherence
          {auditData.length > 0 && (
            <span style={{ marginLeft: '1rem', color: '#10b981' }}>
              • {auditData.length} events loaded
            </span>
          )}
          {auditData.length === 0 && !loading && (
            <span style={{ marginLeft: '1rem', color: '#ef4444' }}>
              • No events found
            </span>
          )}
        </p>
      </div>

      {/* Metrics cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(3, 1fr)', 
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        <div style={{ 
          background: 'transparent',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          borderRadius: '6px',
          padding: '1rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: '300', color: '#3b82f6', letterSpacing: '0.5px' }}>
            {loading ? '...' : totalChecks}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: '300', letterSpacing: '0.3px' }}>
            Total Cycles
          </div>
        </div>

        <div style={{ 
          background: 'transparent',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '6px',
          padding: '1rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: '300', color: '#ef4444', letterSpacing: '0.5px' }}>
            {loading ? '...' : (rawHaltCount > 0 ? rawHaltCount : totalHalts)}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: '300', letterSpacing: '0.3px' }}>
            HALTs
          </div>
        </div>

        <div style={{ 
          background: 'transparent',
          border: '1px solid rgba(245, 158, 11, 0.2)',
          borderRadius: '6px',
          padding: '1rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: '300', color: '#f59e0b', letterSpacing: '0.5px' }}>
            {loading ? '...' : bypassRate}%
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: '300', letterSpacing: '0.3px' }}>
            Bypass Rate
          </div>
        </div>
      </div>

      {/* Timeline chart */}
      <div style={{ 
        position: 'relative',
        background: 'rgba(0, 0, 0, 0.2)',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        padding: '1rem',
        height: '200px'
      }}>
        {loading ? (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            height: '100%',
            color: 'var(--text-secondary)'
          }}>
            Loading...
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'flex-end', height: '100%', gap: '2px' }}>
            {hourlyBuckets.map((bucket, index) => {
              const height = (bucket.checks / maxChecks) * 100
              const haltHeight = bucket.halts > 0 ? (bucket.halts / bucket.checks) * height : 0
              const overrideHeight = bucket.overrides > 0 ? (bucket.overrides / bucket.checks) * height : 0

              return (
                <div
                  key={index}
                  style={{
                    flex: 1,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'flex-end',
                    position: 'relative'
                  }}
                  title={`${bucket.label}: ${bucket.checks} cycles, ${bucket.halts} halts, ${bucket.overrides} overrides`}
                >
                  <div style={{
                    background: 'linear-gradient(to top, #3b82f6, #60a5fa)',
                    height: `${height}%`,
                    borderRadius: '4px 4px 0 0',
                    position: 'relative',
                    minHeight: bucket.checks > 0 ? '2px' : '0'
                  }}>
                    {/* HALT overlay */}
                    {haltHeight > 0 && (
                      <div style={{
                        position: 'absolute',
                        bottom: 0,
                        width: '100%',
                        height: `${(haltHeight / height) * 100}%`,
                        background: 'rgba(239, 68, 68, 0.7)',
                        borderRadius: '4px 4px 0 0'
                      }} />
                    )}
                    {/* Override overlay */}
                    {overrideHeight > 0 && (
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        width: '100%',
                        height: `${(overrideHeight / height) * 100}%`,
                        background: 'rgba(245, 158, 11, 0.7)',
                        borderRadius: '4px 4px 0 0'
                      }} />
                    )}
                  </div>
                  {index % 4 === 0 && (
                    <div style={{
                      fontSize: '0.65rem',
                      color: 'var(--text-secondary)',
                      textAlign: 'center',
                      marginTop: '4px'
                    }}>
                      {bucket.label}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Legend */}
      <div style={{ 
        marginTop: '1rem', 
        display: 'flex', 
        gap: '1rem',
        fontSize: '0.75rem',
        justifyContent: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#3b82f6' }} />
          <span style={{ color: 'var(--text-secondary)' }}>Cycles</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#ef4444' }} />
          <span style={{ color: 'var(--text-secondary)' }}>HALTs</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: '#f59e0b' }} />
          <span style={{ color: 'var(--text-secondary)' }}>Overrides</span>
        </div>
      </div>
    </div>
  )
}
