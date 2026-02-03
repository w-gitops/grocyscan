# Homebot Product Requirements Documentation

**Version:** 2.0  
**Date:** February 3, 2026  
**Status:** Active Development

---

## Overview

Homebot is a standalone home inventory management system with optional Grocy API compatibility. It provides intelligent barcode scanning, product tracking, meal planning, cost analysis, and document management for household inventory.

**Design Philosophy:** Tablet-first, mobile-optimized, desktop-compatible PWA. See [30.13 UI Specification](30.13-ui-specification.md) for responsive design, offline support, Core Web Vitals targets, and accessibility requirements.

## Johnny Decimal Organization

This documentation uses the [Johnny Decimal](https://johnnydecimal.com/) system. See [00.00 Johnny Decimal Standard](00.00-johnny-decimal-standard.md) for full details.

### Index

#### 00-09 System Management
| ID | Document | Status |
|----|----------|--------|
| 00.00 | [Johnny Decimal Standard](00.00-johnny-decimal-standard.md) | ✅ |

#### 10-19 Foundation
| ID | Document | Status |
|----|----------|--------|
| 10.10 | [Standards of Development](10.10-standards-of-development.md) | ✅ |
| 10.11 | [Executive Summary](10.11-executive-summary.md) | ✅ |
| 10.12 | [Delivery Plan](10.12-delivery-plan.md) | ✅ |

#### 20-29 Requirements
| ID | Document | Status |
|----|----------|--------|
| 20.10 | [User Stories](20.10-user-stories.md) | ✅ |
| 20.11 | [Functional Requirements](20.11-functional-requirements.md) | ✅ |

#### 30-39 Technical Design
| ID | Document | Status |
|----|----------|--------|
| 30.10 | [Technical Architecture](30.10-technical-architecture.md) | ✅ |
| 30.11 | [Data Models](30.11-data-models.md) | ✅ |
| 30.12 | [API Specification](30.12-api-specification.md) | ✅ |
| 30.13 | [UI Specification](30.13-ui-specification.md) | ✅ |

#### 40-49 Operations
| ID | Document | Status |
|----|----------|--------|
| 40.10 | [Installation & Operations](40.10-installation-operations.md) | ✅ |
| 40.11 | [Observability](40.11-observability.md) | ✅ |
| 40.12 | [Security](40.12-security.md) | ✅ |
| 40.13 | [Schema Evolution](40.13-schema-evolution.md) | ✅ |
| 40.14 | [Environment Variables](40.14-environment-variables.md) | ✅ |
| 40.15 | [Deployment](40.15-deployment.md) | ✅ |

#### 50-59 Quality
| ID | Document | Status |
|----|----------|--------|
| 50.10 | [Testing Strategy](50.10-testing-strategy.md) | ✅ |
| 50.11 | [Project Standards](50.11-project-standards.md) | ✅ |
| 50.12 | [Troubleshooting](50.12-troubleshooting.md) | ✅ |

#### 60-69 Core Features
| ID | Document | Status |
|----|----------|--------|
| 60.10 | [QR Routing System](60.10-qr-routing-system.md) | ✅ |
| 60.11 | [Multi-Tenant](60.11-multi-tenant.md) | ✅ |
| 60.12 | [Device Preferences](60.12-device-preferences.md) | ✅ |
| 60.13 | [Label Printing](60.13-label-printing.md) | ✅ |
| 60.14 | [Container Management](60.14-container-management.md) | ✅ |
| 60.15 | [LPN Instance Tracking](60.15-lpn-instance-tracking.md) | ✅ |

#### 70-79 Household Features
| ID | Document | Status |
|----|----------|--------|
| 70.10 | [People & Consumption](70.10-people-consumption.md) | ✅ |
| 70.11 | [Recipes & Meal Planning](70.11-recipes-meal-planning.md) | ✅ |
| 70.12 | [Shopping Lists](70.12-shopping-lists.md) | ✅ |
| 70.13 | [Food Intelligence](70.13-food-intelligence.md) | ✅ |
| 70.14 | [Cost Tracking](70.14-cost-tracking.md) | ✅ |
| 70.15 | [Paperless Integration](70.15-paperless-integration.md) | ✅ |
| 70.16 | [Return Tracking](70.16-return-tracking.md) | ✅ |
| 70.17 | [Integrations Settings](70.17-integrations-settings.md) | ✅ |

#### 80-89 Ralph Phases
| ID | Document | Status |
|----|----------|--------|
| 80.10 | [Ralph Phases Overview](80.10-ralph-phases-overview.md) | ✅ |
| 80.11 | [Phase 1: Foundation](80.11-ralph-phase-1-foundation.md) | ✅ |
| 80.12 | [Phase 2: Inventory](80.12-ralph-phase-2-inventory.md) | ✅ |
| 80.13 | [Phase 3: Device UI](80.13-ralph-phase-3-device-ui.md) | ✅ |
| 80.14 | [Phase 4: Labels & QR](80.14-ralph-phase-4-labels-qr.md) | ✅ |
| 80.15 | [Phase 5: Recipes](80.15-ralph-phase-5-recipes.md) | ✅ |
| 80.16 | [Phase 6: Intelligence](80.16-ralph-phase-6-intelligence.md) | ✅ |
| 80.17 | [Phase 7: Documents](80.17-ralph-phase-7-documents.md) | ✅ |

#### 90-99 Appendices
| ID | Document | Status |
|----|----------|--------|
| 91.10 | [API Documentation](91.10-api-documentation.md) | ✅ |
| 91.11 | [MCP Server](91.11-mcp-server.md) | ✅ |
| 91.12 | [User Documentation](91.12-user-documentation.md) | ✅ |
| 91.13 | [N8N Integration](91.13-n8n-integration.md) | ✅ |
| 91.14 | [Decision Log](91.14-decision-log.md) | ✅ |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0 |
| **Frontend (target)** | Vue.js 3, Quasar v2, Pinia, PWA |
| **Frontend (current)** | NiceGUI (interim, see [DEC-051](91.14-decision-log.md)) |
| **Database** | PostgreSQL 17 with RLS |
| **Cache/Queue** | Redis |
| **Observability** | OpenTelemetry, Prometheus, Loki, Grafana |
| **Documents** | Paperless-ngx, Gotenberg, Tika |
| **Deployment** | Docker Compose, systemd |

## Target Server

| Property | Value |
|----------|-------|
| **Host** | `192.168.200.37` |
| **SSH** | `root@192.168.200.37` |
| **Install Path** | `/opt/homebot/` |
| **Service** | `homebot` (systemd) |
| **API Port** | 3334 |

---

## Quick Start: Ralph Wiggum Execution

To begin building Homebot using Ralph Wiggum methodology:

1. **Copy Phase 1 task to RALPH_TASK.md:**
   ```bash
   # The RALPH_TASK.md in project root is the active task
   # It should contain Phase 1 criteria from prd/80.11-ralph-phase-1-foundation.md
   ```

2. **Start a fresh conversation** and say:
   > "Read RALPH_TASK.md and begin working on the unchecked criteria."

3. **After phase completes**, update RALPH_TASK.md with next phase

See [80.10 Ralph Phases Overview](80.10-ralph-phases-overview.md) for detailed execution guide.

---

## Document Status Summary

| Status | Count | Description |
|--------|-------|-------------|
| ✅ Complete | 46 | Fully updated for Homebot |
| **Total** | **46** | All documents ready |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0-1.3 | 2026-02-02 | Initial GrocyScan PRD |
| 2.0 | 2026-02-03 | Rebrand to Homebot, Johnny Decimal reorganization |

---

*This documentation represents the complete specification for Homebot.*
