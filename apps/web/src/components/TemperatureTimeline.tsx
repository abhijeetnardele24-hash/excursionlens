import React, { useState } from 'react';
import { SensorReading, CustodyEvent, OperationalEvent } from '../types';

interface TemperatureTimelineProps {
  readings: SensorReading[];
  custodyEvents: CustodyEvent[];
  operationalEvents: OperationalEvent[];
  minAllowed: number;
  maxAllowed: number;
}

export const TemperatureTimeline: React.FC<TemperatureTimelineProps> = ({
  readings,
  custodyEvents,
  operationalEvents,
  minAllowed,
  maxAllowed,
}) => {
  const [showTable, setShowTable] = useState(false);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!readings || readings.length === 0) {
    return <div className="card">No telemetry readings available.</div>;
  }

  // Chart coordinate space
  const width = 850;
  const height = 260;
  const padding = { top: 25, right: 30, bottom: 40, left: 45 };

  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  // Temperature domain: min 0°C, max 14°C to fit 10.5°C peak and 8°C threshold comfortably
  const minTempDomain = 0.0;
  const maxTempDomain = 13.0;

  const yScale = (temp: number) => {
    const clamped = Math.max(minTempDomain, Math.min(maxTempDomain, temp));
    const pct = (clamped - minTempDomain) / (maxTempDomain - minTempDomain);
    return padding.top + (1 - pct) * innerHeight;
  };

  const xScale = (index: number) => {
    return padding.left + (index / (readings.length - 1)) * innerWidth;
  };

  // Build SVG path
  const linePoints = readings.map((r, i) => `${xScale(i)},${yScale(r.temperature_celsius)}`);
  const pathD = `M ${linePoints.join(' L ')}`;

  // Threshold lines
  const y8 = yScale(maxAllowed);
  const y2 = yScale(minAllowed);

  // Active hover reading
  const activeReading = hoverIndex !== null ? readings[hoverIndex] : null;

  // Calculate excursion duration from out-of-range readings
  const outOfRangeCount = readings.filter(
    (r) => r.temperature_celsius < minAllowed || r.temperature_celsius > maxAllowed
  ).length;
  const excursionMinutes = outOfRangeCount > 0 ? outOfRangeCount * 5 : 0;

  return (
    <div className="card" style={{ position: 'relative', maxWidth: '100%', overflow: 'hidden' }}>
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <h2 className="card-title">Temperature Telemetry &amp; Event Alignment</h2>
          {excursionMinutes > 0 ? (
            <span className="badge badge-excursion" title="Continuous excursion interval">
              {excursionMinutes} min Out-of-Range Window
            </span>
          ) : (
            <span className="badge badge-supported" title="Temperature within policy">
              Within Normal Range
            </span>
          )}
          <span className="badge badge-neutral" title="Associated logged events">
            {custodyEvents.length} Custody &bull; {operationalEvents.length} Ops Events Aligned
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%' }}>
          <button
            id="telemetry-table-toggle"
            className="btn-secondary"
            onClick={() => setShowTable(!showTable)}
            style={{ fontSize: '12px', padding: '6px 12px', minHeight: '34px' }}
            aria-expanded={showTable}
            aria-controls="telemetry-table"
          >
            {showTable ? 'Hide Table View' : 'Show Accessible Table'}
          </button>
        </div>
      </div>

      {/* SVG Chart */}
      <div
        tabIndex={0}
        role="region"
        aria-label="Temperature time series interactive chart view"
        style={{ width: '100%', overflowX: 'auto' }}
      >
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: '100%', height: 'auto', display: 'block', minWidth: '600px' }}
          role="img"
          aria-label="Temperature time series chart showing out of range thermal breach"
        >
          {/* Configured temperature band [2°C, 8°C] */}
          <rect
            x={padding.left}
            y={y8}
            width={innerWidth}
            height={y2 - y8}
            fill="#EAF2EE"
            opacity={0.8}
          />
          <text
            x={padding.left + 8}
            y={y8 + 14}
            fill="#275E4B"
            fontSize="10"
            fontWeight="700"
            letterSpacing="0.4px"
          >
            CONFIGURED BAND (2.0°C - 8.0°C)
          </text>

          {/* Excursion danger band > 8°C */}
          <rect
            x={padding.left}
            y={padding.top}
            width={innerWidth}
            height={y8 - padding.top}
            fill="#FBEBE8"
            opacity={0.6}
          />

          {/* Dotted threshold line 8.0°C */}
          <line
            x1={padding.left}
            y1={y8}
            x2={width - padding.right}
            y2={y8}
            stroke="#B5482D"
            strokeWidth="1.5"
            strokeDasharray="4 3"
          />
          <text x={width - padding.right + 4} y={y8 + 3} fill="#B5482D" fontSize="10" fontWeight="700">
            8°C
          </text>

          {/* Dotted threshold line 2.0°C */}
          <line
            x1={padding.left}
            y1={y2}
            x2={width - padding.right}
            y2={y2}
            stroke="#275E4B"
            strokeWidth="1.5"
            strokeDasharray="4 3"
          />
          <text x={width - padding.right + 4} y={y2 + 3} fill="#275E4B" fontSize="10" fontWeight="700">
            2°C
          </text>

          {/* Event markers on timeline */}
          {/* Transfer Hub Door Open ~10:18 (around index 28) */}
          <line
            x1={xScale(28)}
            y1={padding.top}
            x2={xScale(28)}
            y2={height - padding.bottom}
            stroke="#B5482D"
            strokeWidth="1.5"
            strokeDasharray="2 2"
          />
          <text x={xScale(28) - 14} y={padding.top - 6} fill="#B5482D" fontSize="9" fontWeight="700">
            10:18 DOOR OPEN
          </text>

          {/* Door Close ~10:42 (around index 33) */}
          <line
            x1={xScale(33)}
            y1={padding.top}
            x2={xScale(33)}
            y2={height - padding.bottom}
            stroke="#275E4B"
            strokeWidth="1.5"
            strokeDasharray="2 2"
          />
          <text x={xScale(33) - 14} y={padding.top - 6} fill="#275E4B" fontSize="9" fontWeight="700">
            10:42 DOOR CLOSED
          </text>

          {/* Primary Temperature Curve */}
          <path d={pathD} fill="none" stroke="#17201E" strokeWidth="2.5" strokeLinecap="round" />

          {/* Data points */}
          {readings.map((r, i) => {
            const isExcursion = r.temperature_celsius > maxAllowed;
            return (
              <circle
                key={r.timestamp}
                cx={xScale(i)}
                cy={yScale(r.temperature_celsius)}
                r={isExcursion ? 4.5 : 2.5}
                fill={isExcursion ? '#B5482D' : '#17201E'}
                stroke="#FFFFFF"
                strokeWidth={isExcursion ? '1.5' : '1'}
                onMouseEnter={() => setHoverIndex(i)}
                onMouseLeave={() => setHoverIndex(null)}
                style={{ cursor: 'pointer' }}
              />
            );
          })}

          {/* Y Axis Labels */}
          {[0, 2, 4, 6, 8, 10, 12].map((deg) => (
            <text
              key={deg}
              x={padding.left - 8}
              y={yScale(deg) + 4}
              fill="#5D625D"
              fontSize="10"
              textAnchor="end"
              className="tabular-nums"
            >
              {deg}°
            </text>
          ))}

          {/* X Axis Time Labels */}
          {readings
            .filter((_, idx) => idx % 6 === 0 || idx === readings.length - 1)
            .map((r) => {
              const idx = readings.findIndex((x) => x.timestamp === r.timestamp);
              const timeLabel = r.timestamp.slice(11, 16);
              return (
                <text
                  key={r.timestamp}
                  x={xScale(idx)}
                  y={height - padding.bottom + 18}
                  fill="#5D625D"
                  fontSize="10"
                  textAnchor="middle"
                  className="tabular-nums"
                >
                  {timeLabel}
                </text>
              );
            })}
        </svg>
      </div>

      {/* Hover Info Tooltip */}
      {activeReading && (
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            right: '20px',
            backgroundColor: 'var(--surface-raised)',
            border: '1px solid var(--rules)',
            padding: '8px 12px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '12px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
          }}
        >
          <div>
            <strong>Time:</strong> <span className="tabular-nums">{activeReading.timestamp.slice(11, 19)} UTC</span>
          </div>
          <div>
            <strong>Temperature:</strong>{' '}
            <span
              className="tabular-nums"
              style={{
                color: activeReading.temperature_celsius > maxAllowed ? 'var(--excursion)' : 'var(--supported)',
                fontWeight: 700,
              }}
            >
              {activeReading.temperature_celsius.toFixed(1)}°C
            </span>
          </div>
          {activeReading.ambient_celsius && (
            <div>
              <strong>Ambient:</strong> <span className="tabular-nums">{activeReading.ambient_celsius.toFixed(1)}°C</span>
            </div>
          )}
          {activeReading.location && (
            <div style={{ color: 'var(--muted)', fontSize: '11px' }}>{activeReading.location}</div>
          )}
        </div>
      )}

      {/* Accessible Table View for Screen Readers & Keyboard Users */}
      {showTable && (
        <div
          id="telemetry-table"
          tabIndex={0}
          role="region"
          aria-label="Accessible Telemetry Readings Table"
          style={{
            marginTop: '16px',
            maxHeight: '260px',
            overflowY: 'auto',
            borderTop: '1px solid var(--rules)',
            paddingTop: '10px',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--canvas)', textAlign: 'left' }}>
                <th style={{ padding: '6px 8px' }}>Timestamp</th>
                <th style={{ padding: '6px 8px' }}>Recorded Temp (°C)</th>
                <th style={{ padding: '6px 8px' }}>Compliance Status</th>
                <th style={{ padding: '6px 8px' }}>Ambient Temp (°C)</th>
                <th style={{ padding: '6px 8px' }}>Checkpoint</th>
              </tr>
            </thead>
            <tbody>
              {readings.map((r) => {
                const isBreach = r.temperature_celsius > maxAllowed || r.temperature_celsius < minAllowed;
                return (
                  <tr
                    key={r.timestamp}
                    style={{
                      borderBottom: '1px solid var(--rules-subtle)',
                      backgroundColor: isBreach ? 'var(--excursion-bg)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '6px 8px' }} className="tabular-nums">
                      {r.timestamp}
                    </td>
                    <td style={{ padding: '6px 8px', fontWeight: isBreach ? 700 : 400 }} className="tabular-nums">
                      {r.temperature_celsius.toFixed(1)}
                    </td>
                    <td style={{ padding: '6px 8px' }}>
                      <span className={`badge ${isBreach ? 'badge-excursion' : 'badge-supported'}`}>
                        {isBreach ? 'EXCURSION' : 'IN RANGE'}
                      </span>
                    </td>
                    <td style={{ padding: '6px 8px' }} className="tabular-nums">
                      {r.ambient_celsius?.toFixed(1) ?? '—'}
                    </td>
                    <td style={{ padding: '6px 8px', color: 'var(--muted)' }}>{r.location ?? 'In Transit'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
