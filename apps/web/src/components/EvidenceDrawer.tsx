import React, { useEffect, useRef } from 'react';
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
  const drawerRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!selectedId) return;

    // Save previous active element for focus restoration
    previouslyFocusedElement.current = document.activeElement as HTMLElement;

    // Body scroll lock
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Focus first focusable item in drawer
    const focusable = drawerRef.current?.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable && focusable.length > 0) {
      focusable[0].focus();
    }

    // Escape listener and focus trap
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      if (e.key === 'Tab' && focusable && focusable.length > 0) {
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener('keydown', handleKeyDown);
      if (previouslyFocusedElement.current) {
        previouslyFocusedElement.current.focus();
      }
    };
  }, [selectedId, onClose]);

  if (!selectedId) {
    return null;
  }

  const obs = observations.find((o) => o.id === selectedId);
  const src = sources.find((s) => s.id === selectedId);

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Evidence details drawer"
    >
      <div
        ref={drawerRef}
        className="modal-content drawer-content"
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
            aria-label="Close evidence drawer"
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span className={`badge ${src.source_mode === 'LIVE_RETRIEVAL' ? 'badge-accent' : 'badge-neutral'}`}>
                {src.source_mode === 'LIVE_RETRIEVAL' ? 'LIVE RETRIEVAL' : 'VERIFIED FIXTURE'}
              </span>
              <span className="badge badge-neutral" style={{ fontSize: '10px' }}>
                {src.excerpt_kind === 'VERBATIM' ? 'VERBATIM EXCERPT' : 'PARAPHRASE'}
              </span>
            </div>

            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>
              {src.title}
            </h3>
            <div style={{ fontSize: '12px', color: 'var(--accent)', marginBottom: '12px' }}>
              <a href={src.url} target="_blank" rel="noopener noreferrer">
                {src.url} ↗
              </a>
            </div>

            <div style={{ backgroundColor: 'var(--canvas)', padding: '12px', borderRadius: 'var(--radius-sm)', marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                {src.source_mode === 'LIVE_RETRIEVAL' && src.excerpt_kind === 'VERBATIM'
                  ? 'Live retrieved excerpt'
                  : 'Verified fixture summary — not a live quotation'}{' '}
                (Domain: {src.domain})
              </div>
              <p style={{ fontSize: '13px', color: 'var(--ink-secondary)', fontStyle: src.excerpt_kind === 'VERBATIM' ? 'italic' : 'normal', margin: '6px 0' }}>
                {src.excerpt_kind === 'VERBATIM' ? `"${src.snippet}"` : src.snippet}
              </p>
              {src.verification_note && (
                <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '6px' }}>
                  <strong>Verification Note:</strong> {src.verification_note}
                </div>
              )}
            </div>

            <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
              <div><strong>Source Mode:</strong> <code>{src.source_mode}</code></div>
              {src.verified_at && (
                <div><strong>Verified At:</strong> <span className="tabular-nums">{src.verified_at}</span></div>
              )}
              {src.published_or_updated_at && (
                <div><strong>Published / Updated:</strong> <span className="tabular-nums">{src.published_or_updated_at}</span></div>
              )}
              <div><strong>Retrieved:</strong> {src.retrieved_at}</div>
              <div><strong>Content Digest:</strong> <code style={{ fontSize: '10px' }}>{src.content_digest.slice(0, 24)}…</code></div>
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
