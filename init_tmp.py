import os
import shutil
from pathlib import Path

def ensure_tmp_watchlist():
    """
    Copia watchlist.json para /tmp no Vercel se ainda não existir.
    Não faz nada localmente.
    """
    if not os.getenv("VERCEL"):
        print("💻 Ambiente local — sem necessidade de copiar para /tmp.")
        return

    src = Path(__file__).parent / "watchlist.json"
    dst = Path("/tmp/watchlist.json")

    try:
        if not src.exists():
            print(f"⚠️ Ficheiro de origem não encontrado: {src}")
            return

        if not dst.exists():
            shutil.copy(src, dst)
            print(f"📦 Copiado watchlist.json para {dst}")
        else:
            print("✅ /tmp/watchlist.json já existe, nada a fazer.")
    except Exception as e:
        print(f"❌ Erro ao copiar para /tmp: {e}")
