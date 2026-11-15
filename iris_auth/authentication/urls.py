from django.urls import path
from authentication import views as auth_views  # Assuming your login view is in 'authentication/views.py'

urlpatterns = [
    path('', auth_views.home_view, name='home'),
    path('login/', auth_views.login_view, name='login'),
    path('signup/', auth_views.signup_view, name='signup'),
    path('dashboard/', auth_views.dashboard_view, name='dashboard'),
    path('logout/', auth_views.custom_logout, name='logout'),
    # other paths...
]