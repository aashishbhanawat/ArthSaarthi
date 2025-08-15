import argparse

import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the backend server.")
    parser.add_argument(
        "--port", type=int, default=8000, help="The port to run the server on."
    )
    args = parser.parse_args()

    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, reload=False)
