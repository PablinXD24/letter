import os
import random
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, db

# Inicialização do Firebase Admin usando variáveis de ambiente do Render ou arquivo local
if not firebase_admin._apps:
    firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
    if os.path.exists(firebase_cred_path):
        cred = credentials.Certificate(firebase_cred_path)
    else:
        cred = credentials.ApplicationDefault()
    
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv("FIREBASE_DATABASE_URL", "https://letter-76c0a-default-rtdb.firebaseio.com")
    })

app = FastAPI(title="CineMozi Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "3fd2be6f0c70a2a598f084ddfb75487c")

@app.get("/")
def read_root():
    return {"status": "online", "message": "API do CineMozi rodando com sucesso no Render!"}

@app.post("/api/update-daily-recommendation")
def trigger_daily_recommendation():
    """Endpoint para atualizar a recomendação diária de filme baseada em populares do TMDB."""
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
            "updatedAt": db.SERVER_TIMESTAMP
        }
        
        ref = db.reference("daily_recommendation")
        ref.set(recommendation_data)
        
        return {
            "success": True, 
            "message": "Recomendação diária atualizada com sucesso!", 
            "movie": recommendation_data["title"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
