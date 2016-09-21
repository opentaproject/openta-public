#!/bin/bash

echo "### Translating all messages..."
python manage.py makemessages -a
echo "### Removing commented-out manual messages..."
find locale -name 'django.po' -exec sed s/^\#\~\ // -i {} \;
echo "### Compiling messages..."
python manage.py compilemessages
echo "### Done!"
