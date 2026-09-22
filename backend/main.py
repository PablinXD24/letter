import os
import random
import firebase_admin
from firebase_admin import credentials, db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

# Inicializar Firebase Admin usando variáveis de ambiente do Render
cred_dict = {
    "type": "service_account",
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "token_uri": "https://oauth2.googleapis.com/token",
}

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.environ.get("FIREBASE_DATABASE_URL")
    })

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "3fd2be6f0c70a2a598f084ddfb75487c")

@app.get("/api/daily-recommendation")
def get_daily_recommendation():
    # 1. Buscar todos os filmes salvos na biblioteca do Firebase
    lib_ref = db.reference('library')
    library_data = lib_ref.get() or {}
    
    watched_movie_ids = set()
    genre_counter = {}

    for key, item in library_data.items():
        if item.get('type') == 'movie' and 'movie' in item:
            m = item['movie']
            watched_movie_ids.add(m.get('id'))
            # Se tivermos o ID do TMDB, podemos buscar os gêneros favoritos do usuário
    
    # 2. Escolher uma semente com base nos filmes assistidos ou pegar os populares/trending
    # Exemplo: Buscar recomendações baseadas no último filme avaliado ou em alta
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}&language=pt-BR"
    response = requests.get(url).json()
    results = response.get('results', [])

    # Filtrar filmes que o usuário ainda não assistiu
    available_movies = [m for m in results if m.get('id') not in watched_movie_ids]
    
    if not available_movies:
        available_movies = results # Fallback caso tenha assistido a tudo

    recommended = random.choice(available_movies) if available_movies else None

    if not recommended:
        return {"error": "Nenhum filme encontrado"}

    recommendation_payload = {
        "id": recommended.get('id'),
        "title": recommended.get('title'),
        "overview": recommended.get('overview'),
        "poster": f"https://image.tmdb.org/t/p/w500{recommended.get('poster_path')}",
        "year": recommended.get('release_date', '').split('-')[0],
        "vote_average": recommended.get('vote_average')
    }

    # Opcional: Salvar no Firebase para persistir o destaque diário
    db.reference('daily_recommendation').set(recommendation_payload)

    return recommendation_payload
