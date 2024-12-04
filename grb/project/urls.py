"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("addRecipe", views.addRecipe, name="addRecipe"),
    path("viewRecipe/<int:id>", views.viewRecipe, name="viewRecipe"),
    path("addRecipe/<int:prev_id>", views.addRecipe, name="editRecipe"),
    path("deleteRecipe/<int:id>", views.deleteRecipe, name="deleteRecipe"),
    path("browse", views.browseRecipe, name="browseRecipe"),
    path('', views.fetch_market_data, name='market_data'),
]
