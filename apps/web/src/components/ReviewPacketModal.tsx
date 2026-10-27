import React, { useEffect, useRef } from 'react';
import { InvestigationRun, ShipmentCase } from '../types';

interface ReviewPacketModalProps {
  isOpen: boolean;
  onClose: () => void;
  run?: InvestigationRun;
  caseData: ShipmentCase;
}

export const ReviewPacketModal: React.FC<ReviewPacketModalProps> = ({
  isOpen,
  onClose,
  run,
  caseData,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Save previous active element for focus restoration
    previouslyFocusedElement.current = document.activeElement as HTMLElement;

    // Body scroll lock
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Focus first focusable item in modal
    const focusable = modalRef.current?.querySelectorAll<HTMLElement>(
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
  }, [isOpen, onClose]);

  if (!isOpen || !run) {
    return null;
  }

  const handlePrint = () => {
    window.open(`/api/investigations/${run.id}/report`, '_blank');
  };

  const handleDownloadJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(run, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `excursionlens-${caseData.shipment.shipment_id}-${run.id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="review-packet-modal-title">
      <div
        ref={modalRef}
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{ padding: '28px', maxWidth: '850px' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <span className="badge badge-accent">Quality Incident Packet</span>
            <h2 id="review-packet-modal-title" style={{ fontSize: '20px', fontWeight: 800, marginTop: '4px' }}>
              ExcursionLens Quality Review Packet
            </h2>
            <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
              Shipment: <strong>{caseData.shipment.shipment_id}</strong> &bull; Run ID: <code>{run.id}</code>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn-secondary" onClick={handleDownloadJson}>
              Download JSON
            </button>
            <button className="btn-primary" onClick={handlePrint}>
              Open Print / PDF View ↗
            </button>
            <button
              className="btn-secondary"
              onClick={onClose}
              aria-label="Close review packet modal"
              style={{ padding: '6px 10px' }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Quality boundary notice */}
        <div
          style={{
            backgroundColor: 'var(--canvas)',
            border: '1px solid var(--rules)',
            padding: '12px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '12px',
            color: 'var(--muted)',
            marginBottom: '20px',
          }}
        >
          <strong>Decision-Support Boundary:</strong> {run.disclaimer}
        </div>

        {/* Summary metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '20px' }}>
          <div style={{ backgroundColor: 'var(--surface-raised)', padding: '10px', border: '1px solid var(--rules-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase' }}>Recommended Posture</div>
            <strong style={{ fontSize: '13px', color: 'var(--excursion)' }}>
              {run.review_posture.replace(/_/g, ' ')}
            </strong>
          </div>

          <div style={{ backgroundColor: 'var(--surface-raised)', padding: '10px', border: '1px solid var(--rules-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase' }}>Deterministic Facts</div>
            <strong style={{ fontSize: '13px' }}>
              {run.observations.length} Observations Verified
            </strong>
          </div>

          <div style={{ backgroundColor: 'var(--surface-raised)', padding: '10px', border: '1px solid var(--rules-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase' }}>Provider Mode</div>
            <strong style={{ fontSize: '13px', color: run.provider_mode === 'LIVE_TOKEN_FACTORY' ? 'var(--supported)' : 'var(--muted)' }}>
              {run.provider_mode === 'LIVE_TOKEN_FACTORY' ? 'LIVE VERIFIED' : 'FIXTURE DEMO'}
            </strong>
          </div>
        </div>

        {/* Hypotheses brief */}
        <h3 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.4px', borderBottom: '1px solid var(--rules-subtle)', paddingBottom: '4px', marginBottom: '10px' }}>
          Ranked Causal Hypotheses
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>
          {run.hypotheses.map((h) => (
            <div
              key={h.id}
              style={{
                padding: '10px',
                border: '1px solid var(--rules-subtle)',
                backgroundColor: 'var(--surface-raised)',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <strong style={{ fontSize: '13px' }}>
                  {h.id}: {h.label}
                </strong>
                <span className={`badge ${h.status === 'LEADING' ? 'badge-supported' : h.status === 'DOWNGRADED' ? 'badge-excursion' : 'badge-unknown'}`}>
                  {h.status}
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--ink-secondary)', margin: '0 0 6px 0' }}>{h.summary}</p>
              <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                <strong>Discriminating Action:</strong> {h.next_check}
              </div>
            </div>
          ))}
        </div>

        <div style={{ textAlign: 'right' }}>
          <button className="btn-primary" onClick={handlePrint} style={{ width: '100%', padding: '12px' }}>
            Open Formatted Incident Packet (Print/PDF) ↗
          </button>
        </div>
      </div>
    </div>
  );
};
