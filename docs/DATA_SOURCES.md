# ExcursionLens Data Sources & Provenance Specification

ExcursionLens operates on three distinct classes of data: physical IoT sensor telemetry, logistics custody records, and authoritative regulatory references.

---

## 1. IoT Sensor Telemetry Stream

- **Primary Cold-Chain Logger:**
  - Standard measurement interval: 5 minutes.
  - Channels: Surface Temperature (°C), Ambient External Temperature (°C), Relative Humidity (%), and Battery/Bus Voltage (V).
  - Accuracy: ±0.3°C across the critical -20°C to +30°C range.
  - Data payload format: ISO 8601 UTC timestamps, monotonic indexing, floating point Celsius readings.
- **Secondary / Backup Thermal Mass Probe:**
  - Simulates the thermal inertia of liquid vial core volume (e.g. 50-dose antigen vial).
  - Used in counterfactual evaluation to distinguish between brief surface convective warming and core biologic product temperature breach.

---

## 2. Custody & Operational Event Logs

Multimodal events aligned along the common UTC timeline:
- **Custody Handshake Events:**
  - Dispatch, transfer hub arrival, cross-dock handoff, carrier change, receiving dock check-in.
  - Attributes: actor ID, facility name, dock number, signature timestamp, physical tamper-seal verification.
- **Vehicle & Equipment Telemetry Events:**
  - Reefer compressor activation, cargo door sensor state (open/closed duration), auxiliary power unit (APU) bus voltage (12.8V-13.1V nominal).

---

## 3. Authoritative Health Guidelines (Tavily Allowlist)

Real-time guidance retrieval restricted to trusted public health repositories:
- **CDC (Centers for Disease Control and Prevention):**
  - *Vaccine Storage and Handling Toolkit (June 2024)*
  - Temperature monitoring best practices, purpose-built storage units, and emergency response procedures.
  - Domain: `cdc.gov`
- **WHO (World Health Organization):**
  - *Good Distribution Practices for Pharmaceutical Products (Technical Report Series)*
  - Temperature excursion management protocols in cross-dock transit.
  - Domain: `who.int`
- **FDA (Food and Drug Administration):**
  - *21 CFR Part 211 & Part 11 Electronic Records Compliance*
  - Stability testing guidelines and quarantine segregation mandates.
  - Domain: `fda.gov`
- **GS1 Healthcare:**
  - *Global Traceability Standard for Healthcare*
  - Barcode and product lot tracking standards.
  - Domain: `gs1.org`

---

## 4. Provenance Hashing & Retention

- Every ingested file and query snippet receives a SHA-256 digest upon intake.
- These digests are recorded in the structured review packet and JSON audit export to guarantee non-repudiation in pharmaceutical compliance reviews.
