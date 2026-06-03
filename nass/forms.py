from django import forms
from .models import TaskUserAssignment,Task ,User,Register
from django.core.exceptions import ValidationError


from django import forms
from .models import TaskUserAssignment, Task

class TaskSubmissionForm(forms.ModelForm):
    screenshot = forms.ImageField(
        required=True,
        label="Screenshot Proof",
        help_text="Upload a screenshot as proof of task completion"
    )
    proof_text = forms.CharField(
        required=True,
        widget=forms.Textarea,
        label="Proof Description",
        help_text="Describe how you completed the task"
    )
    proof_video = forms.FileField(
        required=False,
        label="Video Proof (Optional)",
        help_text="Upload a video if required (max 25MB)",
    )

    class Meta:
        model = TaskUserAssignment
        fields = ['screenshot', 'proof_text', 'proof_video']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['screenshot'].widget.attrs.update({'class': 'form-control'})
        self.fields['proof_text'].widget.attrs.update({'class': 'form-control', 'rows': 3})
        self.fields['proof_video'].widget.attrs.update({'class': 'form-control'})

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_by'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()

# class TaskSubmissionForm(forms.ModelForm):
#     like = forms.BooleanField(required=False, label="Liked")
#     subscribe = forms.BooleanField(required=False, label="Subscribed")
#     follow = forms.BooleanField(required=False, label="Followed")
#     comment = forms.BooleanField(required=False, label="Commented")
#     download = forms.BooleanField(required=False, label="Downloaded")
#     share = forms.BooleanField(required=False, label="Shared")

#     class Meta:
#         model = TaskUserAssignment
#         fields = ['proof_screenshot', 'proof_text', 'proof_video']

# class TaskForm(forms.ModelForm):
#     class Meta:
#         model = Task
#         fields = ['title', 'description', 'commission_per_task','payout', 'deadline', 'created_by', 'users_assigned', 'proof', 'status','scheduled_at']
#         widgets = {
#             'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task title'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter task description'}),
#             'commission_per_task': forms.NumberInput(attrs={'class': 'form-control'}),
#             'payout': forms.NumberInput(attrs={'class': 'form-control'}),
#             'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
#             'created_by': forms.Select(attrs={'class': 'form-select'}),
#             'users_assigned': forms.CheckboxSelectMultiple(attrs={'class': 'users-assigned'}),
#             'proof': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional proof details'}),
#             'status': forms.Select(attrs={'class': 'form-select'}),
#             'scheduled_at':forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
#         }

# class TaskForm(forms.ModelForm):
#     # user_assigned = forms.ModelMultipleChoiceField(
#     #     queryset = User.objects.none(),
#     #     widget = forms.CheckboxSelectMultiple(attrs={'class':'form-select'}),
#     #     required = False
#     # )

#     class Meta:
#         model = Task
#         fields = ['title', 'description', 'commission_per_task','payout', 'deadline', 'created_by', 'users_assigned', 'proof', 'status','scheduled_at','workers_limit','task_url']
#         widgets = {
#             'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task title'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter task description'}),
#             'task_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter task URL'}),
#             'commission_per_task': forms.NumberInput(attrs={'class': 'form-control'}),
#             'payout': forms.NumberInput(attrs={'class': 'form-control'}),
#             'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
#             'created_by': forms.Select(attrs={'class': 'form-select'}),
#             'users_assigned': forms.CheckboxSelectMultiple(attrs={'class': 'users-assigned'}),
#             'proof': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional proof details'}),
#             'status': forms.Select(attrs={'class': 'form-select'}),
#             'scheduled_at':forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
#             'workers_limit': forms.NumberInput(attrs={'class': 'form-control'})
#         }


#     def clean(self):
#         cleaned_data = super().clean()
#         if not cleaned_data.get('task_url') and cleaned_data.get('requires_url'):
#             raise ValidationError("Task URL is required for this type of task")
#         return cleaned_data

#     def filter_users(self,country = None , languages = None):
#         queryset = Register.objects.all()
#         if country:
#             queryset = queryset.filter(country = country)
#         if languages:
#             queryset = queryset.filter(languages__icontains = languages)

#         self.fields['users_assigned'].queryset = queryset




class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'commission_per_task', 'payout', 'deadline', 
                 'created_by', 'users_assigned', 'proof', 'status', 'scheduled_at', 
                 'workers_limit', 'task_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter task description'}),
            'task_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter task URL'}),
            'commission_per_task': forms.NumberInput(attrs={'class': 'form-control'}),
            'payout': forms.NumberInput(attrs={'class': 'form-control'}),
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
            'users_assigned': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'proof': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional proof details'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'workers_limit': forms.NumberInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        # Set the queryset for users_assigned (non-admin users)
        self.fields['users_assigned'].queryset = User.objects.filter(is_superuser=False)