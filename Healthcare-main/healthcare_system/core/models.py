from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
from django.urls import reverse

USER_TYPE_CHOICES = (
    ('doctor', 'Doctor'),
    ('patient', 'Patient'),
)

SPECIALIZATION_CHOICES = (
    ('general', 'General Practice'),
    ('cardiology', 'Cardiology'),
    ('neurology', 'Neurology'),
    ('orthopedics', 'Orthopedics'),
    ('ophthalmology', 'Ophthalmology'),
    ('pediatrics', 'Pediatrics'),
    ('dermatology', 'Dermatology'),
    ('psychiatry', 'Psychiatry'),
    ('radiology', 'Radiology'),
    ('emergency', 'Emergency Medicine'),
)

APPOINTMENT_STATUS_CHOICES = (
    ('scheduled', 'Scheduled'),
    ('confirmed', 'Confirmed'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ('no_show', 'No Show'),
)

PRIORITY_CHOICES = (
    ('normal', 'Normal'),
    ('urgent', 'Urgent'),
    ('emergency', 'Emergency'),
)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, blank=True, null=True)
    
    # Personal Information
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', 
                                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    
    # Medical Information (for patients)
    emergency_contact = models.CharField(max_length=17, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True, help_text="List any known allergies")
    medical_history = models.TextField(blank=True)
    
    # Professional Information (for doctors)
    license_number = models.CharField(max_length=50, blank=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    bio = models.TextField(blank=True, help_text="Professional biography")
    
    # Profile settings
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    notifications_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.user_type.title()}"
    
    def get_full_name(self):
        return self.user.get_full_name() or self.user.username
    
    class Meta:
        ordering = ['user__username']

class Appointment(models.Model):
    patient = models.ForeignKey(User, related_name='patient_appointments', on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, related_name='doctor_appointments', on_delete=models.CASCADE)
    
    # Appointment Details
    date = models.DateField()
    time = models.TimeField()
    description = models.TextField(help_text="Describe your symptoms or reason for visit")
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Additional Information
    contact_number = models.CharField(max_length=17, blank=True)
    notes = models.TextField(blank=True, help_text="Doctor's notes (internal)")
    prescription_notes = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Payment
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    payment_status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"{self.patient.get_full_name() or self.patient.username} with Dr. {self.doctor.get_full_name() or self.doctor.username} on {self.date}"
    
    def get_absolute_url(self):
        return reverse('appointment_detail', kwargs={'pk': self.pk})
    
    @property
    def is_upcoming(self):
        from datetime import datetime, time
        appointment_datetime = datetime.combine(self.date, self.time)
        return appointment_datetime > timezone.now()
    
    @property
    def is_today(self):
        return self.date == timezone.now().date()
    
    def can_be_cancelled(self):
        # Can be cancelled up to 24 hours before appointment
        from datetime import datetime, timedelta
        appointment_datetime = datetime.combine(self.date, self.time)
        cutoff_time = appointment_datetime - timedelta(hours=24)
        return timezone.now() < cutoff_time and self.status in ['scheduled', 'confirmed']
    
    class Meta:
        ordering = ['-date', '-time']
        unique_together = ['doctor', 'date', 'time']  # Prevent double booking

class MedicalRecord(models.Model):
    patient = models.ForeignKey(User, related_name='medical_records', on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, related_name='created_records', on_delete=models.CASCADE)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, blank=True, null=True)
    
    # Record Details
    diagnosis = models.TextField()
    symptoms = models.TextField()
    treatment = models.TextField()
    medications = models.TextField(blank=True)
    test_results = models.TextField(blank=True)
    
    # Vitals
    blood_pressure = models.CharField(max_length=20, blank=True)
    heart_rate = models.PositiveIntegerField(blank=True, null=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medical Record for {self.patient.get_full_name() or self.patient.username} - {self.created_at.date()}"
    
    class Meta:
        ordering = ['-created_at']

class Prescription(models.Model):
    patient = models.ForeignKey(User, related_name='prescriptions', on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, related_name='prescribed_medications', on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, related_name='prescriptions', on_delete=models.CASCADE, blank=True, null=True)
    
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.medication_name} for {self.patient.get_full_name() or self.patient.username}"
    
    class Meta:
        ordering = ['-created_at']

class DoctorSchedule(models.Model):
    WEEKDAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    doctor = models.ForeignKey(User, related_name='schedules', on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['doctor', 'weekday', 'start_time']
        ordering = ['weekday', 'start_time']

    def __str__(self):
        return f"Dr. {self.doctor.get_full_name() or self.doctor.username} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('appointment_booked', 'Appointment Booked'),
        ('appointment_confirmed', 'Appointment Confirmed'),
        ('appointment_cancelled', 'Appointment Cancelled'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('prescription_ready', 'Prescription Ready'),
        ('test_results', 'Test Results Available'),
        ('general', 'General'),
    )
    
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"
