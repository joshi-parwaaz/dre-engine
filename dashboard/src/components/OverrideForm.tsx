import { useState } from 'react'

interface Props {
  assertionIds: string[]
}

const OverrideForm = ({ assertionIds }: Props) => {
  const [justification, setJustification] = useState('')
  const [signature, setSignature] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setResult(null)

    try {
      const response = await fetch('http://127.0.0.1:8000/override', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assertion_ids: assertionIds,
          justification,
          signature,
          timestamp: new Date().toISOString(),
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setResult('Override request recorded and pending evaluation.')
        setJustification('')
        setSignature('')
      } else {
        setResult(`Override rejected: ${data.detail || 'Unknown error'}`)
      }
    } catch (error) {
      setResult(`Failed to submit override: ${error}`)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ 
      border: '1px solid rgba(239, 68, 68, 0.2)', 
      borderRadius: '8px', 
      padding: '2rem',
      background: 'rgba(15, 23, 42, 0.2)'
    }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ 
          color: 'var(--accent-danger)', 
          fontSize: '1.25rem',
          fontWeight: '500',
          margin: 0,
          letterSpacing: '0.3px'
        }}>
          Override Request
        </h3>
      </div>
      
      <div style={{ 
        marginBottom: '1.5rem', 
        padding: '1rem',
        fontSize: '0.9rem', 
        color: 'var(--text-secondary)',
        background: 'transparent',
        borderRadius: '6px',
        border: '1px solid rgba(100, 116, 139, 0.15)',
        letterSpacing: '0.2px'
      }}>
        <p style={{ margin: 0, lineHeight: '1.6', fontWeight: '300' }}>
          Override requests are logged and evaluated against governance policy. Approval is not automatic.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '0.75rem', 
            fontWeight: '600',
            color: 'var(--text-primary)',
            fontSize: '0.95rem'
          }}>
            Justification <span style={{ color: 'var(--accent-danger)' }}>*</span>
          </label>
          <textarea
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            required
            rows={4}
            style={{ 
              width: '100%',
              background: 'rgba(15, 23, 42, 0.3)',
              border: '1px solid rgba(100, 116, 139, 0.2)',
              padding: '1rem',
              borderRadius: '8px',
              fontFamily: 'inherit',
              fontSize: '0.9rem',
              color: 'var(--text-primary)',
              resize: 'vertical',
              transition: 'all 0.2s ease'
            }}
            placeholder="Explain why this override is necessary..."
            onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
            onBlur={(e) => e.target.style.borderColor = 'rgba(100, 116, 139, 0.2)'}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '0.75rem', 
            fontWeight: '600',
            color: 'var(--text-primary)',
            fontSize: '0.95rem'
          }}>
            Digital Signature <span style={{ color: 'var(--accent-danger)' }}>*</span>
          </label>
          <input
            type="text"
            value={signature}
            onChange={(e) => setSignature(e.target.value)}
            required
            style={{ 
              width: '100%',
              background: 'rgba(15, 23, 42, 0.3)',
              border: '1px solid rgba(100, 116, 139, 0.2)',
              padding: '0.875rem 1rem',
              borderRadius: '8px',
              fontFamily: 'inherit',
              fontSize: '0.9rem',
              color: 'var(--text-primary)',
              transition: 'all 0.2s ease'
            }}
            placeholder="Your name or employee ID"
            onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
            onBlur={(e) => e.target.style.borderColor = 'rgba(100, 116, 139, 0.2)'}
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !justification.trim() || !signature.trim()}
          style={{
            padding: '1rem 2rem',
            background: submitting || !justification.trim() || !signature.trim()
              ? 'rgba(100, 116, 139, 0.2)' 
              : '#ef4444',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: submitting || !justification.trim() || !signature.trim() ? 'not-allowed' : 'pointer',
            fontWeight: '400',
            fontSize: '0.95rem',
            width: '100%',
            transition: 'all 0.2s ease',
            letterSpacing: '0.3px'
          }}
        >
          {submitting ? 'Submitting...' : 'Submit Override Request'}
        </button>

        {result && (
          <div className="fade-in" style={{ 
            marginTop: '1.5rem', 
            padding: '1rem', 
            borderRadius: '6px',
            background: 'transparent',
            color: result.includes('recorded') 
              ? 'var(--accent-success)' 
              : 'var(--accent-danger)',
            border: `1px solid ${result.includes('recorded') 
              ? 'rgba(16, 185, 129, 0.2)' 
              : 'rgba(239, 68, 68, 0.2)'}`,
            fontWeight: '300',
            fontSize: '0.9rem',
            letterSpacing: '0.2px'
          }}>
            {result}
          </div>
        )}
      </form>

      <div className="glass" style={{ 
        marginTop: '2rem', 
        padding: '1.25rem', 
        background: 'rgba(15, 23, 42, 0.6)', 
        borderRadius: '12px',
        border: '1px solid var(--border-color)'
      }}>
        <strong style={{ 
          fontSize: '0.95rem',
          color: 'var(--text-primary)',
          display: 'block',
          marginBottom: '0.75rem'
        }}>
          Affected Assertions:
        </strong>
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '0.5rem' 
        }}>
          {assertionIds.map(id => (
            <code key={id} style={{
              padding: '0.5rem 0.75rem',
              background: 'rgba(100, 116, 139, 0.15)',
              borderRadius: '8px',
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              color: 'var(--accent-primary)',
              border: '1px solid rgba(59, 130, 246, 0.2)'
            }}>
              {id}
            </code>
          ))}
        </div>
      </div>
    </div>
  )
}

export default OverrideForm
