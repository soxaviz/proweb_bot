from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.views.decorators.http import require_POST, require_GET
import telebot
import json, sys, os, time
from .models import UserAdmin


def main_view(request):
    response = JsonResponse({'ok':True, 'result':True, 'method':request.method, })
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    # response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"

    return response



