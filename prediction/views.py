from django.shortcuts import render
from django.http import JsonResponse


def home(request):
    return render(request, 'prediction/home.html')

def predict_disease(request):
    if request.method == 'POST':
        symptoms = request.POST.get('symptoms')
       
        return JsonResponse({'disease': 'Common Cold'})
    return render(request, 'prediction/predict.html')
# Create your views here.

