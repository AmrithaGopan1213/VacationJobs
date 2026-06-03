from django.shortcuts import render, redirect, HttpResponse, get_object_or_404, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Register, BankDetails, Task, Wallet, TaskUserAssignment, WithdrawalRequest, UserSupport, UserReferral, Txn, EmailVerification, PasswordReset
from django.contrib.auth.decorators import login_required
from .forms import TaskSubmissionForm, TaskForm
from django.utils.timezone import now
from PIL import Image
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.conf import settings
from collections import deque
from django.views.decorators.csrf import csrf_exempt
import json, logging, requests, uuid
from django.core.mail import send_mail
import secrets, pycountry
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q

# Create your views here.
@never_cache
def index(request):
    return render(request, 'index.html')

@never_cache
def login1(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
            
        # Check if the user is an admin
        if user and user.is_superuser:
            login(request, user) 
            return redirect('admin_dashboard') 
        
        if user is not None:
            if user.register.is_verified:
                login(request, user) 
                return redirect('user_dashboard')
            else:
                return render(request, 'login.html', {'error': 'Not verified, please check email and verify'})
        else:
            # Handle invalid login
            return render(request, 'login.html', {'error': 'Invalid credentials'})
        
    return render(request, 'login.html')

def send_verification_email(email, token):
    subject = "Verify Your Email Address"
    message = f"Hi, please verify your email by clicking the link below:\n\n" \
              f"https://vacationjobs.in/verify/{token}/"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def verify_email(request, token):
    try:
        verification = EmailVerification.objects.get(token=token)
        
        # Check if expired
        if verification.is_expired():
            verification.delete()
            return render(request, 'verification_error.html', {
                'message': 'Verification link expired',
                'action': 'resend'
            })
        
        # Verify user
        user = verification.user
        if hasattr(user, 'register'):
            user.register.is_verified = True
            user.register.save()
        
        verification.delete()
        
        return render(request, 'verification_success.html')
        
    except EmailVerification.DoesNotExist:
        # Check if user might be already verified
        try:
            user_already_verified = User.objects.filter(
                register__is_verified=True
            ).exists()
            
            if user_already_verified:
                return render(request, 'verification_error.html', {
                    'message': 'Email already verified',
                    'action': 'login'
                })
        except:
            pass
            
        return render(request, 'verification_error.html', {
            'message': 'Invalid verification link',
            'action': 'resend'
        })

@never_cache
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        referral_code = request.POST.get('referal_link')
        
        # create root user if not
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(username='Nassonline', email='nassonlinetvm@gmail.com', password='123')
            user_referal = UserReferral.objects.create(user=admin_user, referral_link="ROOT")
            Wallet.objects.create(user=admin_user)

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return redirect('register_view')

        # Create user
        user = User.objects.create_user(username=username, password=password)
        person = Register.objects.create(
            user=user,
            first_name=first_name, 
            email=email, 
            phone=phone
        )

        parent = find_parent(referral_code)
        next_parent = check_parent(parent)
        assign_parent(user, next_parent)

        create_wallet(user)

        person.is_verified = False

        # Generate a token and save it
        token = secrets.token_urlsafe(16)
        EmailVerification.objects.create(user=user, token=token)

        # Send the verification email
        send_verification_email(email, token)

        person.save()
        messages.success(request, 'Registration successful!')
        return render(request, 'email_verify.html')
    
    return render(request, 'signup.html')

def find_parent(referral_code):
    if referral_code:
        parent = UserReferral.objects.filter(referral_link=referral_code).first()
        if parent:
            return parent
        else:
            raise ValueError("Invalid referral code")
    else:
        root_user = UserReferral.objects.first()  
        return root_user

def check_parent(parent):
    queue = deque([parent])
    while queue:
        current_user = queue.popleft()
        if current_user.children.count() < 5:
            return current_user
        for child in current_user.children.all():
            queue.append(child)
    return None

def assign_parent(user, parent):
    user_referral = UserReferral(user=user, parent=parent, referral_link=generate_referral_link(user))
    user_referral.save()

def generate_referral_link(user_id):
    return f"https://example.com/register?ref={uuid.uuid4().hex[:8]}"

def create_wallet(user):
    Wallet.objects.create(user=user)

def admin_dashboard(request):
    user = request.user
    users = User.objects.filter(is_superuser=False)
    assignments = TaskUserAssignment.objects.filter(user=user).select_related('task')
    wallet, created = Wallet.objects.get_or_create(user=user)
    withdraws = WithdrawalRequest.objects.all()
    return render(request, 'Admin.html', {'assignments': assignments, 'wallet': wallet, 'users': users, 'withdraws': withdraws})

def user_dashboard(request):
    try:
        person = Register.objects.get(user=request.user)
        # Get the user's referral link
        referral = UserReferral.objects.get(user=request.user)
    except:
        return HttpResponse("<script>window.alert('Problem with user');window.location.href=('/login/');</script>")
    return render(request, 'User.html', {'person': person, 'referral_link': referral.referral_link})

def verify_dashboard(request):
    return render(request, 'verificationteam.html')

def profile_view(request):
    try:
        person = Register.objects.get(user=request.user)
        # Get the user's referral information
        referral = UserReferral.objects.get(user=request.user)
    except Register.DoesNotExist:
        return HttpResponse("<script>window.alert('Problem with user');window.location.href=('/userprofile/');</script>")
    except UserReferral.DoesNotExist:
        # Handle case where referral doesn't exist (though it should if your system is working correctly)
        referral = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            person.first_name = request.POST['full_name']
            person.email = request.POST['email']
            person.phone = request.POST['phone']
            person.birth_date = request.POST['dob']
            person.gender = request.POST['gender']
            person.status = request.POST['status']
            person.qualification = request.POST['qualification']
            person.address = request.POST['address']
            person.pincode = request.POST['pin']
            person.country = request.POST['country']
            person.state = request.POST['state']
            person.city = request.POST['city']
            person.annual_income = request.POST['annual']
            person.about = request.POST['about']
            person.images = request.FILES.get('profile_photo')
            person.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_view')
        
        return render(request, 'Profile.html', {
            'Data': person,
            'referral_link': referral.referral_link if referral else None
        })
    else:
        hobbies_options = [
            "Reading",
            "Traveling",
            "Cooking",
            "Gardening",
            "Photography",
            "Painting",
            "Music",
            "Sports",
            "Dancing",
            "Writing"
        ]
        return render(request, 'Profile.html', {
            'Data': person,
            'hobbies_options': hobbies_options,
            'referral_link': referral.referral_link if referral else None
        })

def language_list(request):
    all_languages = cache.get('all_languages')
    if not all_languages:
        all_languages = [lang.name for lang in pycountry.languages if hasattr(lang, "name")]
        cache.set('all_languages', all_languages, timeout=60 * 60 * 24)  # Cache for 24 hours
    return JsonResponse({'all_languages': all_languages})

def languages_view(request):
    person = get_object_or_404(Register, user=request.user)

    if request.method == "POST":
        # Add a new language
        data = json.loads(request.body)
        language = data.get("language")
        proficiencies = data.get("proficiency")

        if not language or not proficiencies:
            return JsonResponse({"error": "Invalid input. Both language and proficiencies are required."}, status=400)

        languages = person.languages or []
        languages.append({"language": language, "proficiencies": proficiencies})
        person.languages = languages
        person.save()

        return JsonResponse({"message": "Language added successfully.", "languages": languages})

    elif request.method == "PUT":
        # Update an existing language
        data = json.loads(request.body)
        language = data.get("language")
        proficiencies = data.get("proficiency")
        index = data.get("index")  # The index of the language to update

        if not language or not proficiencies or index is None:
            return JsonResponse({"error": "Invalid input. Language, proficiencies, and index are required."}, status=400)

        languages = person.languages or []
        if index < 0 or index >= len(languages):
            return JsonResponse({"error": "Invalid index."}, status=400)

        languages[index] = {"language": language, "proficiencies": proficiencies}
        person.languages = languages
        person.save()

        return JsonResponse({"message": "Language updated successfully.", "languages": languages})

    elif request.method == "DELETE":
        # Delete a language
        data = json.loads(request.body)
        index = data.get("index") 

        if index is None:
            return JsonResponse({"error": "Index is required."}, status=400)

        languages = person.languages or []
        if index < 0 or index >= len(languages):
            return JsonResponse({"error": "Invalid index."}, status=400)

        languages.pop(index)
        person.languages = languages
        person.save()

        return JsonResponse({"message": "Language deleted successfully.", "languages": languages})

    elif request.method == "GET":
        # Fetch all languages
        return JsonResponse({"languages": person.languages or []})

    return JsonResponse({"error": "Invalid request method."}, status=405)

def Logout(request):
    logout(request)
    return HttpResponse("<script>window.alert('Log Out Success');window.location.href=('/login/');</script>")

@login_required
def bank_details(request):
    if request.method == 'POST':
        try:
            # Get form data
            account_holder = request.POST.get('accountHolder')
            account_number = request.POST.get('accountNumber')
            ifsc_code = request.POST.get('ifscCode')
            bank_name = request.POST.get('bankName')
            branch = request.POST.get('branch', '')

            # Validate required fields
            if not all([account_holder, account_number, ifsc_code, bank_name]):
                messages.error(request, 'Please fill all required fields!')
                return redirect('bank_details')

            # Save to database
            BankDetails.objects.update_or_create(
                user=request.user,
                defaults={
                    'account_holder': account_holder,
                    'account_number': account_number,
                    'ifsc_code': ifsc_code,
                    'bank_name': bank_name,
                    'branch': branch
                }
            )
            
            messages.success(request, 'Bank details saved successfully!')
            return redirect('bank_details')
            
        except Exception as e:
            messages.error(request, f'Error saving details: {str(e)}')
            return redirect('bank_details')
    
    # GET request - show form
    try:
        bank_details = BankDetails.objects.get(user=request.user)
    except BankDetails.DoesNotExist:
        bank_details = None
    
    return render(request, "bank_details.html", {
        "bank_details": bank_details,
        "messages": messages.get_messages(request)
    })

def dashboard(request):
    user = request.user
    assignments = TaskUserAssignment.objects.filter(user=user).select_related('task')
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Check if user has bank details
    has_bank_details = BankDetails.objects.filter(user=user).exists()
    
    return render(request, 'dashboard.html', {
        'assignments': assignments, 
        'wallet': wallet,
        'has_bank_details': has_bank_details
    })

@login_required
def user_Request_withdrawal(request):
    user = request.user
    
    # Check if user has bank details
    if not BankDetails.objects.filter(user=user).exists():
        messages.error(request, "Please fill your bank details before requesting withdrawal.")
        return redirect('bank_details')
    
    # Use transaction to ensure data consistency
    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(user=user)
        
        # Check if there are any pending withdrawals
        if WithdrawalRequest.objects.filter(user=user, status='Pending').exists():
            messages.error(request, "You already have a pending withdrawal request")
            return redirect('dashboard')
            
        # Check if wallet has sufficient balance
        if wallet.wallet_balance <= 0:
            messages.error(request, "Insufficient balance for withdrawal")
            return redirect('dashboard')
            
        bank = BankDetails.objects.get(user=user)
        amount = wallet.wallet_balance
        bank_details = f"A/C no: {bank.account_number} IFSC: {bank.ifsc_code}"
        
        # Create withdrawal request
        WithdrawalRequest.objects.create(
            user=user, 
            amount=amount, 
            bank_account=bank_details, 
            status='Pending'
        )
        
        # Reset wallet balance to zero
        wallet.wallet_balance = 0
        wallet.save()
    
    messages.success(request, "Withdrawal requested successfully")
    return redirect('dashboard')

def JobList(request):
    tasks = Task.objects.all()
    return render(request, 'joblist.html', {'tasks': tasks})

def validate_image(image):
    """Validate the uploaded image"""
    if image.size > 5 * 1024 * 1024:  # 5MB limit
        raise ValidationError("Image file too large ( > 5MB )")
    if not image.content_type.startswith('image/'):
        raise ValidationError("File is not an image")

@login_required
def submit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if task.is_expired:
        messages.error(request, "This task has expired and cannot be submitted.")
        return redirect('JobList')
    
    assignment, created = TaskUserAssignment.objects.get_or_create(
        task=task,
        user=request.user,
        defaults={'submission_status': 'pending'}
    )
    
    if assignment.submission_status == 'pending_review' or assignment.submission_status == 'approved':
        messages.warning(request, "You have already submitted this task.")
        return redirect('JobList')

    if request.method == 'POST':
        form = TaskSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Update the assignment with the submitted proof
                assignment.screenshot = form.cleaned_data['screenshot']
                assignment.proof_text = form.cleaned_data['proof_text']
                if 'proof_video' in request.FILES:
                    assignment.proof_video = request.FILES['proof_video']
                
                assignment.proof_submitted = True
                assignment.proof_submitted_at = timezone.now()
                assignment.submission_status = 'pending_review'
                assignment.save()
                
                messages.success(request, "Your work has been submitted for review.")
                return redirect('JobList')
            except Exception as e:
                messages.error(request, f"Error submitting task: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TaskSubmissionForm()

    return render(request, 'submit_task.html', {
        'form': form,
        'task': task,
        'timezone': timezone
    })

def track_and_redirect(request, task_id):
    assignment = TaskUserAssignment.objects.filter(task_id=task_id, user=request.user).first()
    if assignment:
        assignment.clicked_at = now()
        assignment.save()
    target_url = request.GET.get('url', 'https://www.example.com') 
    return redirect(target_url)

def filter_users(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Get filter parameters with defaults
            filters = {
                'user__is_active': True,  # Only active users
            }
            
            if country := data.get('country'):
                filters['country__icontains'] = country
            if state := data.get('state'):
                filters['state__icontains'] = state
            if language := data.get('language'):
                filters['languages__icontains'] = language
            if gender := data.get('gender'):
                filters['gender__iexact'] = gender
            if status := data.get('status'):
                filters['status__iexact'] = status
            if qualification := data.get('qualification'):
                filters['qualification__icontains'] = qualification
            
            users = Register.objects.filter(**filters).select_related('user')
            
            users_data = [{
                'id': user.user.id,
                'name': user.user.get_full_name() or user.user.username,
                'email': user.user.email,
                'country': user.country,
                'state': user.state,
                'language': user.languages,
                'gender': user.gender,
                'status': user.status,
                'qualification': user.qualification
            } for user in users]
            
            return JsonResponse({'users': users_data, 'count': len(users_data)})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def job_listings(request):
    # Get all TaskUserAssignment records for current user with related task data
    assignments = TaskUserAssignment.objects.filter(
        user=request.user
    ).select_related('task').order_by('-task__created_at')
    
    # Pagination
    paginator = Paginator(assignments, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'joblist.html', {
        'page_obj': page_obj,
        'assignments': page_obj.object_list,
        'timezone': timezone
    })

@login_required
def claim_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        assignment = TaskUserAssignment.objects.get(
            task=task,
            user=request.user,
            submission_status='pending'
        )
        
        # Check if deadline has passed
        if timezone.now() > task.deadline:
            return JsonResponse({
                'success': False,
                'error': 'This task has expired and can no longer be claimed.'
            }, status=400)
            
        # Check if task has reached workers limit
        if task.workers_limit:
            claimed_count = TaskUserAssignment.objects.filter(
                task=task, 
                submission_status='in_progress'
            ).count()
            if claimed_count >= task.workers_limit:
                return JsonResponse({
                    'success': False,
                    'error': 'This task has reached its maximum workers limit.'
                }, status=400)
        
        # Claim the task
        assignment.submission_status = 'in_progress'
        assignment.clicked_at = timezone.now()
        assignment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Task claimed successfully!'
        })
        
    except Task.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Task not found.'
        }, status=404)
    except TaskUserAssignment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Task assignment not found or already claimed.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            
            # Get selected user IDs from the form
            selected_user_ids = request.POST.getlist('users_assigned')
            
            # Create TaskUserAssignment records
            for user_id in selected_user_ids:
                user = User.objects.get(id=user_id)
                TaskUserAssignment.objects.create(
                    task=task,
                    user=user,
                    submission_status='pending'
                )
            
            messages.success(request, "Task created and assigned successfully!")
            return redirect('admin_dashboard')
        
        else:
            messages.error(request, "There was an error creating the task. Please check the form.")

    else:
        form = TaskForm()
    
    return render(request, 'create_task.html', {'form': form})

# ... (rest of your views remain the same, including distribute_commission, admin_task_approval, etc.)

# The rest of your views.py file remains unchanged...
    

# def distribute_commission(task, user):
#     commission_per_task = task.commission_per_task
#     commission_distribution = [20, 15, 10, 6, 4, 2, 1.5, 1.5]

#     # Distribute to the hierarchy
#     current_user = user
#     for percentage in commission_distribution:
#         if not current_user:
#             break
        
#         # Get or create wallet for the user
#         wallet, created = Wallet.objects.get_or_create(user=current_user)
        
#         share = (commission_per_task * percentage) / 100
#         wallet.add_balance(share)

#         # Log the txn
#         Txn.objects.create(
#             user=current_user,
#             task=task,
#             amount=share,
#             description=f"{percentage}% commission for completing {task.title}"
#         )

#         if current_user.username == 'admin' and current_user.id == 1:
#             break
            
#         # Move to the parent user
#         try:
#             parent_user = current_user.userreferral.parent.user
#             current_user = parent_user
#         except (UserReferral.DoesNotExist, AttributeError):
#             break



from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

def distribute_commission(task, user):
    """
    Distributes commission to user and their referral hierarchy using:
    [20%, 15%, 10%, 6%, 4%, 2%, 1.5%, 1.5%]
    """
    try:
        with transaction.atomic():
            # Get the assignment with lock - updated status to 'pending_review'
            try:
                assignment = TaskUserAssignment.objects.select_for_update().get(
                    task=task,
                    user=user,
                    submission_status='pending_review'  # Changed from 'in_progress'
                )
            except ObjectDoesNotExist:
                return False, "No valid task assignment found for commission distribution"

            if assignment.commission_distributed:
                return False, "Commission already distributed"

            if not task.commission_per_task or task.commission_per_task <= Decimal('0'):
                return False, "Invalid commission amount"
            
            commission_distribution = [20, 15, 10, 6, 4, 2, 1.5, 1.5]
            current_user = user
            total_distributed = Decimal('0')
            distribution_log = []

            for percentage in commission_distribution:
                if not current_user:
                    break

                # Calculate share with proper decimal handling
                share = (task.commission_per_task * Decimal(percentage)) / Decimal(100)
                share = share.quantize(Decimal('0.00'))
                total_distributed += share

                # Get or create wallet with lock
                wallet, created = Wallet.objects.select_for_update().get_or_create(
                    user=current_user,
                    defaults={'wallet_balance': Decimal('0.00')}
                )
                
                # Update wallet balance
                wallet.wallet_balance += share
                wallet.save()
                
                # Record transaction
                Txn.objects.create(
                    user=current_user,
                    task=task,
                    amount=share,
                    description=f"{percentage}% commission for {task.title}"
                )

                distribution_log.append({
                    'user': current_user.username,
                    'user_id': current_user.id,
                    'percentage': percentage,
                    'amount': float(share),
                    'wallet_balance': float(wallet.wallet_balance)
                })

                # Move up the referral chain
                try:
                    referral = UserReferral.objects.get(user=current_user)
                    if referral.parent:
                        current_user = referral.parent.user
                    else:
                        break  # No more parents in the chain
                except UserReferral.DoesNotExist:
                    break  # User has no referral entry

            # Handle any remaining amount due to rounding
            remaining = task.commission_per_task - total_distributed
            if remaining > Decimal('0.00'):
                admin = User.objects.filter(is_superuser=True).order_by('id').first()
                if admin:
                    wallet, _ = Wallet.objects.select_for_update().get_or_create(
                        user=admin,
                        defaults={'wallet_balance': Decimal('0.00')}
                    )
                    wallet.wallet_balance += remaining
                    wallet.save()
                    
                    Txn.objects.create(
                        user=admin,
                        task=task,
                        amount=remaining,
                        description=f"Remaining commission for {task.title}"
                    )
                    
                    distribution_log.append({
                        'user': admin.username,
                        'user_id': admin.id,
                        'percentage': float((remaining/task.commission_per_task)*100),
                        'amount': float(remaining),
                        'wallet_balance': float(wallet.wallet_balance)
                    })

            # Update assignment status
            assignment.commission_distributed = True
            assignment.commission_amount = task.commission_per_task
            assignment.commission_distributed_at = timezone.now()
            assignment.submission_status = 'paid'  # Changed to 'paid' from 'approved'
            assignment.commission_distribution_log = distribution_log
            assignment.save()

            return True, {
                'message': "Commission distributed successfully",
                'total': float(total_distributed),
                'distribution': distribution_log
            }

    except Exception as e:
        return False, f"Commission distribution failed: {str(e)}"

# views.py - Update admin_task_approval view
@login_required
def admin_task_approval(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        action = request.POST.get('action')
        
        try:
            assignment = get_object_or_404(TaskUserAssignment, id=task_id)
            
            if action == "approve":
                if assignment.submission_status == 'pending_review':
                    # Distribute commission
                    success, result = distribute_commission(assignment.task, assignment.user)
                    
                    if success:
                        assignment.submission_status = 'approved'
                        assignment.save()
                        messages.success(request, "Task approved! Commission distributed.")
                    else:
                        messages.error(request, f"Commission error: {result}")
                else:
                    messages.error(request, "Task cannot be approved in its current state")
            
            elif action == "reject":
                if assignment.submission_status == 'pending_review':
                    assignment.submission_status = 'rejected'
                    assignment.save()
                    messages.success(request, "Task rejected")
                else:
                    messages.error(request, "Task cannot be rejected in its current state")
            
            return redirect('admin_task_approval')
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('admin_task_approval')

    # Show tasks that are pending review
    tasks = TaskUserAssignment.objects.filter(
        submission_status='pending_review'
    ).select_related('task', 'user')
    
    return render(request, 'admin_task_approval.html', {
        'tasks': tasks
    })





def create_wallet(user):
    wallet, created = Wallet.objects.get_or_create(user=user)
    return wallet

# def admin_task_approval(request):
#     if request.method == 'POST':
#         task_id = request.POST.get('task_id')
#         usertask = get_object_or_404(TaskUserAssignment, id=task_id)
#         action = request.POST.get('action')
        
#         if action == "approve" and usertask.submission_status != 'Approved':
#             # Ensure user has a wallet before distributing commission
#             Wallet.objects.get_or_create(user=usertask.user)
#             distribute_commission(usertask.task, usertask.user)
#             usertask.submission_status = 'Approved'
#         elif action == "reject":
#             usertask.submission_status = 'Rejected'

#         usertask.save()
#         return redirect('admin_task_approval')

#     tasks = TaskUserAssignment.objects.filter(proof_submitted=True)
#     return render(request, 'admin_task_approval.html', {'tasks': tasks})

# def admin_withdrawal_requests(request):
#     if request.method == 'POST':
#         request_id = request.POST.get('request_id')
#         action = request.POST.get('action')
#         withdrawal_request = get_object_or_404(WithdrawalRequest, id=request_id)

#         if action == 'approve':
#             approve_withdrawal(request_id)
#         elif action == 'reject':
#             withdrawal_request.status = 'Rejected'
#             withdrawal_request.error_message = 'Rejected by Admin'

#         withdrawal_request.save()
#         return redirect('admin_withdrawal_requests')

#     requests = WithdrawalRequest.objects.filter(status='Pending')
#     return render(request, 'admin_withdrawal_requests.html', {'requests': requests})

# logger = logging.getLogger(_name_)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import WithdrawalRequest
import logging
import time

logger = logging.getLogger(__name__)

@login_required
def admin_withdrawal_requests(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        
        if not request_id or not action:
            messages.error(request, "Invalid request parameters")
            return redirect('admin_withdrawal_requests')
        
        try:
            withdrawal_request = WithdrawalRequest.objects.get(id=request_id)
            
            if action == 'approve':
                # Process payment (add your payment logic here)
                payment_reference = f"PAY-{int(time.time())}-{withdrawal_request.id}"
                
                # Update the request
                withdrawal_request.status = 'Approved'
                withdrawal_request.payment_reference = payment_reference
                withdrawal_request.error_message = ''
                withdrawal_request.save()
                
                messages.success(request, f"Successfully approved withdrawal #{withdrawal_request.id}")
                logger.info(f"Approved withdrawal {withdrawal_request.id}")
                
            elif action == 'reject':
                withdrawal_request.status = 'Rejected'
                withdrawal_request.error_message = request.POST.get('rejection_reason', 'Rejected by admin')
                withdrawal_request.save()
                messages.warning(request, f"Rejected withdrawal #{withdrawal_request.id}")
                
            return redirect('admin_withdrawal_requests')
            
        except WithdrawalRequest.DoesNotExist:
            messages.error(request, "Withdrawal request not found")
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")
            logger.error(f"Error processing withdrawal: {str(e)}")
    
    # GET request - show pending withdrawals
    requests = WithdrawalRequest.objects.filter(status='Pending').order_by('-requested_at')
    return render(request, 'admin_withdrawal_requests.html', {
        'requests': requests
    })



def approve_withdrawal(request):
    if request.method == 'POST':
        withdrawal_id = request.POST.get('request_id')
        action = request.POST.get('action')
        
        withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
        
        if action == 'approve':
            # Handle approval
            wallet, created = Wallet.objects.get_or_create(user=withdrawal.user)
            
            if withdrawal.status == 'Pending':
                try:
                    payout_response = process_payout(withdrawal.user, withdrawal.amount)
                    
                    if payout_response.get('success'):
                        withdrawal.status = 'Approved'
                        withdrawal.payment_reference = payout_response.get('transaction_id')
                        withdrawal.processed_at = now()
                        wallet.paid_amount += withdrawal.amount
                        wallet.wallet_balance -= withdrawal.amount
                        wallet.save()
                        messages.success(request, f"Withdrawal #{withdrawal_id} approved successfully!")
                    else:
                        withdrawal.status = 'Rejected'
                        withdrawal.error_message = payout_response.get('error', 'Unknown error occurred.')
                        messages.error(request, f"Payout failed: {withdrawal.error_message}")
                except Exception as e:
                    withdrawal.status = 'Rejected'
                    withdrawal.error_message = str(e)
                    messages.error(request, f"Error processing withdrawal: {str(e)}")
                
                withdrawal.save()
        
        elif action == 'reject':
            # Handle rejection
            if withdrawal.status == 'Pending':
                withdrawal.status = 'Rejected'
                withdrawal.error_message = request.POST.get('rejection_reason', 'Rejected by admin')
                withdrawal.processed_at = now()
                withdrawal.save()
                messages.success(request, f"Withdrawal #{withdrawal_id} rejected.")
    
    return redirect('admin_withdrawal_requests')

def process_payout(user, amount):
    try:
        # Get user's bank details
        bank = BankDetails.objects.get(user=user)
        
        # Prepare payout data
        payout_data = {
            "account_number": bank.account_number,  # Your business account number
            "fund_account": {
                "account_type": "bank_account",
                "bank_account": {
                    "name": bank.user.username,
                    "ifsc": bank.ifsc_code,
                    "account_number": bank.account_number,
                }
            },
            "amount": int(1 * 100),  # Amount in paise
            "currency": "INR",
            "mode": "IMPS",  # Options: IMPS, NEFT, RTGS, UPI
            "purpose": "refund",
            "queue_if_low_balance": True,
            "reference_id": f"withdrawal_{user.id}",
            "narration": "Payout for task completion"
        }

        # Razorpay API endpoint for payouts
        payout_url = "https://api.razorpay.com/v1/payouts"

        # Use Razorpay API keys for authentication
        auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        
        # Make the API request
        response = requests.post(payout_url, json=payout_data, auth=auth)
        response_data = response.json()
        
        if response.status_code == 200 or response.status_code == 201:
            return {"success": True, "transaction_id": response_data.get('id')}
        else:
            return {"success": False, "error": response_data.get('error', {}).get('description', 'Unknown error')}
    
    except BankDetails.DoesNotExist:
        return {"success": False, "error": "User bank details not found."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}


def support(request):
    if request.method == 'POST':
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')
        UserSupport.objects.create(
            user=request.user,
            category='review',
            subject=f"Review Rating: {rating}",
            description=review_text
        )
        return redirect('support')
    reviews = UserSupport.objects.filter(category='review').order_by('-created_at')  # Fetch reviews sorted by latest
    return render(request, 'support.html', {'reviews': reviews})

def get_user_hierarchy(user_id=None):
    if user_id is None:
        root_users = UserReferral.objects.filter(parent_id=1) 
    else:
        root_users = UserReferral.objects.filter(parent_id=user_id)

    hierarchy = []
    for user in root_users:
        children = get_user_hierarchy(user.id)
        hierarchy.append({
            "name": user.user.username,  
            "children": children
        })
    return hierarchy

def view_map_api(request):
    hierarchy = get_user_hierarchy()
    return JsonResponse({"name": "Admin", "children": hierarchy})

def Users_tree(request):
    return render(request,'users_tree.html')

def save_hobbies(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Parse JSON data
            selected_hobbies = data.get("hobbies", [])

            if len(selected_hobbies) > 3:
                return JsonResponse({"success": False, "error": "You can select up to 3 hobbies only."}, status=400)

            # Save hobbies to the database (assuming user model has hobbies field)
            request.user.register.hobby = ",".join(selected_hobbies)  # Convert list to comma-separated string
            request.user.register.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)

def resend_verification_email(request):
    if request.method == "POST":
        email = request.POST.get('email')

        # Check if user exists
        user = get_object_or_404(Register, email=email)

        # Check if already verified
        if user.is_verified:
            return JsonResponse({'message': 'User is already verified'}, status=400)

        # Get or create a new verification token
        verification, created = EmailVerification.objects.get_or_create(user=user.user)

        # If existing token is expired, generate a new one
        if not created and verification.is_expired():
            verification.token = secrets.token_urlsafe(16)
            verification.created_at = now()
            verification.save()

        # Resend the email
        send_verification_email(user.email, verification.token)

        return JsonResponse({'message': 'Verification email has been resent!'})

def send_password_reset_email(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = get_object_or_404(Register, email=email)

        # Generate or reuse existing token
        reset_request, created = PasswordReset.objects.get_or_create(user=user.user)
        if not created and reset_request.is_expired():
            reset_request.token = secrets.token_urlsafe(16)
            reset_request.created_at = now()
            reset_request.save()

        # Send reset link
        reset_link = f"https://vacationjobs.in/reset-password/{reset_request.token}/"
        send_mail(
            "Reset Your Password",
            f"Click here to reset your password: {reset_link}",
            settings.EMAIL_HOST_USER,
            [email]
        )

        messages.success(request, "Password reset link has been sent to your email.")
    return render(request, 'forgot_password.html')

def reset_password(request, token):
    reset_request = get_object_or_404(PasswordReset, token=token)

    # If token is expired, show error
    if reset_request.is_expired():
        messages.error(request, "Password reset link has expired.")

    if request.method == "POST":
        new_password = request.POST.get('password')

        if not new_password:
            messages.error(request, "Please enter a new password.")

        # Update the user's password
        reset_request.user.password = make_password(new_password)
        reset_request.user.save()

        # Delete token after successful password reset
        reset_request.delete()

        messages.success(request, "Password has been reset successfully!")
        return redirect('login1')

    return render(request, 'reset_password.html', {'token': token})

@login_required
def user_management(request):
    users = Register.objects.all()  # Get only unverified users
    return render(request, 'user_management.html', {'users': users})

@login_required
def verify_user(request, user_id):
    user = Register.objects.get(id=user_id)
    user.is_verified = True
    user.save()
    return JsonResponse({'message': f'{user.user.username} has been verified!'})

def user_logins(request):
    if not request.user.is_superuser:
        return redirect('index')  # Redirect non-admin users
    
    verified_users = Register.objects.filter(is_verified=True)
    return render(request, 'user_logins.html', {'verified_users': verified_users})

# def impersonate_user(request, user_id):
#     if not request.user.is_superuser:
#         return redirect('login')  # Ensure only admin can impersonate users

#     user_to_impersonate = get_object_or_404(User, id=user_id)
    
#     login(request, user_to_impersonate)

#     return redirect('user_dashboard')  

# def end_impersonation(request):
#     logout(request)  # Logs out the impersonated user
#     return redirect('admin_dashboard')



@require_POST
@login_required
def impersonate_user(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        user_to_impersonate = User.objects.get(id=user_id)
        login(request, user_to_impersonate)
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@login_required
def end_impersonation(request):
    if hasattr(request, 'original_user'):
        login(request, request.original_user)
        del request.session['original_user_id']
    return redirect('admin_dashboard')



@login_required
def unverify_user(request, user_id):
    user = Register.objects.get(id=user_id)
    user.is_verified = False
    user.save()
    return JsonResponse({'message': f'{user.user.username} has been unverified!'})


# delete user
@require_POST
@login_required
def delete_user(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        user_to_delete = User.objects.get(id=user_id)
        
        # Delete related objects first to maintain data integrity
        if hasattr(user_to_delete, 'register'):
            user_to_delete.register.delete()
        if hasattr(user_to_delete, 'wallet'):
            user_to_delete.wallet.delete()
        if hasattr(user_to_delete, 'userreferral'):
            user_to_delete.userreferral.delete()
            
        # Delete the user
        user_to_delete.delete()
        
        return JsonResponse({'message': 'User deleted successfully'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# new
# task list
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone

def task_list(request):
    tasks = Task.objects.all().order_by('-created_at')
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    # Apply filters
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(created_by__username__icontains=search_query)
        )
    
    if status_filter:
        if status_filter == 'expired':
            tasks = tasks.filter(deadline__lt=timezone.now())
        else:
            tasks = tasks.filter(status=status_filter)
    
    if date_filter:
        tasks = tasks.filter(deadline__date=date_filter)
    
    # Pagination
    paginator = Paginator(tasks, 10)  # Show 10 tasks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'task_list.html', {
        'tasks': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter
    })


def edit_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task Updated Successfully")
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'create_task.html', {
        'form': form,
        'edit_mode': True,
        'task': task
    })

def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == "POST":
        task.delete()
        messages.success(request, "Task Deleted Successfully")
        return redirect('task_list')
    
    return render(request, 'confirm_delete.html', {'task': task})
    
    
    
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from collections import deque

@login_required
def referral_tree_view(request):
    try:
        # Get the current user's referral information
        user_referral = UserReferral.objects.get(user=request.user)
        
        # Prepare the tree data
        tree_data = build_referral_tree(user_referral)
        
        context = {
            'referral_tree': tree_data,
            'referral_link': user_referral.referral_link,
            'total_referrals': count_total_referrals(user_referral)
        }
        return render(request, 'referral_tree.html', context)
    except UserReferral.DoesNotExist:
        messages.error(request, "Referral information not found")
        return redirect('home')  # Redirect to your home page

def build_referral_tree(user_referral, max_depth=5):
    """
    Build a tree structure of referrals up to a certain depth
    """
    tree = {
        'user': user_referral.user,
        'register': Register.objects.filter(user=user_referral.user).first(),
        'children': []
    }
    
    # Use BFS to build the tree up to max_depth
    queue = deque([(user_referral, tree, 0)])
    
    while queue:
        current_ref, current_node, depth = queue.popleft()
        
        if depth >= max_depth:
            continue
            
        # Get all children of the current referral
        children = current_ref.children.all().order_by('user__date_joined')
        
        for child in children:
            # Get the Register info for the child user
            register_info = Register.objects.filter(user=child.user).first()
            
            child_node = {
                'user': child.user,
                'register': register_info,
                'children': []
            }
            
            current_node['children'].append(child_node)
            queue.append((child, child_node, depth + 1))
    
    return tree

def count_total_referrals(user_referral):
    """
    Count total referrals in the entire downline
    """
    count = 0
    queue = deque([user_referral])
    
    while queue:
        current = queue.popleft()
        count += current.children.count()
        for child in current.children.all():
            queue.append(child)
    
    return count
    
    
def edit_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'create_task.html', {'form': form})




