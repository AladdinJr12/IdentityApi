#---Just a script for clearing all identities----#

#-----Sets up the django environment-----#
import os 
import sys 
import django
sys.path.append(os.path.join(os.getcwd(), "")) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'identityApiSystem.settings') 
django.setup()

#---importing from models.py from the identity Api app fodder---#
from identityApiApp.models import *

#---clearing the identities databse---#
Identity.objects.all().delete()

print("The database's tables' data entries have all been deleted!")

