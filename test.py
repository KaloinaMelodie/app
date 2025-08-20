import socket
from borneo import NoSQLHandleConfig, NoSQLHandle, ListTablesRequest

def test_connection(host, port):
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"✅ Connecté à {host}:{port}")
    except Exception as e:
        print(f"❌ Échec de connexion à {host}:{port} → {e}")

def test_oracle(authProvider):
    try:
        config = NoSQLHandleConfig("localhost:5000", authProvider)
        handle = NoSQLHandle(config)
        result = handle.list_tables(ListTablesRequest())
        print("✅ kvstore est UP — tables :", result.get_table_names())
    except Exception as e:
        print("❌ kvstore n'est pas actif ou erreur :", e)

