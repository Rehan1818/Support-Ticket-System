from django.urls import path
from .views import *

urlpatterns = [
    path('tickets/classify/', TicketClassify.as_view()),   
    path('tickets/stats/', TicketStats.as_view()),         
    path('tickets/', TicketListCreateView.as_view()),
    path('tickets/<int:pk>/', TicketUpdateView.as_view()),
]

