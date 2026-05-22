import subprocess
import sys
import signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent


def kill_port(port: int):
    import time

    # fuser -k é mais confiável que lsof para liberar portas
    result = subprocess.run(
        ["fuser", "-k", f"{port}/tcp"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"  Porta {port} liberada.")
        time.sleep(0.5)  # aguarda OS liberar a porta


SERVICES = [
    {
        "name": "solutis-manager-back",
        "port": 8000,
        "cwd": BASE_DIR,
        "command": ["uv", "run", "uvicorn", "src.main:appAPI", "--reload", "--port", "8000"],
    },
    {
        "name": "solutis-procurement",
        "port": 8001,
        "cwd": ROOT_DIR / "solutis_procurement",
        "command": ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8001"],
    },
    {
        "name": "solutis-report",
        "port": 8002,
        "cwd": ROOT_DIR / "solutis_report",
        "command": ["uv", "run", "uvicorn", "main:appAPI", "--reload", "--port", "8002", "--app-dir", "src"],
    },
]

processes = []


def start_services():
    for service in SERVICES:
        print(f"Subindo {service['name']} (porta {service['port']})...")
        kill_port(service["port"])
        process = subprocess.Popen(service["command"], cwd=service["cwd"])
        processes.append(process)


def stop_services(*_):
    print("\nParando serviços...")
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    print("Todos os serviços foram parados.")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, stop_services)
    signal.signal(signal.SIGTERM, stop_services)

    start_services()

    print("\nTudo rodando com hot reload:")
    print("Manager Back: http://localhost:8000")
    print("Procurement:  http://localhost:8001")
    print("Report:       http://localhost:8002")
    print("\nPressione CTRL+C para parar tudo.\n")

    try:
        while True:
            signal.pause()
    except AttributeError:
        import time
        while True:
            time.sleep(1)
