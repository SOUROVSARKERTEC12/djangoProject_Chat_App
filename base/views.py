from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Topic, Message
from .forms import RoomForm, UserForm


# Create your views here.

# rooms = [
#     {'id': 1, 'name': 'Web Developer'},
#     {'id': 2, 'name': 'Design Segment'},
#     {'id': 3, 'name': 'Frontend Design'},
# ]

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username, password=password)
        except :
            messages.error(request, 'User doses not exist.')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR Password does not exist.')

    context = {'page': page}
    return render(request, 'chatTWS/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration!!')

    return render(request, 'chatTWS/login_register.html', {'form': form})


def home(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms': rooms, 'topics': topics,
               'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'chatTWS/home.html', context)


def room(request, pk):
    roomNum = Room.objects.get(id=pk)
    room_messages = roomNum.message_set.all()
    participants = roomNum.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=roomNum,
            body=request.POST.get('body')
        )
        roomNum.participants.add(request.user)
        return redirect('room', pk=roomNum.id)

    context = {'room': roomNum, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'chatTWS/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms,
               'room_messages': room_messages, 'topics': topics}
    return render(request, 'chatTWS/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'chatTWS/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    rooms = Room.objects.get(id=pk)
    form = RoomForm(instance=rooms)
    topics = Topic.objects.all()
    if request.user != rooms.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        rooms.name = request.POST.get('name')
        rooms.topic = topic
        rooms.description = request.POST.get('description')
        rooms.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'rooms': rooms}
    return render(request, 'chatTWS/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    rooms = Room.objects.get(id=pk)

    if request.user != rooms.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        rooms.delete()
        return redirect('home')
    return render(request, 'chatTWS/delete.html', {'obj': rooms})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'chatTWS/delete.html', {'obj': message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    return render(request, 'chatTWS/update-user.html', {'form': form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'chatTWS/topics.html', {'topics': topics})


def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'chatTWS/activity.html', {'room_messages': room_messages})
