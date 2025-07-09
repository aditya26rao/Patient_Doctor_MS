from django import forms
from django.contrib.auth.models import User
from .models import Profile, Appointment, MedicalRecord, Prescription
from django.utils import timezone
from datetime import datetime, timedelta

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a strong password'
        }),
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        }),
        label="Confirm Password"
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        }),
        required=True
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        }),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a unique username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
        }

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords don't match")
        return password_confirm

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered")
        return email

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'user_type', 'specialization', 'phone_number', 'date_of_birth',
            'address', 'blood_group', 'allergies', 'emergency_contact',
            'emergency_contact_name', 'license_number', 'years_of_experience',
            'consultation_fee', 'bio'
        ]
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your full address'
            }),
            'blood_group': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., A+, B-, O+'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any known allergies'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact number'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact name'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Medical license number'
            }),
            'years_of_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 50
            }),
            'consultation_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about your professional background'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields required based on user type
        self.fields['specialization'].required = False

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'description', 'priority', 'contact_number']
        widgets = {
            'doctor': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select a doctor'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please describe your symptoms or reason for visit in detail'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number for appointment confirmation'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter doctors only
        self.fields['doctor'].queryset = User.objects.filter(
            profile__user_type='doctor',
            profile__is_available=True
        )
        self.fields['doctor'].empty_label = "Select a doctor"
        
        # Set minimum date to today
        today = timezone.now().date()
        self.fields['date'].widget.attrs['min'] = today.isoformat()
        
        # Set time constraints
        self.fields['time'].widget.attrs.update({
            'min': '09:00',
            'max': '18:00',
            'step': '1800'  # 30-minute intervals
        })

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now().date():
            raise forms.ValidationError("Appointment date cannot be in the past")
        
        # Don't allow appointments more than 3 months in advance
        max_date = timezone.now().date() + timedelta(days=90)
        if date and date > max_date:
            raise forms.ValidationError("Appointments can only be booked up to 3 months in advance")
        
        return date

    def clean_time(self):
        time = self.cleaned_data.get('time')
        if time:
            # Check if time is within working hours (9 AM to 6 PM)
            if time < datetime.strptime('09:00', '%H:%M').time() or time > datetime.strptime('18:00', '%H:%M').time():
                raise forms.ValidationError("Appointments are only available between 9:00 AM and 6:00 PM")
        return time

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        if doctor and date and time:
            # Check if the slot is already booked
            existing_appointment = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time=time,
                status__in=['scheduled', 'confirmed']
            )
            
            if self.instance.pk:
                existing_appointment = existing_appointment.exclude(pk=self.instance.pk)
            
            if existing_appointment.exists():
                raise forms.ValidationError(
                    f"This time slot is already booked with Dr. {doctor.get_full_name() or doctor.username}. "
                    "Please choose a different time."
                )

        return cleaned_data

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            'diagnosis', 'symptoms', 'treatment', 'medications', 'test_results',
            'blood_pressure', 'heart_rate', 'temperature', 'weight', 'height'
        ]
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'treatment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'test_results': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'blood_pressure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 120/80'
            }),
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'beats per minute'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': '°F'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'lbs'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'inches'
            }),
        }

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['medication_name', 'dosage', 'frequency', 'duration', 'instructions']
        widgets = {
            'medication_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Medication name'
            }),
            'dosage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 500mg'
            }),
            'frequency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Twice daily'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 7 days'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional instructions (e.g., take with food)'
            }),
        }

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'notes', 'follow_up_required', 'follow_up_date']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Doctor notes (visible to patient)'
            }),
            'follow_up_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
