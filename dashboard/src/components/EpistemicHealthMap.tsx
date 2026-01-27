interface Assertion {
  id: string
  logical_name: string
  owner_role: string
  gate_status: {
    freshness: string
    stability: string
    alignment: string
  }
}

interface HealthMapProps {
  assertions: Assertion[]
}

export default function EpistemicHealthMap({ assertions }: HealthMapProps) {
  const getHealthStatus = (freshness: string, stability: string, alignment: string) => {
    const statuses = [freshness, stability, alignment]
    if (statuses.includes('HALT')) return { status: 'CRITICAL', color: '#ef4444', label: 'Critical Issue' }
    if (statuses.includes('WARN')) return { status: 'WARNING', color: '#f59e0b', label: 'Warning' }
    return { status: 'HEALTHY', color: '#10b981', label: 'Healthy' }
  }

  const healthyCount = assertions.filter(a => {
    const statuses = [a.gate_status.freshness, a.gate_status.stability, a.gate_status.alignment]
    return !statuses.includes('HALT') && !statuses.includes('WARN')
  }).length

  const warningCount = assertions.filter(a => {
    const statuses = [a.gate_status.freshness, a.gate_status.stability, a.gate_status.alignment]
    return !statuses.includes('HALT') && statuses.includes('WARN')
  }).length

  const criticalCount = assertions.filter(a => {
    const statuses = [a.gate_status.freshness, a.gate_status.stability, a.gate_status.alignment]
    return statuses.includes('HALT')
  }).length

  return (
    <div className="glass fade-in" style={{ 
      padding: '2rem 0', 
      pointerEvents: 'auto',
      height: '100%'
    }}>
      <div style={{ marginBottom: '2rem', padding: '0 2rem' }}>
        <h3 style={{ 
          fontSize: '1.25rem', 
          fontWeight: '400',
          color: 'var(--text-primary)',
          marginBottom: '0.5rem',
          letterSpacing: '0.3px'
        }}>
          Data Health Status
        </h3>
        <p style={{ 
          fontSize: '0.85rem', 
          color: 'var(--text-secondary)',
          margin: 0,
          fontWeight: '300',
          letterSpacing: '0.3px'
        }}>
          Real-time assertion monitoring
        </p>
      </div>

      {/* Summary cards */}
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '1rem',
        marginBottom: '2rem',
        padding: '0 2rem'
      }}>
        <div style={{
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '6px',
          padding: '1rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: '300', color: '#10b981', letterSpacing: '0.5px' }}>
            {healthyCount}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: '300', letterSpacing: '0.3px' }}>
            Healthy
          </div>
        </div>
        <div style={{
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: '6px',
          padding: '1rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: '300', color: '#f59e0b', letterSpacing: '0.5px' }}>
            {warningCount}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: '300', letterSpacing: '0.3px' }}>
            Warnings
          </div>
        </div>
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '6px',
          padding: '1rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: '300', color: '#ef4444', letterSpacing: '0.5px' }}>
            {criticalCount}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: '300', letterSpacing: '0.3px' }}>
            Critical
          </div>
        </div>
      </div>

      {/* Assertion list */}
      <div style={{ padding: '0 2rem', maxHeight: '300px', overflowY: 'auto' }}>
        {assertions.map((assertion) => {
          const health = getHealthStatus(
            assertion.gate_status.freshness,
            assertion.gate_status.stability,
            assertion.gate_status.alignment
          )

          return (
            <div
              key={assertion.id}
              style={{
                background: 'rgba(0, 0, 0, 0.2)',
                border: `1px solid ${health.color}40`,
                borderRadius: '6px',
                padding: '0.75rem 1rem',
                marginBottom: '0.75rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: '400', marginBottom: '0.25rem' }}>
                  {assertion.logical_name}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '300' }}>
                  {assertion.owner_role}
                </div>
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: health.color
                }} />
                <span style={{ fontSize: '0.8rem', color: health.color, fontWeight: '400' }}>
                  {health.label}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
