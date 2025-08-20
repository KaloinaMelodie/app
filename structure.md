your_project/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Point d'entrée FastAPI
│   ├── api/                     # Routes
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── routes.py
│   ├── models/                  # Schémas Pydantic et classes de données
│   │   ├── __init__.py
│   │   └── survey.py
│   ├── services/                # Logique métier (Milvus, Hive, Embedding)
│   │   ├── __init__.py
│   │   ├── milvus_service.py
│   │   ├── embedding_service.py
│   │   └── hive_service.py
│   ├── agents/                  # Abstractions ou wrappers AI/langchain
│   │   ├── __init__.py
│   │   └── ollama_embedder.py
│   ├── core/                    # Config, logging, constantes
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logger.py
│   ├── exceptions/              # Gestion des erreurs personnalisées
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── handlers.py
│   └── utils/                   # Utilitaires (conversion, format, etc.)
│       ├── __init__.py
│       └── parser.py
├── requirements.txt
└── run.py                       # Pour lancer le projet facilement
