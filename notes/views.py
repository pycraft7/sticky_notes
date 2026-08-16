from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib.auth.decorators import login_required

from .models import Note
from accounts.models import Profile


@login_required
def home_views(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name()
            or request.user.username
        }
    )

    notes = Note.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "notes/home.html",
        {
            "notes": notes,
            "profile": profile,
        }
    )


@login_required
def add_note(request):

    if request.method == "POST":

        title = request.POST["title"]
        content = request.POST["content"]

        Note.objects.create(
            user=request.user,
            title=title,
            content=content
        )

        return redirect("home_views")

    return render(
        request,
        "notes/add_note.html"
    )


@login_required
def edit_note(request, pk):

    note = get_object_or_404(
        Note,
        pk=pk,
        user=request.user
    )

    if request.method == "POST":

        title = request.POST["title"]
        content = request.POST["content"]

        note.title = title
        note.content = content

        note.save()

        return redirect("home_views")

    return render(
        request,
        "notes/edit_note.html",
        {"note": note}
    )


@login_required
def delete_note(request, pk):

    note = get_object_or_404(
        Note,
        pk=pk,
        user=request.user
    )

    if request.method == "POST":

        note.delete()

        return redirect("home_views")

    return render(
        request,
        "notes/delete_note.html",
        {"note": note}
    )