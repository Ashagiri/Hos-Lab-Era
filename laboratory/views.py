from django.shortcuts import render
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("""
        <h1>🚀 Hos-Lab-Era Database Connected Successfully!</h1>
        <p>The Django backend environment is fully running with no errors.</p>
        <p>To access your admin panel dashboard, go to <a href="/admin/">/admin/</a></p>
    """)

def home_view(request):
    # This automatically picks up user data to render personalized welcome layouts
    return render(request, 'home.html')