import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from app import create_app
    app = create_app()
    handler = app
except Exception:
    traceback.print_exc()
    raise

if __name__ == "__main__":
    app.run()
