import sys
import os

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from backend.app.rag.chain import run_rag
from backend.app.core.database import init_db

# Initialize DB (needed for some dependencies potentially, though run_rag is mostly logic)
# init_db() 

try:
    print("Testing query: 'hello'")
    response = run_rag(
        question="hello",
        chat_history=[]
    )
    print("Response:", response)
except Exception as e:
    print("Caught exception:")
    import traceback
    traceback.print_exc()
