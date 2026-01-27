import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, Area, AreaChart, ResponsiveContainer } from 'recharts'

interface Distribution {
  min: number
  mode: number
  max: number
}

interface Props {
  distribution: Distribution
  baseline?: Distribution
}

const PertOverlapChart = ({ distribution, baseline }: Props) => {
  const generatePertPoints = (min: number, mode: number, max: number) => {
    const points = []
    const step = (max - min) / 100
    
    for (let x = min; x <= max; x += step) {
      let y = 0
      
      if (x < mode) {
        const t = (x - min) / (mode - min)
        y = Math.pow(t, 2)
      } else {
        const t = (max - x) / (max - mode)
        y = Math.pow(t, 2)
      }
      
      y = y * (4 / (max - min))
      
      points.push({ x: x.toFixed(3), value: y, baseline: 0 })
    }
    
    return points
  }

  const data = generatePertPoints(distribution.min, distribution.mode, distribution.max)

  if (baseline) {
    const baselinePoints = generatePertPoints(baseline.min, baseline.mode, baseline.max)
    data.forEach((point, i) => {
      point.baseline = baselinePoints[i]?.value || 0
    })
  }

  return (
    <div className="glass" style={{ 
      width: '100%', 
      padding: '1.5rem',
      borderRadius: '16px'
    }}>
      <h4 style={{ 
        marginBottom: '0.75rem',
        fontSize: '1.1rem',
        fontWeight: '600',
        color: 'var(--text-primary)'
      }}>
        Distribution Analysis
      </h4>
      <p style={{ 
        fontSize: '0.85rem', 
        color: 'var(--text-secondary)', 
        marginBottom: '1.5rem',
        fontStyle: 'italic'
      }}>
        Visual approximation - React computes shapes, Python computes truth
      </p>
      
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="colorBaseline" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.6}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(100, 116, 139, 0.2)" />
          <XAxis 
            dataKey="x" 
            stroke="var(--text-muted)"
            style={{ fontSize: '0.75rem' }}
            label={{ 
              value: 'Value', 
              position: 'insideBottom', 
              offset: -5,
              fill: 'var(--text-secondary)',
              fontSize: '0.85rem'
            }}
          />
          <YAxis 
            stroke="var(--text-muted)"
            style={{ fontSize: '0.75rem' }}
            label={{ 
              value: 'Density (approx)', 
              angle: -90, 
              position: 'insideLeft',
              fill: 'var(--text-secondary)',
              fontSize: '0.85rem'
            }}
          />
          <Tooltip 
            contentStyle={{
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(100, 116, 139, 0.3)',
              borderRadius: '8px',
              padding: '8px 12px',
              fontSize: '0.85rem'
            }}
            labelStyle={{ color: 'var(--text-primary)' }}
          />
          <Legend 
            wrapperStyle={{
              paddingTop: '1rem',
              fontSize: '0.9rem'
            }}
          />
          
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke="#3b82f6" 
            fill="url(#colorValue)" 
            strokeWidth={2}
            name="Current Distribution"
          />
          
          {baseline && (
            <Area 
              type="monotone" 
              dataKey="baseline" 
              stroke="#10b981" 
              fill="url(#colorBaseline)" 
              strokeWidth={2}
              name="Baseline Distribution"
            />
          )}
        </AreaChart>
      </ResponsiveContainer>

      <div className="glass" style={{ 
        marginTop: '1.5rem', 
        padding: '1rem',
        fontSize: '0.9rem', 
        color: 'var(--text-secondary)',
        background: 'rgba(100, 116, 139, 0.05)',
        borderRadius: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <strong style={{ color: 'var(--text-primary)' }}>PERT Range:</strong>
          <code style={{ 
            background: 'rgba(59, 130, 246, 0.15)',
            padding: '0.25rem 0.75rem',
            borderRadius: '6px',
            fontFamily: 'monospace',
            color: 'var(--accent-primary)'
          }}>
            [{distribution.min}, {distribution.mode}, {distribution.max}]
          </code>
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          min: {distribution.min} | mode: {distribution.mode} | max: {distribution.max}
        </div>
      </div>
    </div>
  )
}

export default PertOverlapChart
