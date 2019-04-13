"""facepro URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from uploads import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/',views.home,name='home'),
    path('delete/<int:id>/', views.delete_view, name='delete_view'),
    path('logout/',views.logout_view,name='logout'),
    path('results/',views.results_view,name='results'),
    path('uploads/recognition/',views.face_recognition_view,name='face_recognition'),
    path('uploads/classify/', views.face_recognition_classify,
         name='face_classify'),
    path('uploads/train/',views.train_view,name='train_view'),     
    path('uploads/simple/',views.simple_upload,name='simple_upload'),
    path('uploads/form/',views.model_form_upload,name='model_form_upload'),
    path('accounts/',include('accounts.urls')),
    path('', include('django.contrib.auth.urls'),name='login'),
]

if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL,
                              document_root=settings.MEDIA_ROOT)
        # urlpatterns += static(settings.STATIC_URL,
        #                       document_root=settings.STATIC_ROOT)
