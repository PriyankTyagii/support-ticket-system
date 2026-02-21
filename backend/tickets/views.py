from django.db.models import Count, Avg, F, ExpressionWrapper, FloatField
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .llm import classify_ticket
from .models import Ticket
from .serializers import ClassifyRequestSerializer, TicketSerializer


class TicketListCreateView(ListCreateAPIView):
    """
    GET  /api/tickets/  — list all tickets (newest first), with optional filters.
    POST /api/tickets/  — create a new ticket, returns 201 on success.

    Supported query params: ?category=, ?priority=, ?status=, ?search=
    """

    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "priority", "status"]
    search_fields = ["title", "description"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Ticket.objects.all().order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TicketDetailView(RetrieveUpdateAPIView):
    """
    GET   /api/tickets/<id>/  — retrieve a single ticket.
    PATCH /api/tickets/<id>/  — partial update (status, category, priority, etc.).
    """

    serializer_class = TicketSerializer
    queryset = Ticket.objects.all()
    http_method_names = ["get", "patch", "head", "options"]

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class TicketStatsView(APIView):
    """
    GET /api/tickets/stats/
    Returns aggregated metrics computed entirely at the database level.
    """

    def get(self, request):
        qs = Ticket.objects.all()

        total_tickets = qs.count()
        open_tickets = qs.filter(status="open").count()

        # Average tickets per day — use DB-level aggregation
        daily_counts = (
            qs.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
        )
        if daily_counts.exists():
            total_days = daily_counts.count()
            total_for_avg = sum(d["count"] for d in daily_counts)
            avg_tickets_per_day = round(total_for_avg / total_days, 1)
        else:
            avg_tickets_per_day = 0.0

        priority_qs = (
            qs.values("priority")
            .annotate(count=Count("id"))
        )
        priority_breakdown = {p: 0 for p in ["low", "medium", "high", "critical"]}
        for row in priority_qs:
            priority_breakdown[row["priority"]] = row["count"]

        category_qs = (
            qs.values("category")
            .annotate(count=Count("id"))
        )
        category_breakdown = {c: 0 for c in ["billing", "technical", "account", "general"]}
        for row in category_qs:
            category_breakdown[row["category"]] = row["count"]

        return Response(
            {
                "total_tickets": total_tickets,
                "open_tickets": open_tickets,
                "avg_tickets_per_day": avg_tickets_per_day,
                "priority_breakdown": priority_breakdown,
                "category_breakdown": category_breakdown,
            }
        )


class ClassifyView(APIView):
    """
    POST /api/tickets/classify/
    Body: { "description": "..." }
    Returns: { "suggested_category": "...", "suggested_priority": "..." }
    """

    def post(self, request):
        serializer = ClassifyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        description = serializer.validated_data["description"]
        result = classify_ticket(description)
        return Response(result)
