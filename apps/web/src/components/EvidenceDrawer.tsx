import React from 'react';
import { Observation, SourceRecord } from '../types';

interface EvidenceDrawerProps {
  selectedId: string | null;
  observations: Observation[];
  sources: SourceRecord[];
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  selectedId,
  observations,
  sources,
  onClose,
}) => {
  if (!selectedId) {
    return null;
  }

  const obs = observations.find((o) => o.id === selectedId);
  const src = sources.find((s) => s.id === selectedId);

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{ padding: '24px', maxWidth: '600px' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="badge badge-accent">Evidence Item</span>
            <code style={{ fontSize: '14px', fontWeight: 700 }}>{selectedId}</code>
          </div>
          <button
            onClick={onClose}
            className="btn-secondary"
            style={{ padding: '4px 8px', fontSize: '12px' }}
          >
            ✕ Close
          </button>
        </div>

        {obs && (
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>
              Deterministic Observation: {obs.kind}
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--ink)', marginBottom: '12px' }}>
              {obs.summary}
            </p>

            <div style={{ backgroundColor: 'var(--canvas)', padding: '12px', borderRadius: 'var(--radius-sm)', marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
                Interval &amp; Measured Values
              </div>
              <div style={{ fontSize: '12px' }}>
                <div><strong>Start:</strong> <span className="tabular-nums">{obs.start_at}</span></div>
                <div><strong>End:</strong> <span className="tabular-nums">{obs.end_at}</span></div>
                {Object.entries(obs.numeric_values).map(([k, v]) => (
                  <div key={k}>
                    <strong>{k}:</strong> <span className="tabular-nums">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {obs.source_event_ids.length > 0 && (
              <div>
                <span style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                  Correlated Event IDs:
                </span>
                <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                  {obs.source_event_ids.map((id) => (
                    <span key={id} className="badge badge-neutral">{id}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {src && (
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>
              {src.title}
            </h3>
            <div style={{ fontSize: '12px', color: 'var(--accent)', marginBottom: '12px' }}>
              <a href={src.url} target="_blank" rel="noopener noreferrer">
                {src.url} &nearr;
              </a>
            </div>

            <div style={{ backgroundColor: 'var(--canvas)', padding: '12px', borderRadius: 'var(--radius-sm)', marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                Authoritative Guidance Excerpt (Domain: {src.domain})
              </div>
              <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', fontStyle: 'italic' }}>
                "{src.snippet}"
              </p>
            </div>

            <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
              <div><strong>Retrieved:</strong> {src.retrieved_at}</div>
              <div><strong>Content Digest:</strong> <code style={{ fontSize: '10px' }}>{src.content_digest.slice(0, 24)}...</code></div>
            </div>
          </div>
        )}

        {!obs && !src && (
          <div style={{ color: 'var(--muted)', fontSize: '13px' }}>
            Evidence item <code>{selectedId}</code> details not found in active run.
          </div>
        )}
      </div>
    </div>
  );
};
