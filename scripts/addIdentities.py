#-----Sets up the django environment-----#
import os 
import sys 
import django
sys.path.append(os.path.join(os.getcwd(), "")) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'identityApiSystem.settings') 
django.setup()

#---importing from models.py from the identity Api app fodder---#
from identityApiApp.models import *
from identityApiApp.serializers import *

#---creating/get a test user for the prototype-------------#
user, created = User.objects.get_or_create(username='testuser', email='testuser@example.com')
if created:
    user.set_password('password123')
    user.save()

dummy_identities_data = [
    {"user": user.id, 
     "identity_type": "Profession",
     "identity_name": "Prof George" 
    },
    {"user": user.id, 
     "identity_type": "Legal",
     "identity_name": "George William Washington" 
    },
    {"user": user.id, 
     "identity_type": "Social Media",
     "identity_name": "Professor fox 67" 
    },
]

#-----adding in the dummy identities-----#
for data in dummy_identities_data:
    serializer = identitySerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        print(f" The identity: {data['identity_type']} has been created/added!")

    else:
        print(serializer.errors)

#----checking that they have been added-----#
identities = Identity.objects.all()
for identity in identities:
    print(identity.identity_type + ": " + identity.identity_name)


