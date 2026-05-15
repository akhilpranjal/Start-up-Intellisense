import sys
import os


def main():
    """Simple CLI to run parts of the scaffold during development.

    Usage:
      python main.py api    # start FastAPI (uvicorn)
      python main.py ui     # start Streamlit UI
      python main.py worker # start RQ worker
    """
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "api":
        from app.api import start

        start()
    elif cmd == "ui":
        os.system("streamlit run ui/streamlit_app.py")
    elif cmd == "worker":
        from workers.worker import run_worker

        run_worker()
    else:
        print(main.__doc__)


if __name__ == "__main__":
    main()
