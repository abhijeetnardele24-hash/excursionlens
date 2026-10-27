import React from 'react';

interface AppHeaderProps {
  providerMode: 'LIVE_TOKEN_FACTORY' | 'DEMO_FIXTURE_FALLBACK' | 'DEMO_FIXTURE' | 'CONFIGURED_PENDING_VERIFICATION' | 'NOT_CONFIGURED' | 'FAILED' | 'ERROR';
  selectedModel: string;
  isInvestigating: boolean;
  hasRun: boolean;
  onLoadCase: () => void;
  onStartInvestigation: () => void;
  onOpenReport: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  providerMode,
  selectedModel,
  isInvestigating,
  hasRun,
  onLoadCase,
  onStartInvestigation,
  onOpenReport,
}) => {
  return (
    <header
      className="app-header"
      style={{
        backgroundColor: 'var(--surface)',
        borderBottom: '1px solid var(--rules)',
        padding: '12px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              backgroundColor: 'var(--ink)',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF',
              fontWeight: 900,
              fontSize: '15px',
            }}
          >
            E
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '17px', fontWeight: 800, letterSpacing: '-0.3px', color: 'var(--ink)' }}>
                ExcursionLens
              </span>
              <span className="badge badge-neutral" title="Strictly synthetic benchmark case">
                Synthetic Benchmark
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
              Cold-Chain Temperature Excursion Investigation Agent &bull; Nebius x NVIDIA Hackathon
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            className={`badge ${
              providerMode === 'LIVE_TOKEN_FACTORY'
                ? 'badge-supported'
                : providerMode === 'CONFIGURED_PENDING_VERIFICATION'
                ? 'badge-neutral'
                : providerMode === 'DEMO_FIXTURE_FALLBACK'
                ? 'badge-unknown'
                : providerMode === 'DEMO_FIXTURE'
                ? 'badge-neutral'
                : 'badge-excursion'
            }`}
            title={`Provider runtime mode: ${providerMode}`}
          >
            {providerMode === 'LIVE_TOKEN_FACTORY'
              ? '● LIVE TOKEN FACTORY'
              : providerMode === 'CONFIGURED_PENDING_VERIFICATION'
              ? '● LIVE VERIFICATION PENDING'
              : providerMode === 'DEMO_FIXTURE_FALLBACK'
              ? '● DEMO FIXTURE FALLBACK'
              : providerMode === 'DEMO_FIXTURE'
              ? '● DEMO FIXTURE'
              : '● PROVIDER FAILED'}
          </span>
          <span className="badge badge-accent" title="NVIDIA Open-Source Model">
            {selectedModel.replace('nvidia/', '')}
          </span>
        </div>

        <button
          className="btn-secondary"
          onClick={onLoadCase}
          disabled={isInvestigating}
          title="Reload baseline NMB-204 case"
        >
          Reload NMB-204
        </button>

        <button
          className="btn-danger"
          onClick={onStartInvestigation}
          disabled={isInvestigating}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          {isInvestigating ? 'Investigating…' : 'Investigate Excursion'}
        </button>

        {hasRun && (
          <button
            className="btn-primary"
            onClick={onOpenReport}
            title="Open printable review packet"
          >
            Review Packet
          </button>
        )}
      </div>
    </header>
  );
};
