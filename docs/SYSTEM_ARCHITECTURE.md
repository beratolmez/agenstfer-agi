# System Architecture

This document is the **authoritative single source of truth** for the overarching architecture of the **Agentic Growth Intelligence (AGI)** platform. It integrates the infrastructure boundaries, agentic business workflows, and technical stack.

---

## 1. Core Technology Stack

- **Backend API**: FastAPI (Python 3.12)
- **Agent Orchestration**: LangGraph (StateGraph state machines, checkpointing, human-in-the-loop approvals)
- **Agent Runtime & Structured Outputs**: Pydantic AI
- **Model Gateway (LLM Provider Abstraction)**: Provider-neutral gateway supporting Gemini API (Cloud) and Local/External GPU Inference Servers (Ubuntu Server GPU running Ollama, vLLM, LM Studio with models like GLM 5.2, Qwen 3.7 Max, etc.)
- **Vector Store / RAG**: ChromaDB (disposable vector embeddings derived from OKF 0.1 Markdown sources)
- **Operational Database**: PostgreSQL (users, roles, source locators, LangGraph state checkpoints, audit logs)
- **Frontend**: React UI (Vite, TypeScript, Tailwind CSS, Enterprise Minimal theme, `@xyflow/react` Visual Node Editor)
- **Observability & Tracing**: Self-hosted Langfuse telemetry tracing across LLMs, tools, and VPC boundaries

---

## 2. Infrastructure Architecture

The platform combines cloud control plane management (AWS) with containerized tool clusters, isolated local/cloud GPU model inference, and enterprise management modules.

```mermaid
flowchart TB
    subgraph Users["Users & External Clients"]
        U[Users]
    end

    subgraph AWS["AWS Infrastructure (Control Plane)"]
        GW[API Gateway]
        
        subgraph PrivateSubnet["Private Subnet"]
            BE[FastAPI Backend]
            RDS[(RDS PostgreSQL\nUsers, State & Audit)]
        end

        subgraph PublicSubnet["Public Subnet"]
            FE[React UI / EC2 Frontend]
        end

        subgraph Storage["Persistent Volumes"]
            V1[(Uploads)]
            V2[(Embeddings / ChromaDB)]
            V3[(Document Storage & Cache)]
        end
    end

    subgraph Cluster["Container Cluster (Kubernetes / ECS / EKS / Swarm)"]
        AG[AI Agent Containers]
        RAG[RAG Service]
        WF[Workflow Engine]
        SCH[Scheduler & Auth]
        
        subgraph PrivateTools["Private Tools (Internal Only)"]
            PT1[Internal Data Tool]
            PT2[Internal Scraping Tool]
        end
    end

    subgraph GPUServer["Local / External GPU Inference Server"]
        GPU[AI Model Provider / LLM]
        MODELS["Ollama / vLLM / LM Studio / Gemini API\n(GLM 5.2, Qwen 3.7 Max, Gemini, etc.)"]
    end

    subgraph Management["Enterprise Management Modules"]
        DASH[Dashboard]
        ERP[ERP Connectors]
        CRM[CRM Connectors]
        DOCS[Documents]
        REP[Reports]
        SOC[Social Media Insights]
        WEB[Website Snapshot]
    end

    subgraph Observability["Observability"]
        LANGFUSE[Langfuse Tracing Sink]
    end

    U --> GW
    GW --> FE
    GW --> BE
    BE --> RDS
    BE --> Storage
    BE --> Cluster
    Cluster --> PrivateTools
    Cluster --> GPU
    GPU --- MODELS
    BE --> Management
    BE -. Telemetry .-> LANGFUSE
    GPU -. Telemetry .-> LANGFUSE
```

---

## 3. Agentic Business System (KDS AI ABS) Workflow Architecture

The core intelligent processing is driven by the **KDS AI ABS** (Agentic Business System) orchestrator inside LangGraph. It processes untrusted business documents and data sources through specialized agent nodes to produce evidence-backed growth diagnostics.

```mermaid
flowchart TD
    subgraph Ingestion["Ingestion & Data Sources"]
        SRC["Şirket Dokümanları / Web / CRM / ERP"]
        ING["Read-Only Ingestion Adapters"]
        CHROMA["ChromaDB Vector Storage"]
    end

    subgraph KDS["KDS AI ABS (LangGraph Control Plane)"]
        ABS["KDS AI ABS Core Orchestrator"]
        STRAT["Stratejik Karar Dokümanları / Growth Diagnostic"]
        
        subgraph Nodes["Specialized Agent Nodes (Pydantic AI)"]
            N1["1. Şirketi Tanı (Company Analysis)"]
            N2["2. Potansiyel Müşteriler (Lead Profiling)"]
            N3["3. Rakipler Kimler (Competitor Intelligence)"]
            N4["4. Siber Güvenlik (Security Audit)"]
            N5["5. Finansal Modüller (Financial Analysis)"]
            N6["6. SEO & Sosyal Medya (SEO & Social Insights)"]
            N7["7. Müşteri Memnuniyeti (Satisfaction Analysis)"]
        end
    end

    subgraph Connectors["Read-Only Business System Adapters"]
        DB_CRM[(Veritabanı CRM)]
        ERP_SYS[(ERP System)]
        CALL_OUT[Outbound Call Interface]
        CALL_IN[Inbound Call Interface]
    end

    SRC --> ING --> CHROMA
    CHROMA --> ABS
    ABS --> Nodes
    Nodes --> STRAT
    N2 --> DB_CRM --> CALL_OUT & CALL_IN
    N5 --> ERP_SYS
```

### Agent Node Breakdown:
1. **Şirketi Tanı (Company Profiling)**: Analyzes internal documents, company history, and core capabilities.
2. **Potansiyel Müşteriler (Account Growth)**: Profiles potential growth leads and existing account expansion opportunities.
3. **Rakipler Kimler (Competitor Intelligence)**: Analyzes competitor locations, strategies, customer feedback, and weaknesses via authorized web scraping.
4. **Siber Güvenlik (Cybersecurity Audit)**: Assesses digital footprint security stance and vulnerability risks.
5. **Finansal Modüller (Financial Diagnostics)**: Performs deterministic financial ratio analysis and growth calculations.
6. **SEO & Sosyal Medya**: Analyzes search engine visibility, brand presence, and social media sentiment.
7. **Müşteri Memnuniyeti**: Evaluates customer feedback, support interaction data, and satisfaction metrics.

---

## 4. End-to-End Execution Sequence

### A. Data Ingestion Sequence

```mermaid
sequenceDiagram
    actor Admin as User / Admin
    participant UI as React UI
    participant API as FastAPI Backend
    participant RAG as RAG Service
    participant Chroma as ChromaDB Vector Store

    Admin->>UI: Triggers Ingestion / Setup
    UI->>API: POST /api/setup (Payload)
    API->>RAG: Parse Markdown & Extract Chunks
    RAG->>RAG: Generate Embeddings
    RAG->>Chroma: Insert Chunks & Metadata
    Chroma-->>RAG: Confirm Indexing
    RAG-->>API: Ingestion Complete
    API-->>UI: 200 OK (Setup Finished)
```

### B. Agent Chat & Human-in-the-Loop Approval Sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as FastAPI Backend
    participant Graph as LangGraph StateMachine
    participant Agent as Pydantic AI Agent
    participant Gateway as Model Gateway (Gemini / Local GPU)
    participant Chroma as ChromaDB
    participant Appr as Approval Center (PostgreSQL)

    User->>UI: Sends Query / Action Request
    UI->>API: POST /api/chat
    API->>Graph: Invoke LangGraph Workflow
    
    Graph->>Agent: Route to Researcher Node
    Agent->>Chroma: Query Evidence & Context
    Chroma-->>Agent: Return Context Chunks
    
    Graph->>Agent: Route to Analyst Node
    Agent->>Gateway: Request Inference (Pydantic AI Schema)
    Gateway-->>Agent: Structured Output Response
    
    alt Needs Approval
        Graph->>Appr: Interrupt Execution (interrupt_before)
        Appr-->>UI: Display Action Approval Toast / Notification
        User->>UI: Approves / Rejects Action
        UI->>API: POST /api/approval/{id}/resume
        API->>Graph: Resume Workflow State
    end
    
    Graph->>Agent: Route to Reviewer Node
    Agent->>Gateway: Verify Evidence & Citations
    Gateway-->>Agent: Claim Verification Result
    
    Graph-->>API: Return Final State & Response
    API-->>UI: Stream Output to User
```

---

## 5. Security & Boundary Principles

1. **Read-Only External Interactions (MVP)**: The platform performs read-only data ingestion and authorized web scraping. Autonomous external writes or messaging actions are prohibited without explicit human approval.
2. **Direct DB Isolation**: AI agent containers and model servers **never** connect directly to the database. All interactions must go through authorized FastAPI endpoints.
3. **Data Privacy Rules**: Confidential or restricted internal content is sanitized prior to sending to public cloud LLM endpoints.
4. **Self-Hosted Observability**: Telemetry (prompts, responses, latent traces) is routed strictly to the self-hosted Langfuse instance.
