import click
import os
import sys
import subprocess
import signal

PID_FILE = "aiida_qe_app.pid"


@click.group()
def cli():
    """Command-line interface for managing the aiida_qe_app server."""
    pass


@cli.command()
@click.option("--port", default=8000, help="Port number to run the server on.")
def start(port):
    """Start the FastAPI server."""
    port = int(os.getenv("PORT", port))  # Use environment variable or default port

    # Start uvicorn in a subprocess
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "aiida_qe_app.backend.app.api:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--reload",
            "--log-level",
            "debug",
        ]
    )
    # Write the PID to a file
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))
    click.echo(f"Server started with PID {process.pid} on port {port}")


@cli.command()
def stop():
    """Stop the FastAPI server."""
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read())
        os.kill(pid, signal.SIGTERM)
        click.echo(f"Server with PID {pid} stopped")
        os.remove(PID_FILE)
    except FileNotFoundError:
        click.echo("PID file not found. Is the server running?")
    except ProcessLookupError:
        click.echo("Process not found. Is the server running?")
    except Exception as e:
        click.echo(f"Error stopping server: {e}")


@cli.command()
def status():
    """Check the status of the FastAPI server."""
    if os.path.isfile(PID_FILE):
        click.echo("Server is running.")
    else:
        click.echo("Server is not running.")


if __name__ == "__main__":
    cli()
