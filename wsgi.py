#!/usr/bin/env python3
"""
WSGI entry point for EliWorks application deployment on Render.com
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app

# Configure for production
if __name__ == "__main__":
    # This will only run if the script is executed directly
    # In production, Gunicorn will import the 'app' object
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# This is what Gunicorn will look for
application = app

if __name__ != "__main__":
    # Production logging configuration
    import logging
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level) 