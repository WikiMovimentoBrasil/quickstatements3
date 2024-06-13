import requests

from django.shortcuts import render, redirect


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

        # TODO: move this logic into the api app
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            "https://www.mediawiki.org/w/rest.php/oauth2/resource/profile",
            headers=headers,
        ).json()

        # Verify submitted token by checking `username` in the response
        try:
            username = response["username"]
        except KeyError:
            data = {"error": response}
            return render(request, "login_dev.html", data)

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
