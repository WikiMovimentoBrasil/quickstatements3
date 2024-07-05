from django.shortcuts import render, redirect

from api.client import Client

def login(request):
    if request.session.get("username") is not None:
        return redirect("/auth/profile/")
    else:
        return render(request, "login.html", {})


def logout(request):
    request.session.flush()
    return redirect("/")


def login_dev(request):
    if request.method == "POST":
        # obtain dev token
        token = request.POST["access_token"]

        client = Client.from_token(token)

        # Verify submitted token by checking `username` in the response
        try:
            username = client.get_username()
        except ValueError as e:
            data = {"error": e}
            return render(request, "login_dev.html", data, status=400)

        # save access token and Wikimedia username in the user's session
        request.session["access_token"] = token
        request.session["username"] = username

        return redirect("/auth/profile/")
    else:
        return render(request, "login_dev.html", {})


def profile(request):
    data = {
        "username": request.session.get("username"),
    }
    return render(request, "profile.html", data)
