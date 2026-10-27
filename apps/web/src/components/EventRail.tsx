import React from 'react';
import { CustodyEvent, OperationalEvent } from '../types';

interface EventRailProps {
  custodyEvents: CustodyEvent[];
  operationalEvents: OperationalEvent[];
}

export const EventRail: React.FC<EventRailProps> = ({ custodyEvents, operationalEvents }) => {
  // Combine and sort events by timestamp
  const allEvents = [
    ...custodyEvents.map((c) => ({
      id: c.id,
      timestamp: c.timestamp,
      type: 'CUSTODY',
      label: c.event_type.replace(/_/g, ' '),
      subtitle: `${c.location} &bull; Actor: ${c.actor}`,
      details: c.notes,
    })),
    ...operationalEvents.map((o) => ({
      id: o.id,
      timestamp: o.timestamp,
      type: 'OPERATIONAL',
      label: o.event_type.replace(/_/g, ' '),
      subtitle: o.duration_minutes ? `Duration: ${o.duration_minutes} min` : 'Telemetry Event',
      details: o.details,
    })),
  ].sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  return (
    <div className="card" style={{ height: '100%' }}>
      <div className="card-header">
        <h2 className="card-title">Custody &amp; Operational Events</h2>
        <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
          {allEvents.length} Aligned Events
        </span>
      </div>

      <div
        tabIndex={0}
        role="region"
        aria-label="Custody and Operational Events Chronicle"
        style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '420px', overflowY: 'auto' }}
      >
        {allEvents.map((e) => {
          const isDoorOpen = e.label.includes('DOOR OPEN');
          const isCustody = e.type === 'CUSTODY';

          return (
            <div
              key={e.id}
              style={{
                backgroundColor: isDoorOpen ? 'var(--excursion-bg)' : 'var(--surface-raised)',
                border: `1px solid ${isDoorOpen ? 'rgba(181,72,45,0.3)' : 'var(--rules-subtle)'}`,
                borderLeft: `3px solid ${isDoorOpen ? 'var(--excursion)' : isCustody ? 'var(--accent)' : 'var(--ink)'}`,
                borderRadius: 'var(--radius-sm)',
                padding: '8px 10px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                <span style={{ fontWeight: 700, fontSize: '12px', color: isDoorOpen ? 'var(--excursion)' : 'var(--ink)' }}>
                  {e.label}
                </span>
                <span className="tabular-nums" style={{ fontSize: '11px', color: 'var(--muted)' }}>
                  {e.timestamp.slice(11, 16)} UTC
                </span>
              </div>

              <div
                style={{ fontSize: '11px', color: 'var(--ink-secondary)', marginBottom: '2px' }}
                dangerouslySetInnerHTML={{ __html: e.subtitle }}
              />

              {e.details && (
                <div style={{ fontSize: '11px', color: 'var(--muted)', fontStyle: 'italic' }}>
                  {e.details}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
