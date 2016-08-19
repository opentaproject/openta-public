from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def login_status(request):
    return Response({'username': request.user.get_username(), 'admin': request.user.is_staff})
