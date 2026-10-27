import React from 'react';
import { Hypothesis } from '../types';

interface HypothesisBoardProps {
  hypotheses: Hypothesis[];
  onSelectEvidence: (evidenceId: string) => void;
}

export const HypothesisBoard: React.FC<HypothesisBoardProps> = ({
  hypotheses,
  onSelectEvidence,
}) => {
  if (!hypotheses || hypotheses.length === 0) {
    return (
      <div className="card" style={{ padding: '24px', textAlign: 'center', color: 'var(--muted)' }}>
        No hypotheses synthesized yet. Click <strong>Investigate Excursion</strong> to generate competing causal hypotheses.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 className="card-title">Competing Causal Hypotheses (NVIDIA Nemotron Synthesis)</h2>
        <span style={{ fontSize: '12px', color: 'var(--muted)' }}>
          {hypotheses.length} Competing Hypotheses Evaluated
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '16px',
        }}
      >
        {hypotheses.map((h) => {
          let statusBadgeClass = 'badge-neutral';
          let borderLeftColor = 'var(--rules)';

          if (h.status === 'LEADING') {
            statusBadgeClass = 'badge-supported';
            borderLeftColor = 'var(--supported)';
          } else if (h.status === 'DOWNGRADED' || h.status === 'REJECTED') {
            statusBadgeClass = 'badge-excursion';
            borderLeftColor = 'var(--excursion)';
          } else if (h.status === 'ALTERNATIVE') {
            statusBadgeClass = 'badge-unknown';
            borderLeftColor = 'var(--unknown)';
          }

          return (
            <div
              key={h.id}
              className="card"
              style={{
                borderLeft: `4px solid ${borderLeftColor}`,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className={`badge ${statusBadgeClass}`}>{h.status}</span>
                    <span className="badge badge-neutral">{h.id}</span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
                    Confidence: <strong>{h.confidence_band}</strong>
                  </span>
                </div>

                <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--ink)', marginBottom: '6px' }}>
                  {h.label}
                </h3>

                <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', marginBottom: '12px' }}>
                  {h.summary}
                </p>

                {/* Evidence citations */}
                <div style={{ marginBottom: '10px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                    Supporting Evidence:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                    {h.supporting_evidence_ids.length > 0 ? (
                      h.supporting_evidence_ids.map((eid) => (
                        <button
                          key={eid}
                          onClick={() => onSelectEvidence(eid)}
                          className="badge badge-supported"
                          style={{ cursor: 'pointer', border: '1px solid rgba(39,94,75,0.4)' }}
                          title={`Click to view evidence details for ${eid}`}
                        >
                          {eid}
                        </button>
                      ))
                    ) : (
                      <span style={{ fontSize: '11px', color: 'var(--muted)' }}>None cited</span>
                    )}
                  </div>
                </div>

                {/* Contradicting citations */}
                {h.contradicting_evidence_ids.length > 0 && (
                  <div style={{ marginBottom: '10px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--excursion)', fontWeight: 700, textTransform: 'uppercase' }}>
                      Contradicting Facts:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                      {h.contradicting_evidence_ids.map((eid) => (
                        <button
                          key={eid}
                          onClick={() => onSelectEvidence(eid)}
                          className="badge badge-excursion"
                          style={{ cursor: 'pointer' }}
                          title={`Click to view contradicting evidence for ${eid}`}
                        >
                          {eid}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Unknowns */}
                {h.unknowns.length > 0 && (
                  <div style={{ marginBottom: '10px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--unknown)', fontWeight: 700, textTransform: 'uppercase' }}>
                      Missing Evidence / Unknowns:
                    </span>
                    <ul style={{ paddingLeft: '16px', fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>
                      {h.unknowns.map((u, i) => (
                        <li key={i}>{u}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div>
                <div
                  style={{
                    backgroundColor: 'var(--surface-raised)',
                    border: '1px solid var(--rules-subtle)',
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '11px',
                    marginTop: '10px',
                  }}
                >
                  <strong style={{ color: 'var(--ink)' }}>Next Human Check:</strong> {h.next_check}
                </div>

                <div style={{ fontSize: '10px', color: 'var(--muted)', fontStyle: 'italic', marginTop: '6px' }}>
                  {h.what_it_does_not_establish}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
