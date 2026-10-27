import React from 'react';
import { ShipmentCase, InvestigationRun } from '../types';

interface ShipmentSummaryStripProps {
  caseData: ShipmentCase;
  run?: InvestigationRun;
}

export const ShipmentSummaryStrip: React.FC<ShipmentSummaryStripProps> = ({ caseData, run }) => {
  const hasExcursion = run
    ? run.observations.some((o) => o.kind === 'EXCURSION_WINDOW')
    : true; // Default for NMB-204

  const excursionObs = run?.observations.find((o) => o.kind === 'EXCURSION_WINDOW');
  const duration = excursionObs?.numeric_values.duration_minutes ?? 42;
  const maxTemp = excursionObs?.numeric_values.max_temperature ?? 10.5;

  return (
    <div style={{ backgroundColor: 'var(--surface)', borderBottom: '1px solid var(--rules)' }}>
      {/* Primary summary strip */}
      <div
        style={{
          padding: '14px 24px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '16px',
          borderBottom: '1px solid var(--rules-subtle)',
        }}
      >
        <div>
          <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', display: 'block' }}>
            Shipment ID
          </span>
          <strong style={{ fontSize: '16px', color: 'var(--ink)' }}>{caseData.shipment.shipment_id}</strong>
          <div style={{ fontSize: '12px', color: 'var(--muted)' }}>{caseData.shipment.transport_mode}</div>
        </div>

        <div>
          <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', display: 'block' }}>
            Product Batch
          </span>
          <strong style={{ fontSize: '13px', color: 'var(--ink)' }}>{caseData.product_profile.product_name}</strong>
          <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
            Lot: {caseData.product_profile.lot_number} &bull; {caseData.product_profile.dose_count.toLocaleString()} doses
          </div>
        </div>

        <div>
          <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', display: 'block' }}>
            Route Leg
          </span>
          <div style={{ fontSize: '12px', fontWeight: 600 }}>Albany DC &rarr; Kingston Clinic</div>
          <div style={{ fontSize: '11px', color: 'var(--muted)' }}>Via Newburgh Transfer Hub</div>
        </div>

        <div>
          <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', display: 'block' }}>
            Policy Limits
          </span>
          <div style={{ fontSize: '13px', fontWeight: 700 }} className="tabular-nums">
            {caseData.temperature_policy.min_celsius.toFixed(1)}°C to {caseData.temperature_policy.max_celsius.toFixed(1)}°C
          </div>
          <div style={{ fontSize: '11px', color: 'var(--muted)' }}>Cold-Chain Standard (2°C-8°C)</div>
        </div>

        <div>
          <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', display: 'block' }}>
            Measured Breach
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="badge badge-excursion tabular-nums" style={{ fontSize: '13px' }}>
              +{duration} min &bull; Peak {maxTemp.toFixed(1)}°C
            </span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--excursion)', fontWeight: 600 }}>Threshold breach detected</div>
        </div>
      </div>

      {/* Recommended posture banner */}
      <div
        style={{
          padding: '10px 24px',
          backgroundColor: hasExcursion ? 'var(--excursion-bg)' : 'var(--supported-bg)',
          borderLeft: `4px solid ${hasExcursion ? 'var(--excursion)' : 'var(--supported)'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontWeight: 800, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.4px', color: hasExcursion ? 'var(--excursion)' : 'var(--supported)' }}>
            Recommended Quality Posture:
          </span>
          <strong style={{ fontSize: '13px', color: 'var(--ink)' }}>
            {run?.review_posture.replace(/_/g, ' ') || 'QUARANTINE PENDING QUALIFIED REVIEW'}
          </strong>
          <span style={{ fontSize: '12px', color: 'var(--muted)' }}>
            &bull; Physical inventory must remain segregated. Never auto-release based solely on AI hypothesis.
          </span>
        </div>
      </div>
    </div>
  );
};
