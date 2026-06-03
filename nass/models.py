from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, timezone
from django.utils.timezone import now
from django.core.validators import RegexValidator
import secrets

class Register(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    first_name = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^[\w\W]+$',  # Allows ALL characters
            message="First name can contain letters, numbers, and special characters."
        )]
    )
    email=models.EmailField(max_length=30)
    phone=models.BigIntegerField(default=1010101010,null=True, blank=True)
    birth_date =models.DateField(null=True, blank=True)
    gender_choice =[('male','Male'),('female','Female'),('other','Other')] 
    gender = models.CharField(max_length=10,choices=gender_choice,null=True, blank=True)
    status_choice =[('worker','Worker'),('student','Student'),('other','Other')]
    status = models.CharField(max_length=10,choices=status_choice,null=True, blank=True)
    qualification = models.CharField(max_length=50,null=True, blank=True)
    address = models.CharField(max_length=100,null=True, blank=True)
    landmark = models.CharField(max_length=50,null=True, blank=True)
    pincode = models.IntegerField(default=0,null=True, blank=True)
    city = models.CharField(max_length=50,null=True, blank=True) 
    state = models.CharField(max_length=50,null=True, blank=True) 
    country = models.CharField(max_length=50,null=True, blank=True) 
    hobby = models.CharField(max_length=50,null=True, blank=True) 
    annual_income = models.CharField(max_length=20,null=True, blank=True)
    languages = models.JSONField(default=list,null=True, blank=True)
    about = models.CharField(max_length=200,null=True, blank=True)
    images = models.ImageField(upload_to='User_Images/',null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}"

from django.db import models
from django.contrib.auth.models import User

class BankDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_holder = models.CharField(max_length=50)
    account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=50)
    branch = models.CharField(max_length=50, blank=True, null=True)

    def _str_(self):
        return f"{self.account_holder}'s {self.bank_name} Account"

from django.utils import timezone

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    payout = models.DecimalField(max_digits=6, decimal_places=2, help_text="Commission per user")
    commission_per_task = models.DecimalField(max_digits=8, decimal_places=2, help_text="Total commission for the task",blank=True,null=True)
    total_commission_pool = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total commission pool for this task (auto-calculated)",
        blank=True,
        null=True
    )
    deadline = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks_created')
    users_assigned = models.ManyToManyField(
        User, 
        through='TaskUserAssignment',
        related_name='assigned_tasks'
    )
    proof = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'),('in_progress', 'In Progress'), ('completed', 'Completed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True,)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    workers_limit = models.IntegerField(null=True, blank=True)
    task_url = models.URLField(max_length=500, blank=True, null=True)
    
    @property
    def is_expired(self):
        """Check if the task has passed its deadline (considering both date and time)"""
        return timezone.now() > self.deadline
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-calculate total commission pool based on workers_limit
        if self.workers_limit and self.commission_per_task:
            self.total_commission_pool = self.workers_limit * self.commission_per_task
        super().save(*args, **kwargs)
    
# models.py - Update TaskUserAssignment model
class TaskUserAssignment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid')
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_assignments')
    
    # Proof Submission Fields
    screenshot = models.ImageField(upload_to='task_screenshots/', null=True, blank=True)
    proof_text = models.TextField(blank=True, null=True)
    proof_video = models.FileField(upload_to='task_proofs/videos/', null=True, blank=True)
    proof_submitted = models.BooleanField(default=False)
    proof_submitted_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)  # Add this if you need it
    
    # Status Management
    submission_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Commission Tracking
    commission_distributed = models.BooleanField(default=False)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission_distribution_log = models.JSONField(default=list, blank=True)
    commission_distributed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('task', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.task.title} ({self.get_submission_status_display()})"

    def submit_proof(self, screenshot=None, proof_text=None, proof_video=None):
        """Submit proof for task completion"""
        if screenshot:
            self.screenshot = screenshot
        if proof_text:
            self.proof_text = proof_text
        if proof_video:
            self.proof_video = proof_video
            
        self.proof_submitted = True
        self.proof_submitted_at = timezone.now()
        self.submission_status = 'pending_review'
        self.save()
        return True

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def add_balance(self, amount):
        self.wallet_balance += amount
        self.save()
    
    def total_earnings(self):
        return self.wallet_balance + self.paid_amount
    
    def _str_(self):
        return f"{self.user.username}'s Wallet"
 
class WithdrawalRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='withdraw') 
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bank_account = models.CharField(max_length=100)  
    status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    requested_at  = models.DateTimeField(auto_now_add=True)
    processed_at  = models.DateTimeField(auto_now=True)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    def _str_(self):
        return f"{self.user} - {self.amount} - {self.status}"
    
class UserSupport(models.Model):
    CATEGORY_CHOICES = [
        ('review', 'Review'),
        ('problem', 'Problem'),
        ('question', 'Question'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def _str_(self):
        return f"{self.user.username} - {self.get_category_display()} - {self.subject[:50]}"
    
class UserReferral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral')
    parent = models.ForeignKey('self', on_delete=models.CASCADE,null=True, blank=True, related_name='children')
    referral_link = models.CharField(max_length=255, unique=True,null=True, blank=True)

    def get_downline_count(self):
        """Get total number of referrals in the downline"""
        return self.children.count()
    
    def get_direct_referrals(self):
        """Get direct referrals with their register information"""
        return self.children.select_related('user').prefetch_related(
            'user__register'
        ).all()
    
    def get_referral_tree(self, max_depth=3):
        """Get a limited depth tree structure"""
        def build_tree(node, depth):
            if depth >= max_depth:
                return None
                
            register = Register.objects.filter(user=node.user).first()
            return {
                'user': node.user,
                'register': register,
                'children': [build_tree(child, depth+1) for child in node.children.all()],
                'depth': depth
            }
            
        return build_tree(self, 0)
        
    def __str__(self):
        return f"{self.user.username}"

class Txn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.CharField(max_length=255, default='Task Commission')
    created_at = models.DateTimeField(auto_now_add=True)

        
class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.created_at < now() - timedelta(hours=24)

    def __str__(self):
        return f"{self.user.username} - {self.token}"

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.created_at < now() - timedelta(hours=1)

    def __str__(self):
        return f"{self.user.username} - {self.token}"
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        