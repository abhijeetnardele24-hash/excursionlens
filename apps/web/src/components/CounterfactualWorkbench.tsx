import React, { useState } from 'react';
import { CounterfactualResult } from '../types';

interface CounterfactualWorkbenchProps {
  runId: string;
  counterfactual?: CounterfactualResult;
  onSimulate: (interventionType: string) => Promise<void>;
}

export const CounterfactualWorkbench: React.FC<CounterfactualWorkbenchProps> = ({
  runId,
  counterfactual,
  onSimulate,
}) => {
  const [selectedIntervention, setSelectedIntervention] = useState('EXPEDITE_DOOR_CLOSING');
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    try {
      await onSimulate(selectedIntervention);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginTop: '16px' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 className="card-title">Counterfactual Preventive Control Workbench</h2>
          <span className="badge badge-accent">Action-Oriented Replay</span>
        </div>
        <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
          Replays modified timeline facts to evaluate preventive controls
        </span>
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '14px' }}>
        <label htmlFor="intervention-select" style={{ fontSize: '12px', fontWeight: 700, color: 'var(--ink)' }}>
          Select Preventive Intervention:
        </label>
        <select
          id="intervention-select"
          aria-label="Select Preventive Intervention"
          value={selectedIntervention}
          onChange={(e) => setSelectedIntervention(e.target.value)}
          style={{
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--rules)',
            backgroundColor: 'var(--surface)',
            fontSize: '13px',
            fontFamily: 'inherit',
          }}
        >
          <option value="EXPEDITE_DOOR_CLOSING">1. Expedite Door Closing (5 min limit vs 24 min observed)</option>
          <option value="RELOCATE_LOGGER_DEEP">2. Thermal Mass Probe Replay (Core probe peak 6.8°C)</option>
          <option value="BACKUP_REEFER_ENGAGED">3. Standby Active Chilling During Staging</option>
          <option value="NO_TRANSFER_DELAY">4. Direct Cross-Dock Transfer (Eliminate staging delay)</option>
        </select>

        <button
          className="btn-primary"
          onClick={handleRun}
          disabled={loading || !runId}
          style={{ padding: '6px 14px' }}
        >
          {loading ? 'Simulating...' : 'Replay Counterfactual'}
        </button>
      </div>

      {counterfactual ? (
        <div
          style={{
            backgroundColor: 'var(--surface-raised)',
            border: '1px solid var(--rules-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span className="badge badge-supported">Simulation Completed</span>
            <div style={{ fontSize: '13px' }}>
              Baseline Excursion: <strong className="tabular-nums">{counterfactual.original_excursion_duration_minutes.toFixed(1)}m</strong> &rarr;{' '}
              Simulated Excursion:{' '}
              <strong className="tabular-nums" style={{ color: 'var(--supported)', fontSize: '15px' }}>
                {counterfactual.simulated_excursion_duration_minutes.toFixed(1)}m
              </strong>
            </div>
          </div>

          <p style={{ fontSize: '13px', color: 'var(--ink)', marginBottom: '10px' }}>
            <strong>Outcome:</strong> {counterfactual.result_summary}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px', marginBottom: '8px' }}>
            <div>
              <strong style={{ color: 'var(--supported)' }}>Modified Facts:</strong>
              <ul style={{ paddingLeft: '16px', color: 'var(--ink-secondary)', marginTop: '2px' }}>
                {counterfactual.changed_fact_ids.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
            <div>
              <strong style={{ color: 'var(--muted)' }}>Unchanged Constants:</strong>
              <ul style={{ paddingLeft: '16px', color: 'var(--muted)', marginTop: '2px' }}>
                {counterfactual.unchanged_fact_ids.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          </div>

          <div style={{ fontSize: '11px', color: 'var(--muted)', fontStyle: 'italic', borderTop: '1px solid var(--rules-subtle)', paddingTop: '6px' }}>
            <strong>Physical Limits:</strong> {counterfactual.limits}
          </div>
        </div>
      ) : (
        <div style={{ fontSize: '12px', color: 'var(--muted)', padding: '10px', backgroundColor: 'var(--canvas)', borderRadius: 'var(--radius-sm)' }}>
          Select an intervention above and click <strong>Replay Counterfactual</strong> to see how preventive controls alter time-series excursion bounds.
        </div>
      )}
    </div>
  );
};
