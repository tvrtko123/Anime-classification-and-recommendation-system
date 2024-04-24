import json
import requests
import secrets
from django.shortcuts import redirect, render
from django.http import HttpResponse
from pymongo import MongoClient
import time

CLIENT_ID = 'e1ff4897669753e728f93fedd2054cf9'
CLIENT_SECRET = 'f7397555e8e12358d7531cda31a7c4ccc0aa7e270df21354fd274969768f6e89'
REDIRECT_URI = 'http://127.0.0.1:8000/app/callback'

def get_new_code_verifier() -> str:
    token = secrets.token_urlsafe(100)
    return token[:128]

def home(request):
    code_verifier = get_new_code_verifier()
    request.session['code_verifier'] = code_verifier

    code_challenge = code_verifier  # Code challenge can be the same as the verifier in this case
    authorization_url = f'https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&code_challenge={code_challenge}'

    return render(request, 'home.html', {'authorization_url': authorization_url})

def generate_new_token(request):
    authorisation_code = request.GET.get('code')
    code_verifier = request.session.get('code_verifier')

    url = 'https://myanimelist.net/v1/oauth2/token'
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': authorisation_code,
        'code_verifier': code_verifier,
        'grant_type': 'authorization_code'
    }

    response = requests.post(url, data)
    response.raise_for_status()  # Check whether the request contains errors

    token = response.json()
    response.close()
    print('Token generated successfully!')

    with open('token.json', 'w') as file:
        json.dump(token, file, indent=4)
        print('Token saved in "token.json"')

    request.session['access_token'] = token['access_token']
    request.session['refresh_token'] = token['refresh_token']

    return redirect('app:success')

def refresh_token(request):
    refresh_token = request.session.get('refresh_token')

    url = 'https://myanimelist.net/v1/oauth2/token'
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    response = requests.post(url, data)
    response.raise_for_status()

    token = response.json()
    response.close()
    print('Token refreshed successfully!')

    with open('token.json', 'w') as file:
        json.dump(token, file, indent=4)
        print('Token saved in "token.json"')

    request.session['access_token'] = token['access_token']

    return redirect('app:success')

def get_user_info(access_token):
    url = 'https://api.myanimelist.net/v2/users/@me'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user_info = response.json()
        return user_info
    else:
        return None


def fetch_anime_data(request):
    # Fetch the anime data using the MyAnimeList API
    access_token = request.session.get('access_token')
    #refresh_token = request.session.get('refresh_token')
    url = 'https://api.myanimelist.net/v2/anime/{anime_id}?fields=title,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,status,genres,num_episodes,broadcast,average_episode_duration,rating,studios'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        "limit": 500,  # Fetching 100 anime per request
        "offsets": 38917,  # Starting from the first anime
    }

    #response = requests.get(url, headers=headers, params=params)

    try:
        total_anime_count = 0
        batch_size = 500
        iterations = 50
        for i in range(iterations):
            offset = i * batch_size + 38917
            for anime_id in range(offset + 1, offset + batch_size + 1):
                response = requests.get(url.format(anime_id=anime_id), headers=headers, params=params)
                if response.status_code == 404:
                    continue  # Anime not found, skip to the next ID

                response.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
                anime_data = response.json()

                # Connect to MongoDB
                client = MongoClient("mongodb://localhost:27017/")
                db = client['MyAnimeListDB']
                collection = db['anime_data']

                # Insert anime data into MongoDB
                result = collection.insert_one(anime_data)
                total_anime_count += 1
                time.sleep(10)
        return HttpResponse(f"Successfully fetched and saved {total_anime_count} anime to MongoDB.")

    except requests.exceptions.RequestException as e:
        return HttpResponse(f"Error occurred while making the API request: {str(e)}")

    except KeyError:
        return HttpResponse("Error: Invalid API response format. Check the endpoint URL and response structure.")

    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")



def success(request):
    access_token = request.session.get('access_token')
    refresh_token = request.session.get('refresh_token')
    
    if access_token and refresh_token:
        user_info = get_user_info(access_token)
        with open('user_info.json', 'w') as file:
            json.dump(user_info, file, indent=4)
        
        return render(request, 'success.html', {'user_info': user_info })

    else:
        return redirect('app:refresh')

