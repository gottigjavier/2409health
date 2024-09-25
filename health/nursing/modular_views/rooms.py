from django.shortcuts import render

# simulates the call and answer buttons of the rooms 
def rooms(request):
    return render(request, 'rooms.html')
