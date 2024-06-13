from django.shortcuts import render, redirect


def login(request):
    return render(request, "login.html", {})


def login_dev(request):
    if request.method == "POST":
        # obtain dev token
        token = request.POST["access_token"]

        # save access token in the user's session
        request.session["access_token"] = token

        return redirect("/auth/profile/")
    else:
        return render(request, "login_dev.html", {})


def profile(request):
    data = {
        "access_token": request.session.get("access_token"),
    }
    return render(request, "profile.html", data)
