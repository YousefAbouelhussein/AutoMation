import time
import requests
from bs4 import BeautifulSoup
import pywhatkit

from django.shortcuts import render, redirect
from .models import Car
from .forms import CarForm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def scrape_cars():
    url = "URL_DEL_SITO_DI_AUTO_USATE"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Estrapola i dati dal sito
    cars = []
    for listing in soup.select('.listing'):
        name = listing.select_one('.name').text
        phone_number = listing.select_one('.phone').text
        car_model = listing.select_one('.model').text
        description = listing.select_one('.description').text
        photo_url = listing.select_one('.photo')['src']
        cars.append({
            'name': name,
            'phone_number': phone_number,
            'car_model': car_model,
            'description': description,
            'photo_url': photo_url
        })
    return cars

def send_messages(request):
    if request.method == "POST":
        cars = scrape_cars()
        for car_data in cars:
            car, created = Car.objects.get_or_create(phone_number=car_data['phone_number'], defaults=car_data)
            if created:
                message = f"Ciao {car.name}, ho visto il tuo annuncio sul sito AutoScout24 e vorrei proporti di portare la tua auto nella mia concessionaria, saresti interessato? Rispondi solo con 'SI' o 'NO', questo è un messaggio automatizzato, nel caso fossi interessato ti ricontatteremo il prima possibile."
                pywhatkit.sendwhatmsg_instantly(car.phone_number, message)
                car.contacted = True
                car.save()
                time.sleep(10)  # Attendi 10 secondi tra un messaggio e l'altro

    cars = Car.objects.all()
    return render(request, 'scraper/send_messages.html', {'cars': cars})

def send_messages_view(request):
    return render(request, 'send_messages.html')

def monitor_responses():
    # Configura il driver di Selenium
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.get("https://web.whatsapp.com/")

    # Attendi che l'utente scansiona il codice QR
    input("Scansiona il codice QR e premi Invio per continuare...")

    # Recupera i contatti contattati
    contacted_cars = Car.objects.filter(contacted=True)

    for car in contacted_cars:
        # Cerca il contatto su WhatsApp
        search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        search_box.clear()
        search_box.send_keys(car.phone_number)
        time.sleep(2)  # Attendi che il contatto venga trovato
        search_box.send_keys(Keys.ENTER)

        # Attendi un po' per caricare la chat
        time.sleep(5)

        # Recupera i messaggi nella chat
        messages = driver.find_elements(By.XPATH, '//div[@class="_1Gy50"]//span[@class="_1VzZY"]')
        for message in messages:
            if message.text.lower() in ["si", "sì"]:
                car.interested = True
                car.save()
                print(f"{car.name} ha risposto con 'SI'.")
            elif message.text.lower() in ["no"]:
                print(f"{car.name} ha risposto con 'NO'.")
        
        # Torna alla schermata principale
        driver.back()
        time.sleep(2)

    driver.quit()

def interested_responses(request):
    interested_cars = Car.objects.filter(interested=True)
    return render(request, 'scraper/responses.html', {'cars': interested_cars})
