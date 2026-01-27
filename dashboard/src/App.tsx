import { useState, useEffect } from 'react'
import PertOverlapChart from './components/PertOverlapChart'
import OverrideForm from './components/OverrideForm'
import Galaxy from './components/Galaxy'
import AuditLog from './components/AuditLog'
import EpistemicHealthMap from './components/EpistemicHealthMap'
import ConflictCollisionMap from './components/ConflictCollisionMap'
import GovernanceVelocity from './components/GovernanceVelocity'

interface Distribution {
  min: number
  mode: number
  max: number
}

interface GateStatus {
  freshness: string
  stability: string
  alignment: string
}

interface GateDetails {
  status: string
  [key: string]: any
}

interface Assertion {
  id: string
  logical_name: string
  owner_role: string
  gate_status: GateStatus
  gate_details?: {
    freshness: GateDetails
    stability: GateDetails
    alignment: GateDetails
  }
  distribution: Distribution
}

interface GovernanceState {
  status: string
  assertions: Assertion[]
  conflict_pair?: string[]
  last_updated?: string
}

function App() {
  const [state, setState] = useState<GovernanceState | null>(null)
  const [connected, setConnected] = useState(false)
  const [showAuditLog, setShowAuditLog] = useState(false)
  const [leadershipMode, setLeadershipMode] = useState(false)
  const [lastAuditRefresh, setLastAuditRefresh] = useState<string | null>(null)
  const [showBypassModal, setShowBypassModal] = useState(false)
  const [bypassJustification, setBypassJustification] = useState('')
  const [bypassSignature, setBypassSignature] = useState('')

  useEffect(() => {
    // Poll for governance state every 2 seconds
    const pollState = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/governance/state')
        const data = await response.json()
        if (data.assertions && data.assertions.length > 0) {
          // Only update state if data actually changed
          setState(prevState => {
            const dataStr = JSON.stringify(data)
            const prevStr = JSON.stringify(prevState)
            if (dataStr !== prevStr) {
              // Only trigger audit refresh if last_updated timestamp changed (real event, not heartbeat)
              const hasNewEvent = data.last_updated && data.last_updated !== lastAuditRefresh
              if (hasNewEvent && (window as any).refreshGovernanceVelocity) {
                console.log('[DRE] New governance event detected, refreshing audit...')
                setLastAuditRefresh(data.last_updated)
                ;(window as any).refreshGovernanceVelocity()
              }
              return data
            }
            return prevState
          })
        }
      } catch (error) {
        console.error('[DRE] Failed to fetch governance state:', error)
      }
    }
    
    // Initial poll
    pollState()
    
    // Poll every 2 seconds
    const pollInterval = setInterval(pollState, 2000)
    
    // Also set up WebSocket for real-time updates
    const ws = new WebSocket('ws://127.0.0.1:8000/ws')

    ws.onopen = () => {
      console.log('[DRE] WebSocket connected')
      setConnected(true)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('[DRE] Received governance state:', data)
      setState(prevState => {
        const dataStr = JSON.stringify(data)
        const prevStr = JSON.stringify(prevState)
        if (dataStr !== prevStr) {
          // Only trigger audit refresh if last_updated timestamp changed
          const hasNewEvent = data.last_updated && data.last_updated !== lastAuditRefresh
          if (hasNewEvent && (window as any).refreshGovernanceVelocity) {
            console.log('[DRE] New governance event via WebSocket, refreshing audit...')
            setLastAuditRefresh(data.last_updated)
            ;(window as any).refreshGovernanceVelocity()
          }
          return data
        }
        return prevState
      })
    }

    ws.onerror = (error) => {
      console.error('[DRE] WebSocket error:', error)
      setConnected(false)
    }

    ws.onclose = () => {
      console.log('[DRE] WebSocket closed')
      setConnected(false)
    }

    return () => {
      clearInterval(pollInterval)
      ws.close()
    }
  }, [])

  // Connecting state
  if (!connected) {
    return (
      <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden', background: '#0a0e1a' }}>
        <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
          <Galaxy 
            mouseRepulsion
            mouseInteraction
            density={1}
            glowIntensity={0.3}
            saturation={0}
            hueShift={140}
            twinkleIntensity={0.3}
            rotationSpeed={0.1}
            repulsionStrength={2}
            autoCenterRepulsion={0}
            starSpeed={0.5}
            speed={1}
          />
        </div>
        <div style={{ 
          position: 'relative', 
          zIndex: 10, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100vh',
          pointerEvents: 'none'
        }}>
          <div className="fade-in" style={{ 
            padding: '3rem', 
            textAlign: 'center',
            maxWidth: '500px',
            pointerEvents: 'auto'
          }}>
            <h2 style={{ 
              fontSize: '2rem', 
              fontWeight: '300', 
              marginBottom: '0.5rem',
              color: 'var(--text-primary)',
              letterSpacing: '0.5px'
            }}>
              DRE Dashboard
            </h2>
            <p style={{ 
              color: 'var(--text-secondary)',
              fontSize: '0.95rem',
              fontWeight: '300',
              letterSpacing: '0.3px'
            }}>
              Connecting...
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Listening state (no HALT yet)
  if (!state) {
    return (
      <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden', background: '#0a0e1a' }}>
        <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
          <Galaxy 
            mouseRepulsion
            mouseInteraction
            density={1}
            glowIntensity={0.3}
            saturation={0}
            hueShift={140}
            twinkleIntensity={0.3}
            rotationSpeed={0.1}
            repulsionStrength={2}
            autoCenterRepulsion={0}
            starSpeed={0.5}
            speed={1}
          />
        </div>
        <div style={{ 
          position: 'relative', 
          zIndex: 10, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100vh',
          pointerEvents: 'none'
        }}>
          <div className="fade-in" style={{ 
            padding: '3rem', 
            textAlign: 'center',
            maxWidth: '500px',
            pointerEvents: 'auto'
          }}>
            <h2 style={{ 
              fontSize: '2rem', 
              fontWeight: '300', 
              marginBottom: '1rem',
              color: 'var(--text-primary)',
              letterSpacing: '0.5px'
            }}>
              DRE Dashboard
            </h2>
            <p style={{ 
              color: 'var(--text-secondary)',
              fontSize: '0.95rem',
              marginBottom: '2.5rem',
              fontWeight: '300',
              letterSpacing: '0.3px'
            }}>
              Active. Listening for governance events.
            </p>
            <button
              onClick={() => setLeadershipMode(true)}
              style={{
                background: 'transparent',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                color: '#60a5fa',
                padding: '0.85rem 2rem',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: '400',
                transition: 'all 0.2s',
                letterSpacing: '0.3px'
              }}
            >
              Leadership Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  const haltedAssertions = state.assertions.filter(a => 
    Object.values(a.gate_status).includes('HALT')
  )

  // Default to Leadership Dashboard when state exists
  if (leadershipMode || state.status !== 'HALT') {
    return (
      <div style={{ position: 'relative', minHeight: '100vh', overflow: 'auto', background: '#0a0e1a' }}>
        <div style={{ position: 'fixed', inset: 0, zIndex: 0 }}>
          <Galaxy 
            mouseRepulsion={false}
            mouseInteraction={false}
            density={0.5}
            glowIntensity={0.2}
            saturation={0}
            hueShift={140}
            twinkleIntensity={0.2}
            rotationSpeed={0.05}
            speed={0.5}
          />
        </div>
        
        <div style={{ 
          position: 'relative', 
          zIndex: 10, 
          padding: '2rem', 
          maxWidth: '1600px', 
          margin: '0 auto',
          pointerEvents: 'none'
        }}>
          <header className="fade-in" style={{ 
            marginBottom: '3rem', 
            padding: '2rem 0', 
            pointerEvents: 'auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <h1 style={{ 
                fontSize: '2.25rem', 
                fontWeight: '300',
                color: 'var(--text-primary)',
                margin: 0,
                marginBottom: '0.5rem',
                letterSpacing: '0.5px'
              }}>
                Strategic Governance Monitor
              </h1>
              <p style={{ 
                color: 'var(--text-secondary)', 
                fontSize: '0.9rem',
                margin: 0,
                fontWeight: '300',
                letterSpacing: '0.3px'
              }}>
                Real-time epistemic health monitoring
                {state.status === 'HALT' && (
                  <span style={{ 
                    marginLeft: '1rem',
                    color: '#ef4444',
                    fontWeight: '400',
                    letterSpacing: '0.5px'
                  }}>
                    • System HALT Active
                  </span>
                )}
              </p>
            </div>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              {state.status === 'HALT' && (
                <div style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '6px',
                  padding: '0.75rem 1.5rem',
                  color: '#ef4444',
                  fontSize: '0.85rem',
                  fontWeight: '400',
                  letterSpacing: '0.3px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <div style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: '#ef4444',
                    animation: 'pulse 2s infinite'
                  }} />
                  HALT
                </div>
              )}
              {state.status === 'HALT' && (
                <>
                  <button
                    onClick={() => setLeadershipMode(false)}
                    style={{
                      background: 'rgba(239, 68, 68, 0.15)',
                      border: '1px solid rgba(239, 68, 68, 0.4)',
                      color: '#ef4444',
                      padding: '0.75rem 1.5rem',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      fontWeight: '400',
                      transition: 'all 0.2s',
                      letterSpacing: '0.3px'
                    }}
                  >
                    View HALT Details
                  </button>
                  <button
                    onClick={() => setShowBypassModal(true)}
                    style={{
                      background: 'rgba(245, 158, 11, 0.15)',
                      border: '1px solid rgba(245, 158, 11, 0.4)',
                      color: '#f59e0b',
                      padding: '0.75rem 1.5rem',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      fontWeight: '400',
                      transition: 'all 0.2s',
                      letterSpacing: '0.3px'
                    }}
                  >
                    Bypass HALT
                  </button>
                </>
              )}
              <button
                onClick={() => setShowAuditLog(!showAuditLog)}
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(100, 116, 139, 0.3)',
                  color: '#94a3b8',
                  padding: '0.75rem 1.5rem',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '400',
                  transition: 'all 0.2s',
                  letterSpacing: '0.3px'
                }}
              >
                Audit
              </button>
            </div>
          </header>

          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(2, 1fr)', 
            gap: '1.5rem',
            marginBottom: '1.5rem'
          }}>
            <EpistemicHealthMap assertions={state.assertions} />
            <ConflictCollisionMap assertions={state.assertions} />
          </div>

          <GovernanceVelocity recentHours={24} />
        </div>

        {showAuditLog && <AuditLog onClose={() => setShowAuditLog(false)} />}
      </div>
    )
  }

  // HALT Intervention View (pattern interrupt)
  return (
    <div style={{ position: 'relative', minHeight: '100vh', overflow: 'auto', background: '#0a0e1a' }}>
      <div style={{ position: 'fixed', inset: 0, zIndex: 0 }}>
        <Galaxy 
          mouseRepulsion
          mouseInteraction
          density={1}
          glowIntensity={0.3}
          saturation={0}
          hueShift={140}
          twinkleIntensity={0.3}
          rotationSpeed={0.1}
          repulsionStrength={2}
          autoCenterRepulsion={0}
          starSpeed={0.5}
          speed={1}
        />
      </div>
      
      <div style={{ 
        position: 'relative', 
        zIndex: 10, 
        padding: '2rem', 
        maxWidth: '1400px', 
        margin: '0 auto',
        paddingBottom: '4rem',
        pointerEvents: 'none'
      }}>
        <header className="fade-in" style={{ 
          marginBottom: '3rem', 
          padding: '2rem 0', 
          pointerEvents: 'auto'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: '300', color: 'var(--accent-danger)' }}>!</div>
              <h1 style={{ 
                fontSize: '2.5rem', 
                fontWeight: '300',
                color: 'var(--accent-danger)',
                margin: 0,
                letterSpacing: '0.5px'
              }}>
                GOVERNANCE HALT
              </h1>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                onClick={() => setShowAuditLog(!showAuditLog)}
                style={{
                  background: showAuditLog ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  color: '#fff',
                  padding: '0.75rem 1.5rem',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  fontSize: '0.95rem',
                  fontWeight: '500',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                <span>🔍</span>
                <span>Audit Log</span>
              </button>
              <button
                onClick={() => setLeadershipMode(true)}
                style={{
                  background: 'rgba(59, 130, 246, 0.2)',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  color: '#60a5fa',
                  padding: '0.75rem 1.5rem',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  fontSize: '0.95rem',
                  fontWeight: '500',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                <span>📊</span>
                <span>Leadership</span>
              </button>
            </div>
          </div>
          <p style={{ 
            color: 'var(--text-secondary)', 
            fontSize: '1rem',
            fontWeight: '300',
            letterSpacing: '0.3px'
          }}>
            Governance intervention required.
          </p>
        </header>

        {state.conflict_pair && (
          <div className="fade-in" style={{ 
            background: 'transparent', 
            border: '1px solid rgba(239, 68, 68, 0.2)', 
            padding: '1.25rem', 
            marginBottom: '2rem',
            borderRadius: '8px',
            pointerEvents: 'auto'
          }}>
            <div>
              <strong style={{ color: 'var(--accent-danger)', fontSize: '1rem', fontWeight: '500', letterSpacing: '0.3px' }}>
                Conflict Detected:
              </strong>
              <span style={{ marginLeft: '0.75rem', color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                {state.conflict_pair.join(' vs ')}
              </span>
            </div>
          </div>
        )}

        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ 
            fontSize: '1.75rem', 
            fontWeight: '600', 
            marginBottom: '1.5rem',
            color: 'var(--text-primary)'
          }}>
            Gate Analysis Results
          </h2>
          
          <div style={{ display: 'grid', gap: '2rem', pointerEvents: 'auto' }}>
            {haltedAssertions.map((assertion, idx) => (
              <div 
                key={assertion.id} 
                className="fade-in" 
                style={{ 
                  border: '1px solid rgba(100, 116, 139, 0.15)',
                  borderRadius: '8px',
                  padding: '2rem',
                  transition: 'all 0.3s ease',
                  animationDelay: `${idx * 0.1}s`,
                  background: 'rgba(15, 23, 42, 0.2)'
                }}
              >
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'flex-start',
                  marginBottom: '1.25rem'
                }}>
                  <div>
                    <h3 style={{ 
                      fontSize: '1.35rem', 
                      fontWeight: '600',
                      color: 'var(--text-primary)',
                      marginBottom: '0.5rem'
                    }}>
                      {assertion.logical_name}
                    </h3>
                    <code style={{ 
                      fontSize: '0.8rem',
                      color: 'var(--text-muted)',
                      background: 'rgba(100, 116, 139, 0.15)',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '6px',
                      fontFamily: 'monospace'
                    }}>
                      {assertion.id}
                    </code>
                  </div>
                </div>

                <div style={{ 
                  display: 'flex', 
                  flexDirection: 'column',
                  gap: '1rem', 
                  marginBottom: '1.5rem'
                }}>
                  {Object.entries(assertion.gate_status).map(([gate, status]) => {
                    const gateLabel = gate === 'freshness' ? 'Freshness' : gate === 'stability' ? 'Stability' : 'Structure';
                    const isHalt = status === 'HALT';
                    const gateDetails = assertion.gate_details?.[gate as keyof typeof assertion.gate_details];
                    
                    return (
                      <div key={gate} style={{ 
                        display: 'flex', 
                        flexDirection: 'column',
                        padding: '0.75rem 1rem',
                        background: 'rgba(15, 23, 42, 0.3)',
                        border: `1px solid ${isHalt ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.2)'}`,
                        borderRadius: '6px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: '400', letterSpacing: '0.3px' }}>
                            {gateLabel}
                          </span>
                          <span style={{
                            fontSize: '0.85rem',
                            fontWeight: '500',
                            color: isHalt ? '#ef4444' : '#10b981',
                            letterSpacing: '0.5px'
                          }}>
                            {status}
                          </span>
                        </div>
                        {isHalt && gateDetails && (
                          <div style={{ 
                            marginTop: '0.5rem', 
                            fontSize: '0.85rem', 
                            color: 'var(--text-secondary)',
                            fontWeight: '300',
                            letterSpacing: '0.2px'
                          }}>
                            {gate === 'stability' && gateDetails.drift && (
                              <span>
                                Drift: {(gateDetails.drift * 100).toFixed(1)}% (threshold: {(gateDetails.threshold * 100).toFixed(0)}%)
                                {gateDetails.current_value !== undefined && gateDetails.baseline_value !== undefined && (
                                  <> • Current: {gateDetails.current_value}, Baseline: {gateDetails.baseline_value}</>
                                )}
                              </span>
                            )}
                            {gate === 'freshness' && gateDetails.days_since_update !== undefined && (
                              <span>
                                Last updated {gateDetails.days_since_update} days ago (SLA: {gateDetails.sla_days} days)
                              </span>
                            )}
                            {gate === 'alignment' && gateDetails.reason && (
                              <span>{gateDetails.reason}</span>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {assertion.distribution && (
                  <div style={{ marginTop: '1.5rem' }}>
                    <PertOverlapChart distribution={assertion.distribution} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div style={{ animationDelay: '0.5s', pointerEvents: 'auto' }} className="fade-in">
          <OverrideForm assertionIds={haltedAssertions.map(a => a.id)} />
        </div>
      </div>

      {showAuditLog && <AuditLog onClose={() => setShowAuditLog(false)} />}

      {/* Bypass Modal - Digital Signature Required */}
      {showBypassModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{
            background: 'var(--panel-bg)',
            border: '1px solid rgba(100, 116, 139, 0.3)',
            borderRadius: '12px',
            padding: '2.5rem',
            maxWidth: '600px',
            width: '90%',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)'
          }}>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: 'var(--text-primary)'
            }}>Bypass HALT - Digital Signature Required</h2>
            
            <p style={{
              color: 'var(--text-muted)',
              marginBottom: '1.5rem',
              fontSize: '0.95rem',
              lineHeight: '1.6'
            }}>
              This override will be permanently logged with a cryptographic hash for audit trail compliance.
              All halted assertions will be bypassed.
            </p>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block',
                color: 'var(--text-primary)',
                marginBottom: '0.5rem',
                fontSize: '0.9rem',
                fontWeight: '500'
              }}>Justification (required)</label>
              <textarea
                value={bypassJustification}
                onChange={(e) => setBypassJustification(e.target.value)}
                placeholder="Explain why this HALT is being bypassed (e.g., 'CFO approved new target for Q2', 'Emergency board directive')..."
                style={{
                  width: '100%',
                  minHeight: '120px',
                  padding: '0.75rem',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(100, 116, 139, 0.3)',
                  borderRadius: '6px',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem',
                  fontFamily: 'inherit',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block',
                color: 'var(--text-primary)',
                marginBottom: '0.5rem',
                fontSize: '0.9rem',
                fontWeight: '500'
              }}>Digital Signature (required)</label>
              <input
                type="text"
                value={bypassSignature}
                onChange={(e) => setBypassSignature(e.target.value)}
                placeholder="Your name or employee ID (e.g., 'John Smith - CFO' or 'EMP-12345')"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(100, 116, 139, 0.3)',
                  borderRadius: '6px',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            <div style={{
              background: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '6px',
              padding: '0.75rem',
              marginBottom: '1.5rem'
            }}>
              <div style={{ color: '#f59e0b', fontSize: '0.85rem', marginBottom: '0.25rem', fontWeight: '500' }}>
                ⚠ Non-Repudiation Notice
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: '1.5' }}>
                A SHA-256 hash will be computed from your justification, signature, and timestamp.
                This hash will be permanently stored in the audit log and cannot be altered.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setShowBypassModal(false)
                  setBypassJustification('')
                  setBypassSignature('')
                }}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: 'transparent',
                  border: '1px solid rgba(100, 116, 139, 0.3)',
                  color: 'var(--text-muted)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '400'
                }}
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (!bypassJustification.trim() || !bypassSignature.trim()) {
                    alert('Both justification and signature are required')
                    return
                  }

                  try {
                    const timestamp = new Date().toISOString()
                    
                    // Compute SHA-256 hash for non-repudiation
                    const hashInput = `${bypassJustification}|${bypassSignature}|${timestamp}`
                    const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(hashInput))
                    const hashArray = Array.from(new Uint8Array(hashBuffer))
                    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')

                    // Get all halted assertion IDs
                    const haltedIds = state?.assertions
                      ?.filter((a: any) => 
                        a.gate_status?.freshness === 'HALT' ||
                        a.gate_status?.stability === 'HALT' ||
                        a.gate_status?.alignment === 'HALT'
                      )
                      .map((a: any) => a.id) || []

                    const response = await fetch('http://localhost:8000/override', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        assertion_ids: haltedIds,
                        justification: bypassJustification,
                        signature: bypassSignature,
                        timestamp: timestamp,
                        signature_hash: hashHex
                      })
                    })

                    if (response.ok) {
                      alert(`Override logged successfully.\\n\\nDigital Hash: ${hashHex.substring(0, 16)}...\\n\\nThis override has been permanently recorded in the audit trail.`)
                      setShowBypassModal(false)
                      setBypassJustification('')
                      setBypassSignature('')
                    } else {
                      alert('Failed to submit override')
                    }
                  } catch (error) {
                    console.error('Failed to bypass HALT:', error)
                    alert('Error submitting override. See console for details.')
                  }
                }}
                disabled={!bypassJustification.trim() || !bypassSignature.trim()}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: bypassJustification.trim() && bypassSignature.trim() 
                    ? 'rgba(245, 158, 11, 0.15)'
                    : 'rgba(100, 116, 139, 0.1)',
                  border: bypassJustification.trim() && bypassSignature.trim()
                    ? '1px solid rgba(245, 158, 11, 0.4)'
                    : '1px solid rgba(100, 116, 139, 0.2)',
                  color: bypassJustification.trim() && bypassSignature.trim()
                    ? '#f59e0b'
                    : 'var(--text-muted)',
                  borderRadius: '6px',
                  cursor: bypassJustification.trim() && bypassSignature.trim() ? 'pointer' : 'not-allowed',
                  fontSize: '0.9rem',
                  fontWeight: '500',
                  opacity: bypassJustification.trim() && bypassSignature.trim() ? 1 : 0.5
                }}
              >
                Submit Override
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
