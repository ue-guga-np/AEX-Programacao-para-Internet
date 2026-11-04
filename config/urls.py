from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False), name="inicio"),
    path("admin/", admin.site.urls),
    path("", include("estoque.urls")),
]
