from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def signup_view(request):
    if request.method == 'POST':  #This is for the user creating credentials, POST is used
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Passwords Dont match')
            return render(request, 'people/signup.html')
        user = User.objects.create_user(username = username, password = password1)
        messages.success(request, 'Account has been creatd successfully')
        return redirect('login')
    return render(request, 'people/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request,username = username, password = password)
        if user:
            login(request,user)
            return redirect('problem_list')
        else:
            return render(request,'users/login.html', {'error: Bad creds'})
    return render(request,'people/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

