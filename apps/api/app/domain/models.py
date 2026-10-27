"""
apps/api/app/domain/models.py — Core Domain Models for ExcursionLens

Strict, deterministic Pydantic v2 schemas for:
- Shipment Cases & Sensor Telemetry
- Deterministic Observations & Flags
- Authoritative Source Records
- Structured Hypotheses & Skeptic Critiques
- Investigation Runs & Auditable Event Streams
- Counterfactual Interventions
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ==============================================================================
# 1. Shipment Case & Telemetry
# ==============================================================================

class ShipmentProfile(BaseModel):
    shipment_id: str = Field(..., description="Unique shipment identifier, e.g. NMB-204")
    origin: str = Field(..., description="Origin distribution center or hub")
    destination: str = Field(..., description="Final destination receiving facility")
    carrier: str = Field(..., description="Logistics carrier or fleet")
    transport_mode: str = Field("REFRIGERATED_TRUCK", description="Vehicle/container profile")


class ProductProfile(BaseModel):
    product_name: str = Field(..., description="E.g. Pentavalent Vaccine Training Batch")
    product_class: str = Field(..., description="E.g. Temperature-sensitive biologic")
    lot_number: str = Field(..., description="Batch/Lot identifier")
    dose_count: int = Field(..., ge=1, description="Quantity of units/doses")


class TemperaturePolicy(BaseModel):
    min_celsius: float = Field(2.0, description="Minimum acceptable temperature in Celsius")
    max_celsius: float = Field(8.0, description="Maximum acceptable temperature in Celsius")
    critical_high_celsius: float | None = Field(15.0, description="Emergency critical threshold")
    critical_low_celsius: float | None = Field(0.0, description="Freezing threshold")
    max_allowed_excursion_minutes: int = Field(0, ge=0, description="Allowed cumulative out-of-range minutes before quarantine")


class SensorReading(BaseModel):
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp with timezone")
    temperature_celsius: float = Field(..., description="Recorded temperature in Celsius")
    sensor_id: str = Field("LOGGER-PRIMARY", description="Sensor identifier")
    ambient_celsius: float | None = Field(None, description="External ambient reading")
    battery_pct: float | None = Field(None, ge=0.0, le=100.0, description="Battery percentage")
    location: str | None = Field(None, description="Geographic or facility location tag")


class CustodyEvent(BaseModel):
    id: str = Field(..., description="Unique event identifier, e.g. EVT-CUST-01")
    timestamp: str = Field(..., description="ISO 8601 timestamp with timezone")
    event_type: str = Field(..., description="HANDOFF, LOAD, UNLOAD, TRANSFER, RECEIVE")
    location: str = Field(..., description="Physical facility or checkpoint")
    actor: str = Field(..., description="Responsible personnel or carrier")
    notes: str | None = Field(None, description="Operational notes")


class OperationalEvent(BaseModel):
    id: str = Field(..., description="Unique event identifier, e.g. EVT-OPS-01")
    timestamp: str = Field(..., description="ISO 8601 timestamp with timezone")
    event_type: str = Field(..., description="DOOR_OPEN, DOOR_CLOSE, POWER_DISCONNECT, REEFER_ALERT")
    duration_minutes: float | None = Field(None, ge=0.0, description="Duration in minutes if known")
    details: str | None = Field(None, description="Telemetry details")


class ShipmentCase(BaseModel):
    id: str = Field(..., description="Case identifier, e.g. CASE-NMB-204")
    title: str = Field(..., description="Human-readable case title")
    synthetic: bool = Field(True, description="Strictly true for synthetic benchmark cases")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    shipment: ShipmentProfile
    product_profile: ProductProfile
    temperature_policy: TemperaturePolicy
    readings: list[SensorReading] = Field(..., min_length=1)
    custody_events: list[CustodyEvent] = Field(default_factory=list)
    operational_events: list[OperationalEvent] = Field(default_factory=list)
    input_digest: str | None = Field(None, description="Deterministic SHA-256 of raw input")
    schema_version: str = Field("1.0", description="Schema version")


# ==============================================================================
# 2. Deterministic Observations & Anomalies
# ==============================================================================

ObservationKind = Literal[
    "EXCURSION_WINDOW",
    "TEMPERATURE_SUMMARY",
    "SENSOR_GAP",
    "RATE_OF_CHANGE",
    "JUMP_ANOMALY",
    "SENSOR_DISAGREEMENT"
]


class Observation(BaseModel):
    id: str = Field(..., description="Unique immutable observation ID, e.g. OBS-EXCURSION-01")
    kind: ObservationKind
    start_at: str = Field(..., description="ISO 8601 interval start")
    end_at: str = Field(..., description="ISO 8601 interval end")
    numeric_values: dict[str, float] = Field(default_factory=dict, description="Deterministic measured values")
    unit: str = Field("celsius", description="Measurement unit")
    summary: str = Field(..., description="Fact-based deterministic explanation")
    source_event_ids: list[str] = Field(default_factory=list, description="Associated custody or operational event IDs")
    detector_version: str = Field("1.0", description="Engine version")


class CaseAnalysisResult(BaseModel):
    case_id: str
    has_excursion: bool
    total_excursion_duration_minutes: float
    min_recorded_temperature: float
    max_recorded_temperature: float
    mean_recorded_temperature: float
    reading_count: int
    readings_analyzed: int
    observations: list[Observation]
    anomalies_detected: list[str] = Field(default_factory=list)
    normalized_at: str


# ==============================================================================
# 3. Authoritative Source Records (Tavily Grounding)
# ==============================================================================

class SourceRecord(BaseModel):
    id: str = Field(..., description="Unique source ID, e.g. SRC-CDC-01")
    url: str = Field(..., description="Canonical HTTPS URL")
    title: str = Field(..., description="Document or guideline title")
    domain: str = Field(..., description="Allowlisted domain, e.g. cdc.gov")
    published_or_updated_at: str | None = Field(None, description="Publication or update date")
    retrieved_at: str = Field(..., description="ISO 8601 retrieval timestamp")
    snippet: str = Field(..., description="Relevant text excerpt")
    content_digest: str = Field(..., description="SHA-256 digest of excerpt")
    query: str = Field(..., description="Originating search query")


# ==============================================================================
# 4. Structured Hypotheses & Skeptic Critique
# ==============================================================================

ConfidenceBand = Literal["HIGH", "MEDIUM", "LOW", "UNSUPPORTED"]
HypothesisStatus = Literal["LEADING", "ALTERNATIVE", "DOWNGRADED", "REJECTED"]


class Hypothesis(BaseModel):
    id: str = Field(..., description="Unique hypothesis ID, e.g. HYP-01")
    label: str = Field(..., description="Short descriptive label, e.g. Transfer Exposure")
    summary: str = Field(..., description="Concise causal explanation")
    supporting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Must cite valid Observation IDs or Source IDs"
    )
    contradicting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence contradicting this hypothesis"
    )
    unknowns: list[str] = Field(
        default_factory=list,
        description="Missing facts needed for confirmation"
    )
    next_check: str = Field(
        ...,
        description="Next discriminating check a human reviewer should perform"
    )
    confidence_band: ConfidenceBand
    status: HypothesisStatus = "ALTERNATIVE"
    what_it_does_not_establish: str = Field(
        ...,
        description="Explicit limitation of what this hypothesis cannot prove"
    )


class SkepticCritique(BaseModel):
    hypothesis_id: str
    attack_summary: str
    unsupported_claims: list[str] = Field(default_factory=list)
    ignored_contradictions: list[str] = Field(default_factory=list)
    recommended_status: HypothesisStatus
    rationale: str


# ==============================================================================
# 5. Counterfactual Replay
# ==============================================================================

class CounterfactualRequest(BaseModel):
    intervention_type: Literal[
        "EXPEDITE_DOOR_CLOSING",
        "BACKUP_REEFER_ENGAGED",
        "RELOCATE_LOGGER_DEEP",
        "NO_TRANSFER_DELAY"
    ]
    parameters: dict[str, Any] = Field(default_factory=dict)


class CounterfactualResult(BaseModel):
    id: str
    run_id: str
    intervention_type: str
    parameters: dict[str, Any]
    changed_fact_ids: list[str]
    unchanged_fact_ids: list[str]
    original_excursion_duration_minutes: float
    simulated_excursion_duration_minutes: float
    result_summary: str
    limits: str


# ==============================================================================
# 6. Investigation Run & Event Stream
# ==============================================================================

AgentState = Literal[
    "CREATED",
    "VALIDATING",
    "NORMALIZING",
    "EXCURSION_DETECTED",
    "RESEARCHING",
    "HYPOTHESES_DRAFTED",
    "SKEPTIC_REVIEWED",
    "CLAIMS_VALIDATED",
    "HUMAN_REVIEW_READY",
    "FAILED_TRUTHFULLY"
]

ReviewPosture = Literal[
    "QUARANTINE_PENDING_QUALIFIED_REVIEW",
    "REQUEST_ADDITIONAL_EVIDENCE",
    "ESCALATE_TO_MANUFACTURER"
]

ProviderMode = Literal[
    "LIVE_TOKEN_FACTORY",
    "DEMO_FIXTURE",
    "ERROR"
]


class ToolEvent(BaseModel):
    timestamp: str
    tool_name: str
    status: str
    input_digest: str | None = None
    output_digest: str | None = None
    latency_ms: int | None = None
    summary: str


class InvestigationRun(BaseModel):
    id: str
    case_id: str
    state: AgentState
    created_at: str
    completed_at: str | None = None
    provider_mode: ProviderMode
    requested_model: str
    served_model: str | None = None
    observations: list[Observation] = Field(default_factory=list)
    sources: list[SourceRecord] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    critiques: list[SkepticCritique] = Field(default_factory=list)
    review_posture: ReviewPosture = "QUARANTINE_PENDING_QUALIFIED_REVIEW"
    tool_events: list[ToolEvent] = Field(default_factory=list)
    counterfactual: CounterfactualResult | None = None
    request_digest: str | None = None
    response_digest: str | None = None
    usage: dict[str, int] | None = None
    latency_ms: int | None = None
    validation_result: dict[str, Any] | None = None
    failure_reason: str | None = None
    disclaimer: str = (
        "Investigation support only. Not a product disposition, medical decision, "
        "legal conclusion, or regulatory determination. Keep affected product segregated "
        "and follow your SOP, manufacturer guidance, and responsible authority."
    )
