import bjoern
from django_project.wsgi import application

# Define the host and port
host = '0.0.0.0'
port = 8011

# Start the Bjoern server
bjoern.run(application, host, port)

