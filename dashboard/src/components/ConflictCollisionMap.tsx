import { useState, useEffect } from 'react'

interface Distribution {
  min: number
  mode: number
  max: number
}

interface Assertion {
  id: string
  logical_name: string
  owner_role: string
  distribution?: Distribution
  gate_status: {
    freshness: string
    stability: string
    alignment: string
  }
}

interface CollisionMapProps {
  assertions: Assertion[]
}

export default function ConflictCollisionMap({ assertions }: CollisionMapProps) {
  const [time, setTime] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(t => (t + 1) % 360)
    }, 50)
    return () => clearInterval(interval)
  }, [])

  const getDepartmentColor = (owner: string) => {
    const colors: { [key: string]: string } = {
      'Supply Chain': '#3b82f6',
      'Sales': '#10b981',
      'Production': '#f59e0b',
      'Finance': '#8b5cf6',
      'Operations': '#ec4899'
    }
    
    for (const [dept, color] of Object.entries(colors)) {
      if (owner.includes(dept)) return color
    }
    return '#6b7280'
  }

  const getOrbitRadius = (index: number) => {
    return 25 + (index * 15)
  }

  const getOrbitSpeed = (index: number) => {
    return 1 + (index * 0.3)
  }

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
          Departmental Alignment
        </h3>
        <p style={{ 
          fontSize: '0.85rem', 
          color: 'var(--text-secondary)',
          margin: 0,
          fontWeight: '300',
          letterSpacing: '0.3px'
        }}>
          Cross-functional dependency mapping
        </p>
      </div>

      <div style={{ 
        position: 'relative', 
        width: '100%', 
        paddingTop: '100%',
        background: 'rgba(0, 0, 0, 0.2)',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <svg 
          style={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            width: '100%', 
            height: '100%' 
          }}
          viewBox="0 0 100 100"
        >
          {/* Center point */}
          <circle cx="50" cy="50" r="2" fill="rgba(255, 255, 255, 0.4)" />
          <text x="50" y="53" fill="rgba(255, 255, 255, 0.4)" fontSize="3" textAnchor="middle">Reality Center</text>

          {/* Orbit rings */}
          {assertions.map((_, index) => (
            <circle
              key={`orbit-${index}`}
              cx="50"
              cy="50"
              r={getOrbitRadius(index)}
              fill="none"
              stroke="rgba(255, 255, 255, 0.05)"
              strokeWidth="0.5"
              strokeDasharray="2,2"
            />
          ))}

          {/* Moving assertions */}
          {assertions.map((assertion, index) => {
            const radius = getOrbitRadius(index)
            const speed = getOrbitSpeed(index)
            const angle = (time * speed + index * (360 / assertions.length)) * (Math.PI / 180)
            const x = 50 + radius * Math.cos(angle)
            const y = 50 + radius * Math.sin(angle)
            const color = getDepartmentColor(assertion.owner_role)
            const hasConflict = assertion.gate_status.alignment === 'HALT'

            // Calculate distribution spread (opacity = how wide the distribution is)
            const spread = assertion.distribution 
              ? (assertion.distribution.max - assertion.distribution.min) / assertion.distribution.mode
              : 1
            const opacity = Math.min(0.9, 0.3 + (spread * 0.2))

            return (
              <g key={assertion.id}>
                {/* Distribution "bubble" */}
                <circle
                  cx={x}
                  cy={y}
                  r={4 + spread}
                  fill={color}
                  opacity={opacity * 0.3}
                  stroke={hasConflict ? '#ef4444' : color}
                  strokeWidth={hasConflict ? 0.5 : 0.2}
                >
                  <animate
                    attributeName="r"
                    values={`${4 + spread};${5 + spread};${4 + spread}`}
                    dur="2s"
                    repeatCount="indefinite"
                  />
                </circle>

                {/* Core point */}
                <circle
                  cx={x}
                  cy={y}
                  r={2}
                  fill={color}
                  opacity={0.9}
                />

                {/* Label */}
                <text
                  x={x}
                  y={y - 6}
                  fill="white"
                  fontSize="2.5"
                  textAnchor="middle"
                  opacity={0.7}
                >
                  {assertion.logical_name.substring(0, 8)}
                </text>

                {/* Conflict indicator */}
                {hasConflict && (
                  <text
                    x={x}
                    y={y + 8}
                    fill="#ef4444"
                    fontSize="4"
                    textAnchor="middle"
                  >
                    ⚠
                  </text>
                )}
              </g>
            )
          })}
        </svg>
      </div>

      {/* Department legend */}
      <div style={{ 
        marginTop: '1rem', 
        display: 'flex', 
        flexWrap: 'wrap',
        gap: '0.5rem',
        fontSize: '0.75rem'
      }}>
        {Array.from(new Set(assertions.map(a => a.owner_role))).map(owner => (
          <div key={owner} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ 
              width: '12px', 
              height: '12px', 
              borderRadius: '50%', 
              background: getDepartmentColor(owner) 
            }} />
            <span style={{ color: 'var(--text-secondary)' }}>{owner.substring(0, 20)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
