import subprocess
import time
import webbrowser

# =========================
# START FASTAPI
# =========================
api = subprocess.Popen([
    "uvicorn", "main:app", "--reload"
])

print("A iniciar FastAPI...")

# espera para o servidor subir
time.sleep(3)

# abre docs (opcional)
webbrowser.open("http://127.0.0.1:8000/docs")

# =========================
# START STREAMLIT
# =========================
print("A iniciar Streamlit...")

streamlit = subprocess.Popen([
    "streamlit", "run", "app_streamlit.py"
])

streamlit.wait()