"""
URL configuration for Vacationjob project.

The urlpatterns list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from nass import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index,name='index'),
    path('login/',views.login1,name='login1'),
    path('register/',views.register_view,name='register_view'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('verify/', views.verify_dashboard, name='verify_dashboard'),
    path('userprofile/',views.profile_view, name='profile_view'),
    path('logout/',views.Logout, name='Logout'),
    
        path('bank-details/', views.bank_details, name='bank_details'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/withdraw/', views.user_Request_withdrawal, name='Request_withdrawal'),
    path('Jobs/', views.job_listings, name='JobList'),
    path('submit-task/<int:task_id>/', views.submit_task, name='submit_task'),
    path('track-task/<int:task_id>/', views.track_and_redirect, name='track_task'),
    path('admin-task-approval/', views.admin_task_approval, name='admin_task_approval'),
    path('admin-withdrawal-requests/', views.admin_withdrawal_requests, name='admin_withdrawal_requests'),
    
    path('languages/', views.languages_view, name='languages_view'),
    path('api/languages/', views.language_list, name='language_list'),
    path('support/', views.support, name='support'),
    path('Users_tree/', views.Users_tree, name='Users_tree'),
    path('view_map_api/', views.view_map_api, name='view_map_api'),
    path("save_hobbies/", views.save_hobbies, name="save_hobbies"),
    path("verify/<str:token>/", views.verify_email, name="verify_email"),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    path('forgot-password/', views.send_password_reset_email, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('user-management/', views.user_management, name='user_management'),
    path('verify-user/<int:user_id>/', views.verify_user, name='verify_user'),
    path('unverify-user/<int:user_id>/', views.unverify_user, name='unverify_user'),
    path('user-logins/', views.user_logins, name='user_logins'),
    path('impersonate-user/<int:user_id>/', views.impersonate_user, name='impersonate_user'),
    path('end-impersonation/', views.end_impersonation, name='end_impersonation'),

    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('tasks/edit/<int:pk>/', views.edit_task, name='edit_task'),


# new
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:pk>/edit/', views.edit_task, name='edit_task'),
    # path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/delete/', views.delete_task, name='delete_task'),

    # path('admin/tasks/', views.TaskListView.as_view(), name='admin_task_list'),
    # path('admin/tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='edit_task'),
    # path('admin/tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='delete_task'),
    # path('admin/tasks/<int:task_id>/submissions/', views.task_submissions, name='task_submissions'),
    
    # path('admin/withdrawals/', views.admin_withdrawal_requests, name='admin_withdrawal_requests'),
    # path('admin/withdrawals/process/', views.process_withdrawal, name='process_withdrawal'),
    path('filter-users/', views.filter_users, name='filter_users'),
    path('admin_dash/create-task/', views.create_task, name='create_task'),
    # path('jobs/', views.job_listings, name='job_listings'),
    # path('tasks/', views.task_listings, name='task_listings'),
    path('tasks/<int:task_id>/claim/', views.claim_task, name='claim_task'),
    path('tasks/<int:task_id>/submit/', views.submit_task, name='submit_task'),
    path('referral-tree/', views.referral_tree_view, name='referral_tree'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)