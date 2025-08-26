# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Admin
    path('admin/login/',     views.admin_login_view,      name='admin_login'),
    path('admin/logout/',    views.admin_logout_view,     name='admin_logout'),
    path('admin/dashboard/', views.admin_dashboard,      name='admin_dashboard'),
    path('admin/matches/',   views.admin_view_matches,    name='admin_matches'),

    # Student auth
    path('register/', views.student_register_view, name='student_register'),
    path('login/',    views.student_login_view,    name='student_login'),
    path('logout/',   views.student_logout_view,   name='student_logout'),

    # Dashboard & CV (GET shows form; POST returns PDF OR saves)
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('cv/',        views.student_cv_view,    name='student_cv'),

    # Positions
    path('positions/',             views.browse_positions_view,   name='student_positions'),
    path('positions/toggle-save/', views.toggle_save_position,    name='toggle_save_position'),
    path('positions/<int:pk>/',    views.student_position_detail, name='student_position_detail'),
    path('saved/',                 views.saved_positions_view,    name='student_saved_positions'),

    # Skills
    path('skills/',           views.my_skills_view,       name='student_skills'),
    path('skills/add/',       views.add_skill_view,       name='add_skill'),
    path('skills/update/',    views.update_skill_view,    name='update_skill'),
    path('skills/delete/',    views.delete_skill_view,    name='delete_skill'),
    path('skills/bulk-save/', views.bulk_save_skills,     name='bulk_save_skills'),
]
