"""
apps/api/app/reports/generator.py — Human Review Packet Generator (Printable HTML & JSON)

Produces audit-ready, printable HTML packets conforming to cold-chain quality standards:
- Clear separation of observed physical facts vs synthesized causal hypotheses.
- Evidence index citing Observation IDs and Tavily Source IDs.
- Mandated safety disclaimer and human sign-off block.
- Styled with forensic operations typography and print CSS.
"""

from ..domain.models import InvestigationRun, ShipmentCase


def generate_printable_html_report(run: InvestigationRun, case: ShipmentCase) -> str:
    """Renders a self-contained, print-optimized HTML review packet."""
    obs_rows = "".join(
        f"""<tr>
            <td><code>{o.id}</code></td>
            <td><strong>{o.kind}</strong></td>
            <td>{o.summary}</td>
            <td>{', '.join(f'<code>{k}: {v}</code>' for k, v in o.numeric_values.items()) if o.numeric_values else '—'}</td>
        </tr>"""
        for o in run.observations
    )

    hyp_cards = "".join(
        f"""<div class="hyp-card status-{h.status.lower()}">
            <div class="hyp-header">
                <span class="hyp-badge">{h.status}</span>
                <h3>{h.id}: {h.label}</h3>
                <span class="confidence">Confidence: <strong>{h.confidence_band}</strong></span>
            </div>
            <p class="summary">{h.summary}</p>
            <div class="evidence-grid">
                <div>
                    <strong>Supporting Evidence:</strong>
                    <ul>{''.join(f'<li><code>{e}</code></li>' for e in h.supporting_evidence_ids) or '<li>None</li>'}</ul>
                </div>
                <div>
                    <strong>Contradictions:</strong>
                    <ul>{''.join(f'<li><code>{e}</code></li>' for e in h.contradicting_evidence_ids) or '<li>None</li>'}</ul>
                </div>
                <div>
                    <strong>Unknowns:</strong>
                    <ul>{''.join(f'<li>{u}</li>' for u in h.unknowns) or '<li>None</li>'}</ul>
                </div>
            </div>
            <div class="next-check">
                <strong>Next Discriminating Check:</strong> {h.next_check}
            </div>
            <div class="boundary-note">
                <em>Boundary: {h.what_it_does_not_establish}</em>
            </div>
        </div>"""
        for h in run.hypotheses
    )

    source_rows = "".join(
        f"""<tr>
            <td><code>{s.id}</code></td>
            <td><a href="{s.url}" target="_blank" rel="noopener">{s.title}</a></td>
            <td><code>{s.domain}</code></td>
            <td>{s.snippet}</td>
        </tr>"""
        for s in run.sources
    )

    cf_section = ""
    if run.counterfactual:
        cf = run.counterfactual
        cf_section = f"""
        <section class="report-section">
            <h2>Counterfactual Preventive Control Replay</h2>
            <div class="cf-box">
                <p><strong>Intervention:</strong> <code>{cf.intervention_type}</code></p>
                <p><strong>Baseline Excursion:</strong> {cf.original_excursion_duration_minutes:.1f} min &rarr; <strong>Simulated Excursion:</strong> {cf.simulated_excursion_duration_minutes:.1f} min</p>
                <p><strong>Outcome:</strong> {cf.result_summary}</p>
                <p><em>Limits: {cf.limits}</em></p>
            </div>
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ExcursionLens Incident Packet — {case.shipment.shipment_id}</title>
    <style>
        :root {{
            --canvas: #F3F0E8;
            --ink: #17201E;
            --muted: #5D625D;
            --rules: #C8C1B3;
            --excursion: #B5482D;
            --supported: #275E4B;
            --unknown: #9A6A1F;
            --accent: #365E7D;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            background: #FFFFFF;
            color: var(--ink);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            padding: 40px;
            max-width: 960px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 2px solid var(--ink);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .badge {{
            background: var(--canvas);
            border: 1px solid var(--rules);
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .posture-banner {{
            background: #FBEBE8;
            border-left: 4px solid var(--excursion);
            padding: 16px;
            margin: 20px 0;
            font-size: 15px;
        }}
        .posture-title {{
            font-size: 18px;
            font-weight: 800;
            color: var(--excursion);
            margin: 0 0 6px 0;
        }}
        .disclaimer-box {{
            background: var(--canvas);
            border: 1px solid var(--rules);
            padding: 14px;
            font-size: 12px;
            color: var(--muted);
            margin-bottom: 30px;
        }}
        .report-section {{
            margin-bottom: 35px;
        }}
        h2 {{
            font-size: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--rules);
            padding-bottom: 6px;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 10px;
        }}
        th, td {{
            border: 1px solid var(--rules);
            padding: 8px 10px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background: var(--canvas);
            font-weight: 700;
        }}
        code {{
            font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
            background: var(--canvas);
            padding: 2px 4px;
            font-size: 12px;
        }}
        .hyp-card {{
            border: 1px solid var(--rules);
            padding: 16px;
            margin-bottom: 15px;
            background: #FAFAFA;
        }}
        .hyp-card.status-leading {{
            border-left: 4px solid var(--supported);
        }}
        .hyp-card.status-downgraded {{
            border-left: 4px solid var(--excursion);
            opacity: 0.85;
        }}
        .hyp-card.status-alternative {{
            border-left: 4px solid var(--unknown);
        }}
        .hyp-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}
        .hyp-header h3 {{
            margin: 0;
            font-size: 15px;
            flex-grow: 1;
        }}
        .evidence-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            font-size: 12px;
            background: var(--canvas);
            padding: 10px;
            margin: 12px 0;
        }}
        .evidence-grid ul {{
            margin: 4px 0 0 0;
            padding-left: 16px;
        }}
        .signoff-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 25px;
        }}
        .signoff-field {{
            border-bottom: 1px solid var(--rules);
            padding-bottom: 8px;
            margin-bottom: 20px;
        }}
        .signoff-field span {{
            font-size: 11px;
            color: var(--muted);
            text-transform: uppercase;
            display: block;
        }}
        @media print {{
            body {{ padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-top">
            <div>
                <span class="badge">Cold-Chain Incident Review Packet</span>
                <h1 style="margin: 8px 0 4px 0; font-size: 24px;">ExcursionLens Investigation Report</h1>
                <p style="margin: 0; color: var(--muted); font-size: 13px;">Shipment ID: <strong>{case.shipment.shipment_id}</strong> &bull; Product: <strong>{case.product_profile.product_name}</strong> &bull; Run ID: <code>{run.id}</code></p>
            </div>
            <div style="text-align: right;">
                <span class="badge" style="background: #E8F0FE; color: var(--accent);">NVIDIA Nemotron via Nebius</span><br>
                <small style="color: var(--muted);">Generated: {run.completed_at or run.created_at}</small>
            </div>
        </div>

        <div class="posture-banner">
            <div class="posture-title">Recommended Review Posture: {run.review_posture.replace('_', ' ')}</div>
            <div>Automated excursion analysis detected out-of-range thermal exposure. Mandatory product quarantine is in effect pending qualified pharmacist/QA sign-off.</div>
        </div>

        <div class="disclaimer-box">
            <strong>Mandatory Quality Boundary:</strong> {run.disclaimer}
        </div>
    </header>

    <section class="report-section">
        <h2>1. Physical Shipment &amp; Policy Metadata</h2>
        <table>
            <tr><th>Shipment ID</th><td>{case.shipment.shipment_id}</td><th>Product Batch</th><td>{case.product_profile.product_name} (Lot {case.product_profile.lot_number})</td></tr>
            <tr><th>Origin / Destination</th><td>{case.shipment.origin} &rarr; {case.shipment.destination}</td><th>Dose Quantity</th><td>{case.product_profile.dose_count:,} units</td></tr>
            <tr><th>Allowed Temperature Band</th><td>{case.temperature_policy.min_celsius}&deg;C to {case.temperature_policy.max_celsius}&deg;C</td><th>Critical Limits</th><td>Min {case.temperature_policy.critical_low_celsius}&deg;C / Max {case.temperature_policy.critical_high_celsius}&deg;C</td></tr>
        </table>
    </section>

    <section class="report-section">
        <h2>2. Deterministic Excursion Observations</h2>
        <table>
            <thead>
                <tr><th style="width: 140px;">Observation ID</th><th style="width: 160px;">Kind</th><th>Fact Summary</th><th>Measured Telemetry</th></tr>
            </thead>
            <tbody>
                {obs_rows}
            </tbody>
        </table>
    </section>

    <section class="report-section">
        <h2>3. NVIDIA Nemotron Causal Hypotheses &amp; Skeptic Critique</h2>
        {hyp_cards}
    </section>

    <section class="report-section">
        <h2>4. Authoritative Guidance Evidence (Tavily Search Grounding)</h2>
        <table>
            <thead>
                <tr><th style="width: 120px;">Source ID</th><th>Title &amp; Canonical Reference</th><th>Domain</th><th>Relevant Excerpt</th></tr>
            </thead>
            <tbody>
                {source_rows}
            </tbody>
        </table>
    </section>

    {cf_section}

    <section class="report-section" style="page-break-inside: avoid;">
        <h2>5. Qualified Human Disposition Sign-Off</h2>
        <p style="font-size: 13px; color: var(--muted); margin-bottom: 20px;">
            In accordance with CDC Vaccine Storage and Handling Guidelines and FDA ICH Q1A standards, the undersigned qualified individual has reviewed the telemetry, competing hypotheses, and authoritative guidance, and verified physical product quarantine status.
        </p>
        <div class="signoff-grid">
            <div>
                <div class="signoff-field"><span>Reviewing Quality Authority (Print Name)</span></div>
                <div class="signoff-field"><span>Professional Title / Credentials</span></div>
                <div class="signoff-field"><span>Official Quality Determination (Release / Escalate / Discard)</span></div>
            </div>
            <div>
                <div class="signoff-field"><span>Authorized Signature</span></div>
                <div class="signoff-field"><span>Review Date &amp; Time</span></div>
                <div class="signoff-field"><span>Manufacturer Escalation Reference # (if applicable)</span></div>
            </div>
        </div>
    </section>
</body>
</html>"""
