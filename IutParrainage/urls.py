"""
URL configuration for IutParrainage project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url=None)),

    path('k9fx-gorgore-admin-iut/', admin.site.urls),
    
    path('', include('Parrainage.urls')),
    
]




from django.conf.urls import handler404, handler500, handler403, handler400
from django.shortcuts import render

# --- VUES D'ERREUR PERSONNALISÉES ---

def custom_page_not_found(request, exception):
    return render(request, 'errors/404.html', status=404)

def custom_server_error(request):
    return render(request, 'errors/500.html', status=500)

def custom_permission_denied(request, exception):
    return render(request, 'errors/403.html', status=403)

def custom_bad_request(request, exception):
    return render(request, 'errors/400.html', status=400)

# --- ASSIGNATION DES HANDLERS ---
handler404 = custom_page_not_found
handler500 = custom_server_error
handler403 = custom_permission_denied
handler400 = custom_bad_request




urlpatterns += staticfiles_urlpatterns()
