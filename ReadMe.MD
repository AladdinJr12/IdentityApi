# Identity API System

## Overview
This project is a Django-based web application that allows users to manage multiple identities across different contexts and platforms.  
It also provides API-based identity retrieval using API keys and supports security levels with OTP verification.

## Features
- Identity management (create, edit, delete)
- Context-based identity retrieval
- API key-based identity access
- Security levels (Low / Medium / High)
- OTP verification system
- Custom client platform management

## For starting the prototype
1) Download the files or clone the repository
2) Activate/create your virtual environment
- As I use windows the commands for me were:
python -m venv myenv
myenv\Scripts\activate 

3) Install the files listed in requirements.txt with the command "pip install -r requirements.txt"
4) Cd to the folder "IdentityApi-main"
5) Start the project by running the command "python manage.py runserver 8080" 



## For running the unit tests:
1) Cd to the folder "IdentityApi-main"
2) use the command "python manage.py test"


## The only superuser/admin user created
Username: UserAdmin1
Password: Danganronpa


