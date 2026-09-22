import os
import random
import time
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    """Atualiza a recomendação diária de filme utilizando dados do TMDB e gravando no Firebase via REST."""
    try:
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=pt-BR&page=1"
        response = requests.get(url)
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            raise HTTPException(status_code=404, detail="Nenhum filme encontrado no TMDB.")
        
        movie = random.choice(results[:10])
        
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
            "message": "Recomendação diária atualizada com sucesso!", 
            "movie": recommendation_data["title"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
