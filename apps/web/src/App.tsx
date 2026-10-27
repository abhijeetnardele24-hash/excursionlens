import React, { useState, useEffect } from 'react';
import { ShipmentCase, InvestigationRun, ToolEvent } from './types';
import { AppHeader } from './components/AppHeader';
import { ShipmentSummaryStrip } from './components/ShipmentSummaryStrip';
import { TemperatureTimeline } from './components/TemperatureTimeline';
import { EventRail } from './components/EventRail';
import { StageTracker } from './components/StageTracker';
import { HypothesisBoard } from './components/HypothesisBoard';
import { SkepticCritiquePanel } from './components/SkepticCritiquePanel';
import { CounterfactualWorkbench } from './components/CounterfactualWorkbench';
import { ProviderProofPanel } from './components/ProviderProofPanel';
import { EvidenceDrawer } from './components/EvidenceDrawer';
import { ReviewPacketModal } from './components/ReviewPacketModal';

export const App: React.FC = () => {
  const [caseData, setCaseData] = useState<ShipmentCase | null>(null);
  const [run, setRun] = useState<InvestigationRun | undefined>(undefined);
  const [currentStage, setCurrentStage] = useState<string>('CREATED');
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [meta, setMeta] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch metadata and default sample case at startup
  useEffect(() => {
    fetchMeta();
    loadSampleCase();
  }, []);

  const fetchMeta = async () => {
    try {
      const res = await fetch('/api/meta');
      if (res.ok) {
        const data = await res.json();
        setMeta(data);
      }
    } catch {
      // Offline fallback
    }
  };

  const loadSampleCase = async () => {
    setError(null);
    try {
      const res = await fetch('/api/cases/sample');
      if (res.ok) {
        const data = await res.json();
        setCaseData(data);
        setRun(undefined);
        setCurrentStage('CREATED');
        setToolEvents([]);
      } else {
        setError('Failed to load sample case from backend.');
      }
    } catch (e: any) {
      setError(`Cannot reach API server: ${e.message}`);
    }
  };

  // 2. Run investigation with real-time SSE stage events
  const handleStartInvestigation = async () => {
    if (!caseData) return;
    setIsInvestigating(true);
    setError(null);
    setCurrentStage('VALIDATING');
    setToolEvents([]);

    try {
      // 1. Initialize single-execution run bound to current case
      const startRes = await fetch(`/api/cases/${caseData.id}/investigations`, {
        method: 'POST',
      });
      if (!startRes.ok) {
        throw new Error(`Failed to start investigation: ${startRes.statusText}`);
      }
      const startData = await startRes.json();
      const runId = startData.run_id;

      // 2. Connect to SSE stream to observe execution
      const eventSource = new EventSource(`/api/investigations/${runId}/events`);

      eventSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.stage) {
            setCurrentStage(payload.stage);
          }
          if (payload.message) {
            setToolEvents((prev) => [
              ...prev,
              {
                timestamp: new Date().toISOString(),
                tool_name: payload.stage,
                status: payload.stage === 'FAILED_TRUTHFULLY' ? 'FAILED' : 'SUCCESS',
                summary: payload.message,
              },
            ]);
          }

          if (payload.data?.completed_run) {
            setRun(payload.data.completed_run);
            setIsInvestigating(false);
            eventSource.close();
          } else if (payload.run) {
            setRun(payload.run);
            if (payload.stage === 'HUMAN_REVIEW_READY' || payload.stage === 'FAILED_TRUTHFULLY') {
              setIsInvestigating(false);
              eventSource.close();
            }
          }
        } catch {
          // ignore parsing error
        }
      };

      eventSource.onerror = async () => {
        eventSource.close();
        // Check final status via GET in case SSE closed at completion
        try {
          const res = await fetch(`/api/investigations/${runId}`);
          if (res.ok) {
            const data = await res.json();
            setRun(data);
            setCurrentStage(data.state);
          }
        } catch {
          // ignore
        } finally {
          setIsInvestigating(false);
        }
      };
    } catch (e: any) {
      setError(`Investigation failed: ${e.message}`);
      setIsInvestigating(false);
    }
  };

  // 3. Counterfactual Simulation
  const handleSimulateCounterfactual = async (interventionType: string, parameters?: Record<string, unknown>) => {
    if (!run) return;
    try {
      const res = await fetch(`/api/investigations/${run.id}/counterfactuals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          intervention_type: interventionType,
          parameters: parameters || {},
        }),
      });
      if (res.ok) {
        const cfResult = await res.json();
        setRun((prev) => (prev ? { ...prev, counterfactual: cfResult } : prev));
      } else {
        const errJson = await res.json();
        setError(`Simulation rejected: ${errJson.detail || 'Invalid parameters'}`);
      }
    } catch (e: any) {
      setError(`Simulation error: ${e.message}`);
    }
  };

  if (!caseData) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2>Loading ExcursionLens Case Workspace…</h2>
        {error && <p style={{ color: 'var(--excursion)', marginTop: '10px' }}>{error}</p>}
        <button className="btn-primary" onClick={loadSampleCase} style={{ marginTop: '12px' }}>
          Retry Connection
        </button>
      </div>
    );
  }

  const providerMode = run?.provider_mode ?? (meta.provider?.nebius_token_factory_configured ? 'CONFIGURED_PENDING_VERIFICATION' : 'DEMO_FIXTURE');
  const selectedModel = meta.provider?.selected_deep_model ?? 'nvidia/llama-3.1-nemotron-70b-instruct';

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Skip to Main Content Link for Keyboard / Screen Reader Accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* Polite Live Region for Dynamic State Announcements */}
      <div
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
        style={{
          position: 'absolute',
          width: '1px',
          height: '1px',
          padding: '0',
          margin: '-1px',
          overflow: 'hidden',
          clip: 'rect(0, 0, 0, 0)',
          whiteSpace: 'nowrap',
          border: '0',
        }}
      >
        {isInvestigating ? `Investigation stage active: ${currentStage}` : ''}
        {error ? `Alert: ${error}` : ''}
      </div>

      {/* 1. Header */}
      <AppHeader
        providerMode={providerMode}
        selectedModel={selectedModel}
        isInvestigating={isInvestigating}
        hasRun={Boolean(run)}
        onLoadCase={loadSampleCase}
        onStartInvestigation={handleStartInvestigation}
        onOpenReport={() => setIsReportOpen(true)}
      />

      {/* 2. Main Operational Canvas */}
      <main id="main-content" style={{ maxWidth: 'var(--max-width)', margin: '0 auto', width: '100%', padding: '20px', flexGrow: 1 }}>
        {/* Shipment Summary & Review Posture Strip */}
        <section aria-label="Shipment Case Overview" style={{ marginBottom: '20px' }}>
          <ShipmentSummaryStrip caseData={caseData} run={run} />
        </section>
        {error && (
          <div
            style={{
              backgroundColor: 'var(--excursion-bg)',
              color: 'var(--excursion)',
              border: '1px solid var(--excursion)',
              padding: '10px 16px',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '16px',
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Real-time Stage Tracker */}
        <StageTracker
          currentStage={currentStage}
          isInvestigating={isInvestigating}
          toolEvents={toolEvents}
        />

        <div className="operational-grid">
          {/* Left Column: Timeline, Hypotheses, Skeptic, Counterfactual */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Primary Temperature Timeline */}
            <TemperatureTimeline
              readings={caseData.readings}
              custodyEvents={caseData.custody_events}
              operationalEvents={caseData.operational_events}
              minAllowed={caseData.temperature_policy.min_celsius}
              maxAllowed={caseData.temperature_policy.max_celsius}
            />

            {/* Competing Hypothesis Board */}
            <HypothesisBoard
              hypotheses={run?.hypotheses ?? []}
              onSelectEvidence={(id) => setSelectedEvidenceId(id)}
            />

            {/* Skeptic Critique Pass */}
            {run?.critiques && <SkepticCritiquePanel critiques={run.critiques} />}

            {/* Counterfactual Workbench */}
            <CounterfactualWorkbench
              runId={run?.id ?? ''}
              counterfactual={run?.counterfactual}
              onSimulate={handleSimulateCounterfactual}
            />

            {/* Provider Proof Panel */}
            <ProviderProofPanel run={run} />
          </div>

          {/* Right Column: Aligned Custody & Operational Event Rail */}
          <div>
            <EventRail
              custodyEvents={caseData.custody_events}
              operationalEvents={caseData.operational_events}
            />
          </div>
        </div>
      </main>

      {/* Modals & Drawers */}
      <EvidenceDrawer
        selectedId={selectedEvidenceId}
        observations={run?.observations ?? []}
        sources={run?.sources ?? []}
        onClose={() => setSelectedEvidenceId(null)}
      />

      <ReviewPacketModal
        isOpen={isReportOpen}
        onClose={() => setIsReportOpen(false)}
        run={run}
        caseData={caseData}
      />

      {/* Sticky Safety Footer */}
      <footer
        style={{
          backgroundColor: 'var(--surface)',
          borderTop: '1px solid var(--rules)',
          padding: '12px 24px',
          fontSize: '11px',
          color: 'var(--muted)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div>
          <strong>Quality Boundary:</strong> Investigation support only. Not a product disposition, medical decision, legal conclusion, or regulatory determination.
        </div>
        <div style={{ display: 'flex', gap: '14px' }}>
          <span>ExcursionLens v1.0.0</span>
          <span>NVIDIA Nemotron via Nebius Token Factory</span>
          <span>Tavily Authoritative Search</span>
        </div>
      </footer>
    </div>
  );
};
