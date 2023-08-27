from django.urls import include, path

from . import views

app_name = 'account'
urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('', include('django.contrib.auth.urls')),
]
