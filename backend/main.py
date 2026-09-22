import os
import json
import random
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, db

# Inicialização do Firebase Admin no Render via Variável de Ambiente
if not firebase_admin._apps:
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # Fallback local se estiver testando na sua máquina com o arquivo JSON na pasta
        firebase_cred_path = "serviceAccountKey.json"
        if os.path.exists(firebase_cred_path):
            cred = credentials.Certificate(firebase_cred_path)
        else:
            raise ValueError("As credenciais do Firebase não foram encontradas nas variáveis de ambiente nem localmente.")
    
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") # Chave da API do Google Gemini

@app.get("/")
def read_root():
    return {"status": "online", "message": "API do CineMozi rodando com sucesso no Render!"}

@app.post("/api/update-daily-recommendation")
def trigger_daily_recommendation():
    """Atualiza a recomendação diária de filme utilizando dados do TMDB."""
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
