import os
import subprocess
import sys
import time


ROOT = os.path.dirname(
    os.path.abspath(__file__)
)


SERVICES = [
    {
        "name": "MCP Gateway",
        "command": [
            sys.executable,
            "mcp_gateway/main.py",
        ],
    },
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


def main():

    processes = []

    try:

        for service in SERVICES:

            print(
                f"Starting {service['name']}..."
            )

            process = subprocess.Popen(
                service["command"],
                cwd=ROOT,
            )

            processes.append(process)

            time.sleep(2)

        print()
        print(
            "All services started."
        )

        print()
        print(
            "Travel Gateway:"
        )

        print(
            "http://127.0.0.1:8000"
        )

        print()
        print(
            "Press Ctrl+C to stop."
        )

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print(
            "Stopping services..."
        )

        for process in processes:

            process.terminate()

        for process in processes:

            process.wait()


if __name__ == "__main__":

    main()
