import os
import sys

# Add the virtual environment path and your project path to sys.path
sys.path.insert(0, '/home/neetudfk/Vacationjob')  # Path to your project directory
# sys.path.insert(0, '/home/neetudfk/virtualenv/Vacationjob/3.12/lib/python3.12/site-packages')  # Path to virtualenv packages

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'Vacationjob.settings'  # Replace 'Vacationjob' with your project name if necessary


# Import and set the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()