from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.projects import router as project_router
# from routes.templates import router as template_router
from routes.built_in_templates import router as built_in_templates_router
from internal.admin_built_in_templates import admin_built_in_templates_router

app = FastAPI(title="Estimly Backend")

# CORS for separate frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5000"
        # "https://app.yourdomain.com"  # production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router)
app.include_router(project_router) 

# app.include_router(template_router)
app.include_router(built_in_templates_router)
app.include_router(admin_built_in_templates_router)

