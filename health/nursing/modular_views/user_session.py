from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from .data_analytics import recording
from ..models import User


# ----------------User Manager --------------------------------
def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("home"))
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))

@login_required
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        is_leader = request.POST.get("is-leader", False) # for the future

        if is_leader == "on":
            leader = True
        else:
            leader = False

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.leader = leader
            user.is_staff = leader
            user.image = request.FILES.get("image", "useravatar.png")
            user.save()
            recording(request.user.username, 'register new user', 'none', 'new user registered as: ' + username)
        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("home"))
    else:
        return render(request, "register.html")

# ------------------ End User manager -----------------------

