export interface ShipmentProfile {
  shipment_id: string;
  origin: string;
  destination: string;
  carrier: string;
  transport_mode: string;
}

export interface ProductProfile {
  product_name: string;
  product_class: string;
  lot_number: string;
  dose_count: number;
}

export interface TemperaturePolicy {
  min_celsius: number;
  max_celsius: number;
  critical_high_celsius?: number;
  critical_low_celsius?: number;
  max_allowed_excursion_minutes: number;
}

export interface SensorReading {
  timestamp: string;
  temperature_celsius: number;
  sensor_id?: string;
  ambient_celsius?: number;
  battery_pct?: number;
  location?: string;
}

export interface CustodyEvent {
  id: string;
  timestamp: string;
  event_type: string;
  location: string;
  actor: string;
  notes?: string;
}

export interface OperationalEvent {
  id: string;
  timestamp: string;
  event_type: string;
  duration_minutes?: number;
  details?: string;
}

export interface ShipmentCase {
  id: string;
  title: string;
  synthetic: boolean;
  created_at: string;
  shipment: ShipmentProfile;
  product_profile: ProductProfile;
  temperature_policy: TemperaturePolicy;
  readings: SensorReading[];
  custody_events: CustodyEvent[];
  operational_events: OperationalEvent[];
  input_digest?: string;
}

export interface Observation {
  id: string;
  kind: string;
  start_at: string;
  end_at: string;
  numeric_values: Record<string, number>;
  unit: string;
  summary: string;
  source_event_ids: string[];
  detector_version: string;
}

export interface SourceRecord {
  id: string;
  url: string;
  title: string;
  domain: string;
  published_or_updated_at?: string;
  retrieved_at: string;
  snippet: string;
  content_digest: string;
  query: string;
}

export interface Hypothesis {
  id: string;
  label: string;
  summary: string;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  unknowns: string[];
  next_check: string;
  confidence_band: 'HIGH' | 'MEDIUM' | 'LOW' | 'UNSUPPORTED';
  status: 'LEADING' | 'ALTERNATIVE' | 'DOWNGRADED' | 'REJECTED';
  what_it_does_not_establish: string;
}

export interface SkepticCritique {
  hypothesis_id: string;
  attack_summary: string;
  unsupported_claims: string[];
  ignored_contradictions: string[];
  recommended_status: 'LEADING' | 'ALTERNATIVE' | 'DOWNGRADED' | 'REJECTED';
  rationale: string;
}

export interface CounterfactualResult {
  id: string;
  run_id: string;
  intervention_type: string;
  parameters: Record<string, unknown>;
  changed_fact_ids: string[];
  unchanged_fact_ids: string[];
  original_excursion_duration_minutes: number;
  simulated_excursion_duration_minutes: number;
  result_summary: string;
  limits: string;
}

export interface ToolEvent {
  timestamp: string;
  tool_name: string;
  status: string;
  summary: string;
}

export interface InvestigationRun {
  id: string;
  case_id: string;
  state: string;
  created_at: string;
  completed_at?: string;
  provider_mode: 'LIVE_TOKEN_FACTORY' | 'DEMO_FIXTURE' | 'ERROR';
  requested_model: string;
  served_model?: string;
  observations: Observation[];
  sources: SourceRecord[];
  hypotheses: Hypothesis[];
  critiques: SkepticCritique[];
  review_posture: string;
  tool_events: ToolEvent[];
  counterfactual?: CounterfactualResult;
  usage?: Record<string, number>;
  latency_ms?: number;
  validation_result?: {
    passed: boolean;
    error_count: number;
    errors: string[];
  };
  failure_reason?: string;
  disclaimer: string;
}
