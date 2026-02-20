from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'web/index.html'

def login_view(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        if not User.objects.filter(username=username).exists():
            messages.error(request, "Такого пользователя не существует.")
            return render(request, "login.html")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Неправильный пароль.")
            return render(request, "login.html")

        login(request, user)
        return redirect("index")

    return render(request, "login.html")