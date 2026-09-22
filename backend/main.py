import os
import random
import time
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="CineMozi Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "3fd2be6f0c70a2a598f084ddfb75487c")
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "https://letter-76c0a-default-rtdb.firebaseio.com").rstrip("/")

@app.get("/")
def read_root():
    return {"status": "online", "message": "API do CineMozi rodando com sucesso no Render!"}

@app.post("/api/update-daily-recommendation")
def trigger_daily_recommendation():
    """Atualiza a recomendação diária de filme utilizando dados do TMDB estritamente já lançados (em cartaz/streaming) e gravando no Firebase via REST."""
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Buscamos filmes que já estrearam (com data de lançamento menor ou igual à data atual)
        url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&language=pt-BR&sort_by=popularity.desc&primary_release_date.lte={current_date}&page=1"
        response = requests.get(url)
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            raise HTTPException(status_code=404, detail="Nenhum filme disponível encontrado no TMDB.")
        
        # Filtro de segurança adicional para garantir que não haja datas futuras
        available_movies = []
        for m in results:
            release_date = m.get("release_date")
            if release_date and release_date <= current_date and m.get("poster_path"):
                available_movies.append(m)
        
        if not available_movies:
            available_movies = results # Fallback caso a lista venha vazia

        movie = random.choice(available_movies[:10])
        
        recommendation_data = {
            "id": movie.get("id"),
            "title": movie.get("title"),
            "overview": movie.get("overview"),
            "year": movie.get("release_date", "2026").split("-")[0],
            "poster": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}",
            "updatedAt": int(time.time() * 1000)
        }
        
        # Envio direto via REST API do Firebase Realtime Database
        firebase_url = f"{FIREBASE_DATABASE_URL}/daily_recommendation.json"
        fb_response = requests.put(firebase_url, json=recommendation_data)
        
        if fb_response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Erro ao salvar no Firebase: {fb_response.text}")
        
        return {
            "success": True, 
            "message": "Recomendação diária atualizada com sucesso (apenas lançados/disponíveis)!", 
            "movie": recommendation_data["title"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
