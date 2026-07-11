# Metadata Catalog And Lineage

## Purpose

Metadata and lineage explain what each dataset means, who owns it, where it comes from, and what breaks if it fails.

## Catalog Fields

The catalog tracks:

- dataset name
- layer
- owner
- source system
- refresh frequency
- criticality tier
- business description
- downstream usage
- readiness status

## Lineage Scope

The project emits OpenLineage-style events across:

- raw source files
- bronze datasets
- silver datasets
- dbt staging/intermediate/mart models
- gold datasets
- dashboard/export consumers

## Control Plane

PostgreSQL DDL includes metadata tables for catalog records, schema drift history, contract validation, lineage runs, lineage jobs, lineage edges, column mappings, and downstream consumers.

## Sample Evidence

See [sample_lineage_graph.md](../sample_outputs/sample_lineage_graph.md).

## Interview Point

Lineage and metadata make the platform operable: teams can understand ownership, dependency risk, and downstream blast radius.
