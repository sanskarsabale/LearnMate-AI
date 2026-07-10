"""
LearnMate AI — WSGI entry point for production servers.
Usage: gunicorn wsgi:application
"""
from app import app as application

if __name__ == "__main__":
    application.run()
