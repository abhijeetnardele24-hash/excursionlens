import React from 'react';
import { InvestigationRun } from '../types';

interface ProviderProofPanelProps {
  run?: InvestigationRun;
}

export const ProviderProofPanel: React.FC<ProviderProofPanelProps> = ({ run }) => {
  if (!run) {
    return null;
  }

  const getStatusBadge = () => {
    if (run.state === 'FAILED_TRUTHFULLY') {
      return <span className="badge badge-excursion">FAILED</span>;
    }
    switch (run.provider_mode) {
      case 'LIVE_TOKEN_FACTORY':
        return <span className="badge badge-supported">LIVE VERIFIED</span>;
      case 'DEMO_FIXTURE_FALLBACK':
        return <span className="badge badge-unknown">DEGRADED (FALLBACK)</span>;
      case 'DEMO_FIXTURE':
      default:
        return <span className="badge badge-neutral">FIXTURE DEMO</span>;
    }
  };

  return (
    <div className="card" style={{ marginTop: '16px' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 className="card-title">Provider &amp; Retrieval Proof Panel</h2>
          {getStatusBadge()}
        </div>
        <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
          Transparent execution receipts (Zero secrets logged)
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
        }}
      >
        {/* Nebius & NVIDIA Proof */}
        <div
          style={{
            backgroundColor: 'var(--surface-raised)',
            border: '1px solid var(--rules-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--ink)' }}>
              1. Nebius Token Factory &bull; NVIDIA Nemotron
            </span>
            <span className="badge badge-accent">Inference Status</span>
          </div>

          <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div>
              <span style={{ color: 'var(--muted)' }}>Served Model:</span>{' '}
              <code style={{ fontSize: '11px' }}>{run.served_model || run.requested_model}</code>
            </div>
            <div>
              <span style={{ color: 'var(--muted)' }}>Measured Latency:</span>{' '}
              {run.latency_ms !== null && run.latency_ms !== undefined ? (
                <strong className="tabular-nums">{run.latency_ms}ms</strong>
              ) : (
                <span style={{ color: 'var(--muted)' }}>Not recorded</span>
              )}
            </div>
            {run.usage && run.usage.total_tokens ? (
              <div>
                <span style={{ color: 'var(--muted)' }}>Token Usage:</span>{' '}
                <span className="tabular-nums">
                  {run.usage.total_tokens} tokens
                  {run.usage.prompt_tokens && run.usage.completion_tokens
                    ? ` (${run.usage.prompt_tokens} prompt, ${run.usage.completion_tokens} completion)`
                    : ''}
                </span>
              </div>
            ) : null}
            <div>
              <span style={{ color: 'var(--muted)' }}>Claims Validation:</span>{' '}
              <strong style={{ color: run.validation_result?.passed ? 'var(--supported)' : 'var(--excursion)' }}>
                {run.validation_result?.passed ? '100% Passed (0 unknown IDs)' : 'Validation Checks Failed'}
              </strong>
            </div>
          </div>
        </div>

        {/* Tavily Search Proof */}
        <div
          style={{
            backgroundColor: 'var(--surface-raised)',
            border: '1px solid var(--rules-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--ink)' }}>
              2. Authoritative Search Grounding (Tavily)
            </span>
            <span className="badge badge-neutral">Grounding Evidence</span>
          </div>

          <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div>
              <span style={{ color: 'var(--muted)' }}>Sources Retrieved:</span>{' '}
              <strong>{run.sources.length} Record{run.sources.length === 1 ? '' : 's'}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--muted)' }}>Domain Allowlist:</span>{' '}
              <span className="badge badge-neutral">cdc.gov</span>{' '}
              <span className="badge badge-neutral">fda.gov</span>{' '}
              <span className="badge badge-neutral">who.int</span>{' '}
              <span className="badge badge-neutral">gs1.org</span>
            </div>
            <div>
              <span style={{ color: 'var(--muted)' }}>Grounding Status:</span>{' '}
              <span style={{ color: 'var(--supported)', fontWeight: 600 }}>
                Authoritative domains and HTTPS scheme enforced
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
