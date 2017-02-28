#!/bin/bash
source ../env/bin/activate
echo "### Translating all messages..."
python manage.py makemessages -a --symlinks
echo "### Removing commented-out manual messages..."
find locale -name 'django.po' -exec sed s/^\#\~\ // -i {} \;
echo "### Compiling messages..."
python manage.py compilemessages
echo "### Done!"
