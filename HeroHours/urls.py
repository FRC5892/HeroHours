import debug_toolbar
from django.contrib.auth.views import LoginView
from django.urls import path, include
from . import views
from .admin import add_user


urlpatterns = [
    path('', views.index, name='index'),
    path("insert/", views.handle_entry, name='in-out'),
    path("send_data_to_google_sheet/",views.send_data_to_google_sheet,name='send_data_to_google_sheet'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('__debug__/', include(debug_toolbar.urls)),
    path('custom/', add_user,name='custom'),
    path('logout/', views.logout_view, name='logout'),
]