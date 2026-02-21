from django.urls import path
from .views import ClassifyView, TicketDetailView, TicketListCreateView, TicketStatsView

urlpatterns = [
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list-create"),
    path("tickets/stats/", TicketStatsView.as_view(), name="ticket-stats"),
    path("tickets/classify/", ClassifyView.as_view(), name="ticket-classify"),
    path("tickets/<int:pk>/", TicketDetailView.as_view(), name="ticket-detail"),
]
