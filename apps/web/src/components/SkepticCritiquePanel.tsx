import React from 'react';
import { SkepticCritique } from '../types';

interface SkepticCritiquePanelProps {
  critiques: SkepticCritique[];
}

export const SkepticCritiquePanel: React.FC<SkepticCritiquePanelProps> = ({ critiques }) => {
  if (!critiques || critiques.length === 0) {
    return null;
  }

  return (
    <div className="card" style={{ marginTop: '16px', borderTop: '3px solid var(--accent)' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 className="card-title">Adversarial Skeptic Pass (Nemotron Critique)</h2>
          <span className="badge badge-accent">Self-Correction Layer</span>
        </div>
        <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
          Attacks leading assumptions &amp; detects overclaims
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
        {critiques.map((c) => (
          <div
            key={c.hypothesis_id}
            style={{
              backgroundColor: 'var(--surface-raised)',
              border: '1px solid var(--rules-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span className="badge badge-neutral">{c.hypothesis_id}</span>
              <span
                className={`badge ${
                  c.recommended_status === 'DOWNGRADED'
                    ? 'badge-excursion'
                    : c.recommended_status === 'LEADING'
                    ? 'badge-supported'
                    : 'badge-unknown'
                }`}
              >
                Verdict: {c.recommended_status}
              </span>
            </div>

            <p style={{ fontSize: '12px', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
              {c.attack_summary}
            </p>

            {c.ignored_contradictions.length > 0 && (
              <div style={{ marginBottom: '6px' }}>
                <span style={{ fontSize: '10px', color: 'var(--excursion)', fontWeight: 700, textTransform: 'uppercase' }}>
                  Surfaced Contradiction:
                </span>
                <ul style={{ paddingLeft: '14px', fontSize: '11px', color: 'var(--ink-secondary)' }}>
                  {c.ignored_contradictions.map((con, idx) => (
                    <li key={idx}>{con}</li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '4px' }}>
              <strong>Skeptic Rationale:</strong> {c.rationale}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
