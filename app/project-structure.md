├── .env
├── agents
│   ├── embedder.py
│   ├── manager.py
│   ├── providers
│   │   ├── base.py
│   │   ├── gemini.py
│   │   ├── geminichat.py
│   │   ├── ollama.py
│   │   ├── openrouter.py
│   │   └── __pycache__
│   │       ├── base.cpython-311.pyc
│   │       ├── base.cpython-313.pyc
│   │       ├── gemini.cpython-311.pyc
│   │       ├── gemini.cpython-313.pyc
│   │       ├── geminichat.cpython-313.pyc
│   │       ├── ollama.cpython-311.pyc
│   │       ├── ollama.cpython-313.pyc
│   │       ├── openrouter.cpython-311.pyc
│   │       └── openrouter.cpython-313.pyc
│   ├── __init__.py
│   └── __pycache__
│       ├── embedder.cpython-311.pyc
│       ├── embedder.cpython-313.pyc
│       ├── manager.cpython-311.pyc
│       ├── manager.cpython-313.pyc
│       ├── __init__.cpython-311.pyc
│       └── __init__.cpython-313.pyc
├── api
│   ├── v1
│   │   ├── admins_route.py
│   │   ├── auth_route.py
│   │   ├── bd_route.py
│   │   ├── chat_route.py
│   │   ├── render_route.py
│   │   ├── routes.py
│   │   ├── translate_route.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │       ├── admins_route.cpython-313.pyc
│   │       ├── auth_route.cpython-313.pyc
│   │       ├── bd_route.cpython-313.pyc
│   │       ├── chat.cpython-313.pyc
│   │       ├── chat_route.cpython-313.pyc
│   │       ├── render_route.cpython-313.pyc
│   │       ├── routes.cpython-311.pyc
│   │       ├── routes.cpython-313.pyc
│   │       ├── translate_route.cpython-311.pyc
│   │       ├── translate_route.cpython-313.pyc
│   │       ├── __init__.cpython-311.pyc
│   │       └── __init__.cpython-313.pyc
│   ├── __init__.py
│   └── __pycache__
│       ├── __init__.cpython-311.pyc
│       └── __init__.cpython-313.pyc
├── base
│   ├── db.py
│   ├── indexes.py
│   └── __pycache__
│       ├── db.cpython-313.pyc
│       └── indexes.cpython-313.pyc
├── core
│   ├── config.py
│   ├── responses.py
│   ├── status_code.py
│   ├── __init__.py
│   └── __pycache__
│       ├── config.cpython-311.pyc
│       ├── config.cpython-313.pyc
│       ├── responses.cpython-311.pyc
│       ├── responses.cpython-313.pyc
│       ├── status_code.cpython-311.pyc
│       ├── status_code.cpython-313.pyc
│       ├── __init__.cpython-311.pyc
│       └── __init__.cpython-313.pyc
├── exceptions
│   ├── exceptions.py
│   ├── handlers.py
│   ├── __init__.py
│   └── __pycache__
│       ├── exceptions.cpython-311.pyc
│       ├── exceptions.cpython-313.pyc
│       ├── handlers.cpython-311.pyc
│       ├── handlers.cpython-313.pyc
│       ├── __init__.cpython-311.pyc
│       └── __init__.cpython-313.pyc
├── main.py
├── models
│   ├── admins.py
│   ├── chat.py
│   ├── console.py
│   ├── job.py
│   ├── login.py
│   ├── question.py
│   ├── survey.py
│   ├── text_input.py
│   ├── __init__.py
│   └── __pycache__
│       ├── admins.cpython-311.pyc
│       ├── admins.cpython-313.pyc
│       ├── chat.cpython-313.pyc
│       ├── console.cpython-311.pyc
│       ├── console.cpython-313.pyc
│       ├── job.cpython-313.pyc
│       ├── login.cpython-313.pyc
│       ├── question.cpython-311.pyc
│       ├── question.cpython-313.pyc
│       ├── survey.cpython-311.pyc
│       ├── survey.cpython-313.pyc
│       ├── text_input.cpython-311.pyc
│       ├── text_input.cpython-313.pyc
│       ├── __init__.cpython-311.pyc
│       └── __init__.cpython-313.pyc
├── prompt
│   ├── navigation_prompt.py
│   ├── prompt.py
│   ├── prompt_factory.py
│   ├── __init__.py
│   └── __pycache__
│       ├── navigation.cpython-313.pyc
│       ├── navigation_prompt.cpython-311.pyc
│       ├── navigation_prompt.cpython-313.pyc
│       ├── prompt.cpython-313.pyc
│       ├── prompt_factory.cpython-311.pyc
│       ├── prompt_factory.cpython-313.pyc
│       ├── __init__.cpython-311.pyc
│       └── __init__.cpython-313.pyc
├── services
│   ├── admin_service.py
│   ├── hive_service.py
│   ├── milvus_service.py
│   ├── renderer.py
│   ├── __init__.py
│   └── __pycache__
│       ├── admin_service.cpython-313.pyc
│       ├── hive_service.cpython-311.pyc
│       ├── hive_service.cpython-313.pyc
│       ├── milvus_service.cpython-311.pyc
│       ├── milvus_service.cpython-313.pyc
│       ├── renderer.cpython-313.pyc
│       ├── __init__.cpython-311.pyc
│       └── __init__.cpython-313.pyc
├── structure.md
├── test.py
├── tests
│   ├── conftest.py
│   ├── test_collections_crud.py
│   ├── test_conflicts_and_merge.py
│   └── __pycache__
│       └── conftest.cpython-313-pytest-8.3.2.pyc
├── utils
│   ├── json_params.py
│   ├── langue.py
│   ├── merge.py
│   ├── seq.py
│   ├── tokens.py
│   ├── utils.py
│   ├── __init__.py
│   └── __pycache__
│       ├── json_params.cpython-313.pyc
│       ├── langue.cpython-313.pyc
│       ├── merge.cpython-313.pyc
│       ├── seq.cpython-313.pyc
│       ├── tokens.cpython-313.pyc
│       ├── utils.cpython-311.pyc
│       ├── utils.cpython-313.pyc
│       ├── __init__.cpython-311.pyc
│       └── __init__.cpython-313.pyc
├── __init__.py
└── __pycache__
    ├── main.cpython-311.pyc
    ├── main.cpython-313.pyc
    ├── test.cpython-313.pyc
    ├── __init__.cpython-311.pyc
    └── __init__.cpython-313.pyc
