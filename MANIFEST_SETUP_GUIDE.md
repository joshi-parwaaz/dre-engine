# Manifest Setup Guide

This guide explains how to configure `manifest.json` to define your governance rules and assertions for DRE Guardian.

---

## Quick Start

1. Run `guardian init` to create the `project_space/` folder with a template manifest
2. Place your Excel file (e.g., `model.xlsx`) in `project_space/`
3. Edit `manifest.json` to define your assertions
4. Run `guardian doctor` to validate your configuration
5. Run `guardian monitor --dashboard` to start governance tracking

---

## Manifest Structure

```json
{
  "project_id": "my-project",
  "project_name": "My Strategic Model",
  "target_file": "model.xlsx",
  
  "governance_config": {
    "stability_threshold": 0.15,
    "overlap_integral_cutoff": 0.05,
    "freshness_sla_enforcement": true
  },
  
  "assertions": [
    { ... }
  ]
}
```

### Top-Level Fields

| Field | Required | Description |
|-------|----------|-------------|
| `project_id` | Yes | Unique identifier for your project |
| `project_name` | No | Human-readable project name |
| `target_file` | Yes | Excel filename in `project_space/` |
| `governance_config` | No | Override default thresholds |
| `assertions` | Yes | Array of monitored cells |

### Governance Config

| Field | Default | Description |
|-------|---------|-------------|
| `stability_threshold` | 0.15 | Maximum allowed coefficient of variation |
| `overlap_integral_cutoff` | 0.05 | Minimum overlap required between distributions |
| `freshness_sla_enforcement` | true | Enforce SLA deadlines |

---

## Defining Assertions

Each assertion binds a cell in your Excel file to a governance rule.

```json
{
  "id": "ast-001",
  "logical_name": "quarterly_revenue",
  "description": "Q1 2026 revenue projection",
  "owner_role": "VP of Sales",
  "last_updated": "2026-01-15T10:00:00Z",
  "sla_days": 7,
  
  "binding": {
    "cell": "B5",
    "sheet": "Dashboard"
  },
  
  "baseline_value": 1000000.0,
  
  "distribution": {
    "min": 850000.0,
    "mode": 1000000.0,
    "max": 1200000.0
  }
}
```

### Assertion Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier (e.g., `ast-001`) |
| `logical_name` | Yes | Short name for the metric |
| `description` | No | Human-readable explanation |
| `owner_role` | Yes | Who is accountable for this value |
| `last_updated` | Yes | ISO 8601 timestamp of last review |
| `sla_days` | Yes | Days before value is considered stale |
| `binding` | Yes | Excel cell location |
| `baseline_value` | No | Expected current value |
| `distribution` | Yes | PERT distribution bounds |

### Binding Object

| Field | Required | Description |
|-------|----------|-------------|
| `cell` | Yes | Cell reference (e.g., `B5`, `$C$10`) |
| `sheet` | No | Sheet name (defaults to first sheet) |

### Distribution Object (PERT)

| Field | Required | Description |
|-------|----------|-------------|
| `min` | Yes | Pessimistic estimate (lowest reasonable value) |
| `mode` | Yes | Most likely value |
| `max` | Yes | Optimistic estimate (highest reasonable value) |

**Rule:** Must satisfy `min <= mode <= max`

---

## Four-Gate Validation

Each assertion is validated through four gates:

### Gate 1: Freshness
Checks if `last_updated` is within `sla_days` of the current date.

**Fix:** Update the `last_updated` field after reviewing the value.

### Gate 2: Stability  
Checks if the PERT distribution has acceptable variance (coefficient of variation < threshold).

**Fix:** Narrow your min/max range or adjust the threshold.

### Gate 3: Collision
Checks for overlap between related assertions' distributions.

**Fix:** Resolve conflicting assumptions between stakeholders.

### Gate 4: Alignment
Checks if the current Excel value falls within the expected PERT range.

**Fix:** Either update the Excel value or revise your distribution bounds.

---

## Example: Complete Manifest

```json
{
  "project_id": "sales-forecast-2026",
  "project_name": "Annual Sales Forecast",
  "target_file": "forecast.xlsx",
  
  "assertions": [
    {
      "id": "ast-revenue-q1",
      "logical_name": "q1_revenue",
      "owner_role": "Sales Director",
      "last_updated": "2026-02-01T09:00:00Z",
      "sla_days": 14,
      "binding": { "cell": "C5", "sheet": "Summary" },
      "baseline_value": 2500000,
      "distribution": { "min": 2000000, "mode": 2500000, "max": 3200000 }
    },
    {
      "id": "ast-costs-q1",
      "logical_name": "q1_operating_costs",
      "owner_role": "CFO",
      "last_updated": "2026-02-01T09:00:00Z",
      "sla_days": 14,
      "binding": { "cell": "C6", "sheet": "Summary" },
      "baseline_value": 1800000,
      "distribution": { "min": 1600000, "mode": 1800000, "max": 2100000 }
    }
  ]
}
```

---

## Validation Commands

```bash
# Check manifest syntax and Excel bindings
guardian doctor

# Run full governance check (returns exit code for CI/CD)
guardian check

# Start live monitoring with web dashboard
guardian monitor --dashboard
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Sheet not found` | Sheet name doesn't match | Check exact spelling in Excel |
| `Cell is empty` | Referenced cell has no value | Verify cell reference |
| `Distribution violation` | min > mode or mode > max | Reorder distribution values |
| `Stale assertion` | last_updated older than SLA | Update timestamp after review |

---

## Tips

- Use descriptive `logical_name` values for dashboard readability
- Set `sla_days` based on how often the metric actually changes
- Keep `min`/`max` ranges realistic—overly wide ranges reduce governance value
- Run `guardian doctor` after every manifest change
