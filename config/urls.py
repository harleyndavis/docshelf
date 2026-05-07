from django.urls import path, include

urlpatterns = [
    path("", include("markdown_viewer.urls")),
]
