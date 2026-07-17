
# Agentic Growth Intelligence Platform

Version: MVP v1

---

# 1. Genel Amaç

Bu sistem;

- AI Agent çalıştırmak
- ERP
- CRM
- Dashboard
- Doküman Yönetimi
- Raporlama
- Sosyal Medya Yönetimi
- Web Sitesi

gibi servisleri tek platform altında toplar.

Sistem hem cloud hem de local GPU sunucusu kullanır.

---

# 2. Genel Mimari

    Users
                           │
                    API Gateway
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
     AWS Infrastructure                 Container Cluster
        │                                     │
        │                            AI Agents / Tools
        │                                     │
        └──────────────┬──────────────────────┘
                       │
                Local GPU Server
                       │
                 LLM Provider
                       │
            GLM 5.2 / Qwen / Other Models

---

# 3. Container Cluster

Container altyapısı;

Desteklenen ortamlar

- Kubernetes
- ECS
- Docker Swarm
- Cloudflare Workers
- EKS

amacıyla tasarlanmıştır.

Cluster içerisinde birçok bağımsız container çalışır.

Örnek servisler

- AI Agent
- RAG
- Workflow Engine
- Scheduler
- Notification Service
- Authentication
- Search
- API Services

Ayrıca Private Tools isimli ayrı bir container grubu bulunur.

Private Tools sadece internal erişim içindir.

---

# 4. AWS Infrastructure

AWS içerisinde aşağıdaki yapı bulunur.

AWS

    API Gateway

    VPC

    Private Subnet

    Backend

    RDS

    Public Subnet

    EC2 Frontend

    Persistent Volumes

    Volume 1
            Volume 2
            Volume 3

Görevleri

Backend

- API
- Authentication
- Business Logic

Frontend

- Web UI
- Dashboard UI

RDS

- ERP verileri
- CRM verileri
- kullanıcılar
- loglar
- metadata

Volumes

- uploads
- embeddings
- AI cache
- document storage

---

# 5. Local GPU Server

Ubuntu Server

AI Model Provider

Desteklenen servisler

- Ollama
- vLLM
- LM Studio

Bu servislerden biri çalışır.

LLM örnekleri

- GLM 5.2
- Qwen 3.7 Max

Bu sunucu sadece inference amacıyla kullanılır.

Container Cluster buraya istek gönderir.

---

# 6. Management Katmanı

Management modülü aşağıdaki servislerden oluşur.

Dashboard

ERP

CRM

Bu modüller Backend API üzerinden haberleşir.

AI servisleri gerektiğinde bu modüllere erişebilir.

---

# 7. Business Modules

Platform aşağıdaki modülleri içerir.

ERP

CRM

Documents

Reports

Social Media

Website

Tüm modüller ortak authentication kullanır.

---

# 8. Veri Akışı

User

↓

Frontend

↓

API Gateway

↓

Backend

↓

Business Modules

↓

Container Cluster

↓

LLM Server

↓

Response

---

# 9. AI Akışı

AI Agent

↓

Tool Selection

↓

Private Tool

↓

Backend API

↓

Database

↓

LLM

↓

Reasoning

↓

Result

---

# 10. Network Yapısı

Public

- Frontend
- API Gateway

Private

- Backend
- Database
- AI Containers
- Private Tools
- GPU Server

GPU Server mümkün olduğunca internetten izole tutulmalıdır.

---

# 11. Storage

Kalıcı veriler

- Documents
- Embeddings
- Vector Index
- User Uploads
- Logs
- Reports

AWS Volume üzerinde tutulur.

---

# 12. Güvenlik

Authentication

↓

Authorization

↓

Backend API

↓

Private Services

↓

Database

AI servisleri doğrudan database'e erişmez.

Tüm erişimler Backend API üzerinden yapılır.

---

# 13. Ölçeklenebilirlik

Yatay ölçeklenebilir servisler

- AI Containers
- Backend
- Frontend

Dikey ölçeklenebilir servis

- GPU Server

---

# 14. Gelecek Planları

- Multi Agent
- MCP Servers
- RAG Pipeline
- Vector Database
- Event Bus
- Queue System
- Monitoring
- Langfuse
- Observability
- Kubernetes Auto Scaling
