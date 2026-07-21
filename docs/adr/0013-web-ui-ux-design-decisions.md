# 13. Web UI/UX Design Decisions

Date: 2026-07-21

## Status

Accepted

## Context

The web interface of the Agentic Growth Intelligence platform requires an overhaul to better suit its nature as a B2B AI orchestration platform. The UI must support managing complex workflows, real-time agent approvals, data ingestion visualization, and web scraping capabilities. We needed to establish a cohesive design language and decide on the key interactive components.

## Decisions

1. **Aesthetic Direction: Enterprise Minimal**
   - We adopt a clean, high-contrast, light-themed aesthetic focused on data tables and high performance.
   - We avoid overly stylized "dark mode" or "glassmorphism" in favor of a crisp, professional B2B look.

2. **Workflow Management: Visual Node Editor**
   - We continue utilizing and refining the React Flow (`@xyflow/react`) based visual drag-and-drop editor.
   - The editor will map agent chains and RAG flows like a visual map.
   - Chat-based workflow generation is noted as an experimental future addition but will not replace the visual editor.

3. **New MCP / Skill Panels**
   - **Web Scraping Panel:** A dedicated real-time monitoring view for agents performing web scraping and data gathering.
   - **Real-Time Approval Center:** The Approval Center will be upgraded with real-time push/toast notifications to allow instant decisions on critical agent actions.
   - **Advanced RAG Manager:** The data sources view will be enhanced to visually represent the chunking and embedding status of ingested documents.

## Consequences

- **Positive:** A cohesive, professional look that builds trust with enterprise users. The visual node editor simplifies complex agent orchestration. Real-time panels increase transparency of autonomous agent activities.
- **Negative:** Building custom real-time visualizers (like chunking progress or scraping logs) requires significant frontend development effort and tight integration with backend WebSocket or SSE streams.
