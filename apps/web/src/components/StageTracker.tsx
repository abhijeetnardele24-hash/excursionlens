import React from 'react';
import { ToolEvent } from '../types';

interface StageTrackerProps {
  currentStage: string;
  isInvestigating: boolean;
  toolEvents: ToolEvent[];
}

const STAGES = [
  { key: 'VALIDATING', label: '1. Validate Schema' },
  { key: 'NORMALIZING', label: '2. Normalize Series' },
  { key: 'EXCURSION_DETECTED', label: '3. Detect Excursion' },
  { key: 'RESEARCHING', label: '4. Tavily Guidance' },
  { key: 'HYPOTHESES_DRAFTED', label: '5. Nemotron Hypotheses' },
  { key: 'SKEPTIC_REVIEWED', label: '6. Adversarial Skeptic' },
  { key: 'CLAIMS_VALIDATED', label: '7. Validate Citations' },
  { key: 'HUMAN_REVIEW_READY', label: '8. Quality Review Packet' },
];

export const StageTracker: React.FC<StageTrackerProps> = ({
  currentStage,
  isInvestigating,
  toolEvents,
}) => {
  const currentIdx = STAGES.findIndex((s) => s.key === currentStage);

  return (
    <div className="card" style={{ marginBottom: '16px' }}>
      <div className="card-header">
        <h2 className="card-title">Investigation Stage Stepper</h2>
        {isInvestigating && (
          <span className="badge badge-accent" style={{ animation: 'pulse 1.5s infinite' }}>
            ● Stage Transition in Progress…
          </span>
        )}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '8px',
          alignItems: 'stretch',
        }}
      >
        {STAGES.map((s, idx) => {
          const isCompleted = currentIdx > idx || currentStage === 'HUMAN_REVIEW_READY';
          const isCurrent = currentStage === s.key && isInvestigating;

          let bg = 'var(--surface-raised)';
          let borderColor = 'var(--rules)';
          let color = 'var(--muted)';
          let badgeText = 'PENDING';

          if (isCompleted) {
            bg = 'var(--supported-bg)';
            borderColor = 'var(--supported)';
            color = 'var(--supported)';
            badgeText = 'DONE';
          } else if (isCurrent) {
            bg = 'var(--accent-bg)';
            borderColor = 'var(--accent)';
            color = 'var(--accent)';
            badgeText = 'ACTIVE';
          }

          return (
            <div
              key={s.key}
              style={{
                backgroundColor: bg,
                border: `1px solid ${borderColor}`,
                borderRadius: 'var(--radius-sm)',
                padding: '8px 10px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ fontSize: '11px', fontWeight: 700, color, marginBottom: '4px' }}>
                {s.label}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 700,
                    letterSpacing: '0.4px',
                    color,
                  }}
                >
                  {badgeText}
                </span>
                {isCompleted && <span style={{ color: 'var(--supported)', fontSize: '11px' }}>✓</span>}
              </div>
            </div>
          );
        })}
      </div>

      {toolEvents.length > 0 && (
        <div
          tabIndex={0}
          role="region"
          aria-label="Latest Investigation Log Message"
          style={{
            marginTop: '12px',
            backgroundColor: 'var(--canvas)',
            padding: '8px 12px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--ink-secondary)',
            maxHeight: '60px',
            overflowY: 'auto',
          }}
        >
          <strong>Latest Event:</strong> {toolEvents[toolEvents.length - 1]?.summary}
        </div>
      )}
    </div>
  );
};
