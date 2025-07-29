from django.apps import apps
from django.contrib.auth import authenticate, login, logout, mixins
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST


def health_check(request):
    return HttpResponse('Service is running!')


class ListInstalledHuscyAppsView(mixins.LoginRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        app_names = [app.name
                     for app in apps.get_app_configs()
                     if hasattr(app, 'HuscyAppMeta')]
        return Response(sorted(app_names), status=HTTP_200_OK)


class LoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response({'error': 'Invalid credentials'}, status=HTTP_400_BAD_REQUEST)

        login(request, user)
        return Response({'message': 'Login successful'}, status=HTTP_200_OK)


class LogoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'message': 'Logout successful'}, status=HTTP_200_OK)
