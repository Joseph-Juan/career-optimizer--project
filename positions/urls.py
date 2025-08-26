from django.urls import path

from .views import (
    PositionListView,
    PositionStep1View,
    PositionSkillsView,
    PositionReviewView,
    PositionDeleteView,
    PositionStatusView,
    create_tag,
    create_skill,
)

app_name = 'positions'

urlpatterns = [
    path('',                   PositionListView.as_view(),        name='list'),
    path('new/',               PositionStep1View.as_view(),       name='new'),
    path('<int:pk>/edit/',     PositionStep1View.as_view(),       name='edit'),
    path('<int:pk>/skills/',   PositionSkillsView.as_view(),      name='new_skills'),
    path('<int:pk>/review/',   PositionReviewView.as_view(),      name='new_review'),
    path('<int:pk>/delete/',   PositionDeleteView.as_view(),      name='delete'),
    path('<int:pk>/status/',   PositionStatusView.as_view(),      name='status'),
    path('tags/create/',       create_tag,                        name='create_tag'),
    path('skills/create/',     create_skill,                      name='create_skill'),
]
