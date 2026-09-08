import os
import subprocess
import sys
import time


ROOT = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# SERVICES
# MCP Gateway is already running separately on port 9000.
# ============================================================

SERVICES = [
    {
        "name": "Flight Agent",
        "command": [
            sys.executable,
            "-m",
            "uvicorn",
            "agents.flight_agent.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
        ],
    },
    {
        "name": "Hotel Agent",
        "command": [
            sys.executable,
            "-m",
            "uvicorn",
            "agents.hotel_agent.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8002",
        ],
    },
    {
        "name": "Router Agent",
        "command": [
            sys.executable,
            "-m",
            "uvicorn",
            "agents.router_agent.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8003",
        ],
    },
    {
        "name": "Travel Gateway",
        "command": [
            sys.executable,
            "-m",
            "uvicorn",
            "gateway.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
    },
]


processes = []


# ============================================================
# START SERVICE
# ============================================================

def start_service(service):

    print(
        f"[STARTING] {service['name']}...",
        flush=True,
    )

    process = subprocess.Popen(
        service["command"],
        cwd=ROOT,
    )

    processes.append(
        (
            service["name"],
            process,
        )
    )

    time.sleep(2)

    if process.poll() is not None:

        print(
            f"[FAILED] {service['name']}",
            flush=True,
        )

        return False

    print(
        f"[RUNNING] {service['name']}",
        flush=True,
    )

    return True


# ============================================================
# STOP SERVICES
# ============================================================

def stop_services():

    print()
    print(
        "[STOPPING] All services...",
        flush=True,
    )

    for name, process in reversed(processes):

        if process.poll() is None:

            print(
                f"[STOPPING] {name}",
                flush=True,
            )

            try:
                process.terminate()
            except Exception:
                pass

    time.sleep(2)

    for name, process in reversed(processes):

        if process.poll() is None:

            try:
                process.kill()
            except Exception:
                pass

    print(
        "[STOPPED] All services.",
        flush=True,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("A2A TRAVEL - STARTING SERVICES")
    print("=" * 60)

    print()
    print(
        "[INFO] MCP Gateway is already running:"
    )

    print(
        "       http://127.0.0.1:9000/mcp"
    )

    print()

    try:

        # ----------------------------------------------------
        # Start all services
        # ----------------------------------------------------

        for service in SERVICES:

            if not start_service(service):

                print()
                print(
                    f"[ERROR] Could not start "
                    f"{service['name']}.",
                    flush=True,
                )

                stop_services()

                return

        # ----------------------------------------------------
        # Everything running
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("ALL SERVICES ARE RUNNING")
        print("=" * 60)

        print()
        print("MCP Gateway     : http://127.0.0.1:9000/mcp")
        print("Flight Agent    : http://127.0.0.1:8001")
        print("Hotel Agent     : http://127.0.0.1:8002")
        print("Router Agent    : http://127.0.0.1:8003")
        print("Travel Gateway  : http://127.0.0.1:8000")

        print()
        print("=" * 60)
        print("RUNNING")
        print("=" * 60)

        print()
        print("Press Ctrl+C to stop all services.")

        # ----------------------------------------------------
        # Keep run_all.py alive
        # ----------------------------------------------------

        while True:

            time.sleep(1)

            # Check if a service crashed.
            for name, process in processes:

                if process.poll() is not None:

                    print()
                    print(
                        f"[STOPPED] {name} "
                        f"(exit code: "
                        f"{process.returncode})",
                        flush=True,
                    )

    except KeyboardInterrupt:

        print()
        print(
            "[INFO] Ctrl+C received.",
            flush=True,
        )

    finally:

        stop_services()


if __name__ == "__main__":
    main()