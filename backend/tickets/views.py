from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from .models import Ticket
from .serializers import TicketSerializer
import os
import re
import json
import google.generativeai as genai


class TicketListCreateView(ListCreateAPIView):
    serializer_class = TicketSerializer

    def get_queryset(self):
        qs = Ticket.objects.all().order_by('-created_at')

        category = self.request.query_params.get('category')
        priority = self.request.query_params.get('priority')
        status = self.request.query_params.get('status')
        search = self.request.query_params.get('search')

        if category:
            qs = qs.filter(category=category)
        if priority:
            qs = qs.filter(priority=priority)
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        return qs


class TicketUpdateView(UpdateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


class TicketStats(APIView):
    def get(self, request):

        total = Ticket.objects.count()
        open_tickets = Ticket.objects.filter(status='open').count()

        avg = Ticket.objects.extra(
            select={'day': "date(created_at)"}
        ).values('day').annotate(c=Count('id')).aggregate(avg=Avg('c'))['avg']

        priority_breakdown = Ticket.objects.values('priority').annotate(count=Count('id'))
        category_breakdown = Ticket.objects.values('category').annotate(count=Count('id'))

        return Response({
            "total_tickets": total,
            "open_tickets": open_tickets,
            "avg_tickets_per_day": round(avg or 0, 2),
            "priority_breakdown": {x['priority']: x['count'] for x in priority_breakdown},
            "category_breakdown": {x['category']: x['count'] for x in category_breakdown},
        })


# 🔥 STRONGER PROMPT
CLASSIFY_PROMPT = """
You are a support ticket classification assistant.

Classify the ticket strictly into:

Category: billing, technical, account, general
Priority: low, medium, high, critical

Return ONLY valid JSON.
Do not include explanations.
Do not include markdown.
Do not include backticks.

Format:

{
  "category": "technical",
  "priority": "high"
}
"""


class TicketClassify(APIView):

    def post(self, request):
        description = request.data.get("description")

        if not description:
            return Response({"error": "description is required"}, status=400)

        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-2.5-flash")

            prompt = f"""
{CLASSIFY_PROMPT}

Ticket:
{description}
"""

            response = model.generate_content(prompt)

            result_text = response.text.strip()

            # 🔥 Extract JSON safely (handles markdown + extra text)
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)

            if not json_match:
                raise ValueError("No valid JSON found in LLM response")

            result = json.loads(json_match.group())

            return Response({
                "suggested_category": result.get("category"),
                "suggested_priority": result.get("priority")
            })

        except Exception as e:
            return Response({
                "suggested_category": None,
                "suggested_priority": None,
                "error": str(e)
            }, status=200)
