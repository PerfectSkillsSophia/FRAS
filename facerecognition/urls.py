from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('videofacerecog/', views.videofacerecog, name='videofacerecog'),
    path('upload_images/', views.upload_images, name='upload_images'),
    path('webcam_template/', views.webcam_template, name='webcam_template'),
    path('recognize_image/', views.recognize_image, name='recognize_image'),
    path('get_encodings/', views.get_encodings, name='get_encodings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)