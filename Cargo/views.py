from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.generic import TemplateView


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "web/index.html"


def _safe_next_url(request) -> str:
    # Support both GET and POST next (Django's LoginView convention)
    next_url = (request.POST.get("next") or request.GET.get("next") or "").strip()
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("index")


def login_view(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        if not User.objects.filter(username=username).exists():
            messages.error(request, _("User does not exist."))
            return render(request, "login.html")

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, _("Incorrect password."))
            return render(request, "login.html")

        login(request, user)

        # Remember me (optional): if unchecked, session ends when browser closes
        remember = request.POST.get("remember")
        if remember:
            # 2 weeks, similar to many templates; adjust if you need another period
            request.session.set_expiry(getattr(settings, "SESSION_COOKIE_AGE", 1209600))
        else:
            request.session.set_expiry(0)

        return redirect(_safe_next_url(request))

    return render(request, "login.html")
