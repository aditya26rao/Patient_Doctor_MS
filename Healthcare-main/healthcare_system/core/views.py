from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, ProfileForm, AppointmentForm
from .models import Profile, Appointment
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone

# Register user
def register_view(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect('login')
    else:
        user_form = UserRegisterForm()
        profile_form = ProfileForm()
    return render(request, 'core/register.html', {'user_form': user_form, 'profile_form': profile_form})

# Login user
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'core/login.html')

# Logout user
def logout_view(request):
    logout(request)
    return redirect('login')

# Dashboard view
@login_required
def dashboard_view(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact admin.")
        return redirect('logout')
    
    if profile.user_type == 'doctor':
        appointments = Appointment.objects.filter(doctor=request.user).order_by('-date', '-time')[:10]
        upcoming_count = Appointment.objects.filter(
            doctor=request.user,
            date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        ).count()
    elif profile.user_type == 'patient':
        appointments = Appointment.objects.filter(patient=request.user).order_by('-date', '-time')[:10]
        upcoming_count = Appointment.objects.filter(
            patient=request.user,
            date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        ).count()
    else:
        messages.error(request, "Invalid user type.")
        return redirect('logout')
    
    context = {
        'appointments': appointments,
        'profile': profile,
        'upcoming_count': upcoming_count,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.save()

            # Email to doctor
            subject = "New Appointment Booked"
            message = f"Dear {appointment.doctor.username},\n\nA new appointment has been booked by {appointment.patient.username} on {appointment.date} at {appointment.time}.\n\nDescription: {appointment.description}\n\nPlease login to check more details."
            send_mail(subject, message, 'your_email@gmail.com', [appointment.doctor.email])

            messages.success(request, "Appointment booked successfully and doctor notified.")
            return redirect('dashboard')
    else:
        form = AppointmentForm()
    return render(request, 'core/book_appointment.html', {'form': form})


from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

@login_required
def generate_pdf(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    template_path = 'core/appointment_pdf.html'
    context = {'appointment': appointment}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="appointment_summary.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    return response

from django.db.models import Count

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    doctor_count = Profile.objects.filter(user_type='doctor').count()
    patient_count = Profile.objects.filter(user_type='patient').count()

    appointment_data = Appointment.objects.values('date').annotate(count=Count('id')).order_by('date')
    dates = [entry['date'].strftime("%b %d") for entry in appointment_data]
    counts = [entry['count'] for entry in appointment_data]

    return render(request, 'core/admin_dashboard.html', {
        'doctor_count': doctor_count,
        'patient_count': patient_count,
        'dates': dates,
        'counts': counts,
    })
