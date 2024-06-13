import requests

from django.shortcuts import render, redirect


def login(request):
    return render(request, "login.html", {})


def logout(request):
    request.session.flush()
    return redirect("/")


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
    # TODO: move this logic into the api app
    access_token = request.session.get("access_token")
    if access_token is not None:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            "https://www.mediawiki.org/w/rest.php/oauth2/resource/profile",
            headers=headers,
        )
        username = response.json()["username"]
    else:
        username = None

    data = {
        "username": username,
    }
    return render(request, "profile.html", data)
