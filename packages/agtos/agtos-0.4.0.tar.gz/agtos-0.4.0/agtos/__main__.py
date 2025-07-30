"""Enable running agentctl as a module: python -m agtos"""
from .cli import app

if __name__ == "__main__":
    app()