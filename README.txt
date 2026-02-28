# 🎓 UniHelp — Assistant IA pour Services Universitaires

> **Hackathon Institut International de Technologie / NAU 2022** — Solution propulsée par Groq LLM + RAG

![UniHelp Banner](https://img.shields.io/badge/UniHelp-v2.0-blue?style=for-the-badge&logo=graduation-cap)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## 📋 Table des Matières

- [Problème](#-problème)
- [Solution](#-solution)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Stack Technique](#-stack-technique)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Sécurité](#-sécurité)
- [Structure du Projet](#-structure-du-projet)
- [Équipe](#-équipe)

---

## 🔴 Problème

Dans les universités tunisiennes, les étudiants posent chaque jour les **mêmes questions** :

- 📋 Comment obtenir une attestation de scolarité ?
- 💰 Comment postuler à une bourse ?
- 📅 Quelles sont les dates d'inscription ?
- 📝 Procédure de rattrapage d'examen ?

**Résultat :**
- Les secrétariats sont **surchargés** et peu disponibles
- Les réponses sont **incohérentes** selon l'interlocuteur
- Les étudiants perdent un **temps précieux** en démarches inutiles
- Les documents officiels sont **éparpillés** et difficiles à trouver

---

## ✅ Solution

**UniHelp** est un assistant IA universitaire qui :

1. **Centralise** les documents officiels (règlements, procédures, FAQ, notes internes)
2. **Répond instantanément** aux questions des étudiants via LLM + RAG
3. **Génère automatiquement** les emails et formulaires administratifs standardisés

> 💡 Les étudiants obtiennent des réponses précises 24h/24 basées sur les documents officiels de leur université.

---

## ✨ Fonctionnalités

### 👤 Espace Étudiant
| Fonctionnalité | Description |
|---|---|
| 💬 **Chat IA** | Questions/réponses en langage naturel (FR/AR/EN) |
| ⚡ **Streaming** | Réponses en temps réel token par token (comme ChatGPT) |
| 📚 **RAG** | Réponses basées sur les documents officiels indexés |
| 📜 **Historique** | Conversations sauvegardées par session |
| ✉️ **Email Generator** | Génération automatique d'emails administratifs |
| 🔐 **Auth JWT** | Connexion sécurisée avec token d'accès |

### ⚙️ Espace Administrateur
| Fonctionnalité | Description |
|---|---|
| 📤 **Upload PDF** | Import de documents officiels drag & drop |
| 🧩 **Indexation RAG** | Vectorisation automatique des documents |
| 🗂️ **Gestion docs** | Visualisation et suppression des documents |
| 🔒 **Accès restreint** | Routes protégées par rôle admin |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     UTILISATEUR                          │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────┐
│              FRONTEND (Next.js + Tailwind)               │
│   Landing  →  Login  →  Chat  →  Admin                  │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API + SSE Streaming
                       │ Authorization: Bearer JWT
┌──────────────────────▼──────────────────────────────────┐
│              BACKEND (FastAPI Python)                    │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Auth / JWT  │  │  Rate Limiter │  │ Input Validation│  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │                  RAG Engine                       │   │
│  │  PDF Upload → Chunking → Embedding → ChromaDB   │   │
│  │  Query → Semantic Search → Reranking → Context  │   │
│  └────────────────────┬────────────────────────────┘   │
│                       │                                  │
│  ┌────────────────────▼────────────────────────────┐   │
│  │              LLM (Groq API)                      │   │
│  │         Llama 3.3 70B Versatile                 │   │
│  │    Streaming · Context-aware · Multilingual     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  STOCKAGE LOCAL                          │
│         ChromaDB (vectors)  +  ./docs/ (PDFs)           │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Technique

### Backend
| Technologie | Usage |
|---|---|
| **FastAPI** | API REST + Server-Sent Events streaming |
| **Groq API** | LLM Llama 3.3 70B (ultra-rapide, gratuit) |
| **ChromaDB** | Base vectorielle pour le RAG |
| **Sentence Transformers** | Embeddings multilingues (FR/AR/EN) |
| **LangChain** | Chargement et découpage des PDFs |
| **PyJWT** | Authentification JSON Web Token |
| **Python 3.12** | Runtime |

### Frontend
| Technologie | Usage |
|---|---|
| **Next.js 16** | Framework React avec App Router |
| **Tailwind CSS** | Styling utility-first |
| **shadcn/ui** | Composants UI accessibles |
| **Lucide React** | Icônes |

---

## 🚀 Installation

### Prérequis
- Python 3.10+
- Node.js 18+
- Clé API Groq (gratuit sur [console.groq.com](https://console.groq.com))

### 1. Cloner le projet
```bash
git clone https://github.com/votre-username/unihelp.git
cd unihelp
```

### 2. Backend
```bash
cd backend

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et ajouter votre clé Groq

# Lancer le serveur
uvicorn main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend/unihelp

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

### 4. Accéder à l'application
| URL | Page |
|---|---|
| http://localhost:3000 | Landing page |
| http://localhost:3000/login | Connexion |
| http://localhost:3000/chat | Chat étudiant |
| http://localhost:3000/admin | Administration |
| http://127.0.0.1:8000/docs | Documentation API |

---

## 🔑 Utilisation

### Comptes de démonstration
| Rôle | Identifiant | Mot de passe |
|---|---|---|
| 🎓 Étudiant | `etudiant` | `iit2025` |
| ⚙️ Administrateur | `admin` | `admin2025` |

### Flux utilisateur
```
1. Landing page → "Commencer"
2. Login avec les identifiants
3. Chat : posez une question universitaire
4. Générez un email administratif (bouton "Email")
5. Admin : uploadez des PDFs pour enrichir la base
```

### Types d'emails générés
- 📋 Demande d'attestation de scolarité
- 🏢 Demande de stage PFE
- ⚖️ Réclamation de note
- 📅 Justification d'absence
- 🔄 Demande de transfert
- 💰 Demande de bourse

---

## 🔒 Sécurité

| Mesure | Détail |
|---|---|
| **JWT Auth** | Tokens 8h, signature HS256 |
| **Rate Limiting** | 20 req/min chat, 5 req/min login par IP |
| **Input Sanitization** | Suppression HTML, limite 1000 caractères |
| **Validation Pydantic** | Typage strict de tous les inputs |
| **CORS** | Restreint à localhost:3000 |
| **Upload sécurisé** | PDF only, max 20MB, nom sanitizé |
| **RBAC** | Routes admin protégées par rôle |

---

## 📁 Structure du Projet

```
unihelp/
├── backend/
│   ├── main.py          # API FastAPI + routes + auth + rate limiting
│   ├── llm.py           # Intégration Groq LLM + streaming
│   ├── rag.py           # RAG engine (indexation + retrieval + reranking)
│   ├── requirements.txt # Dépendances Python
│   ├── .env             # Variables d'environnement (non versionné)
│   ├── docs/            # PDFs uploadés
│   └── chroma_db/       # Base vectorielle persistante
│
└── frontend/unihelp/
    └── app/
        ├── page.tsx         # Landing page
        ├── login/page.tsx   # Authentification
        ├── chat/page.tsx    # Interface chat + email generator
        └── admin/page.tsx   # Dashboard administration
```

---

## 📊 Performance

| Métrique | Valeur |
|---|---|
| Temps de réponse LLM | ~0.5s (premier token) |
| Indexation PDF (10 pages) | ~3 secondes |
| Précision RAG | Basée sur cosine similarity < 0.7 |
| Modèle | Llama 3.3 70B Versatile |
| Langues supportées | Français, Arabe, Anglais |

---

## 📄 Licence

MIT License — Libre d'utilisation pour des fins éducatives.

---

<div align="center">
  <strong>UniHelp v2.0</strong> · Propulsé par Groq + RAG · IIT / NAU · 2025
  <br/>
  <em>Simplifier la vie universitaire grâce à l'intelligence artificielle</em>
</div>