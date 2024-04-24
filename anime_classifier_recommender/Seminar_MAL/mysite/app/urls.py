from django.urls import path
from app import views

app_name = 'app'

urlpatterns = [
    path('', views.home, name='home'),
    path('callback', views.generate_new_token, name='callback'),
    path('success', views.success, name='success'),
    path('refresh', views.refresh_token, name='refresh'),
    path('user_info', views.get_user_info, name='user_info'),
    path('anime_data', views.fetch_anime_data, name='anime_data'),
]
