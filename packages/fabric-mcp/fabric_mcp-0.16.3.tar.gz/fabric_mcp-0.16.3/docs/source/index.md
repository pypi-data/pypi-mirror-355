# Fabric MCP Server Documentation Index

This index provides an overview of the original key documentation files for the Fabric MCP Server project,
which integrates Daniel Miessler's Fabric AI framework with the Model Context Protocol (MCP).

NOTE: These documents are here for archival purposes ONLY and should not be regarded
as the source of truth about the current state. Please refer to the other documentation

## Core Documentation Files

### [Product Requirements Document (PRD)](PRD.md)

**Purpose:** Defines the foundational requirements and scope for the Fabric MCP Server project.

**Key Contents:**

- Project goals and objectives
- Functional requirements for MVP (6 core MCP tools)
- Non-functional requirements (performance, security, reliability)
- User interaction and design goals
- Technical assumptions and constraints
- Epic breakdown with detailed user stories
- Testing requirements

**Target Audience:** Product managers, developers, stakeholders

---

### [Architecture Document](architecture.md)

**Purpose:** Provides the comprehensive technical blueprint for the Fabric MCP Server implementation.

**Key Contents:**

- High-level system overview and architectural patterns
- Component architecture and interactions
- Detailed project structure
- API specifications (both consumed and provided)
- Data models and schemas
- Core workflow sequence diagrams
- Technology stack decisions
- Error handling and security strategies
- Coding standards and testing approach

**Target Audience:** Software architects, developers, AI agents implementing the system

---

### [Developer Experience (DX) / Interaction Specification](design-architecture.md)

**Purpose:** Defines the user experience goals and interaction patterns for developers using the Fabric MCP Server.

**Key Contents:**

- Target user personas (MCP Client Developers, Server Operators, End Users)
- CLI command structure and design
- MCP tool organization and discoverability
- Detailed user flows for common scenarios
- Interaction patterns and conventions
- Language, tone, and terminology guidelines
- Accessibility requirements

**Target Audience:** UX designers, developers, technical writers

---

### [High-Level Design Document](design.md)

**Purpose:** Provides an initial design overview for integrating Fabric with MCP.

**Key Contents:**

- Background research on Fabric REST API and MCP
- Proposed MCP integration architecture
- Initial MCP tool definitions
- Implementation approach
- Benefits and next steps

**Target Audience:** Technical leads, developers new to the project

---

### [Epic Overview](epic-overview.md)

**Purpose:** Summarizes the high-level epics and user stories derived from the PRD, guiding the development phases and breaking down the work into actionable items.

This file is preserved here for historical purposes as the live document is in the
[epic-overview directory](../PRD/epic-overview/index.md)

**Key Contents:**

- Epic 1: Foundational Server Setup & Basic Operations
- Epic 2: Fabric Pattern Discovery & Introspection
- Epic 3: Core Fabric Pattern Execution with Strategy & Parameter Control
- Epic 4: Fabric Environment & Configuration Insights
- Detailed user stories and acceptance criteria for each epic.

**Target Audience:** Project managers, development team, stakeholders tracking progress

---

## Document Relationships

```mermaid
graph TD
    A[design.md\u003cbr/\u003eInitial Design] --\u003e B[PRD.md\u003cbr/\u003eRequirements]
    B --\u003e C[architecture.md\u003cbr/\u003eTechnical Blueprint]
    B --\u003e D[design-architecture.md\u003cbr/\u003eDX Specification]
    B --\u003e F[epic-overview.md\u003cbr/\u003eEpics & Stories]
    C --\u003e E[Implementation]
    D --\u003e E
    F --\u003e E
```

## Quick Reference

| Document | Focus Area | Key Decisions |
|----------|------------|---------------|
| PRD.md | What to build | 6 MCP tools, streaming support, 3 transport modes |
| architecture.md | How to build | Python 3.11+, FastMCP, httpx, monolithic service |
| design-architecture.md | User experience | CLI with click, MCP Inspector integration, clear error handling |
| design.md | Initial concept | REST API integration, no Fabric code changes |
| epic-overview.md  | Development Plan  | Breakdown of PRD into actionable epics and stories |

## Getting Started

1. **New to the project?** Start with [design.md](design.md) for context
2. **Understanding requirements?** Read the [PRD](PRD.md)
3. **Implementing features?** Refer to [architecture.md](architecture.md)
4. **Building CLI or tools?** Check [design-architecture.md](design-architecture.md)
5. **Planning development work?** Review [epic-overview.md](epic-overview.md)

## Version Information

All documents include change logs tracking their evolution. The current versions represent the MVP scope for the Fabric MCP Server, focusing on core pattern execution, discovery, and configuration capabilities through a standardized MCP interface.
