from django.urls import path

from hos_planner import views

urlpatterns = [
    path("plan-drive/", views.plan_drive, name="plan-drive"),
    path("search-location/", views.search_location, name="search-location"),
    path("reverse-location/", views.reverse_location_view, name="reverse-location"),
]
