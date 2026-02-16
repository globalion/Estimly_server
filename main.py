from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from routes.auth import router as auth_router
from routes.user import router as user_router
from routes.company import router as company_router
from routes.projects import router as project_router
from routes.custom_templates import router as custom_template_router
from routes.dashboard import router as dashboard_router
from routes.built_in_templates import router as built_in_templates_router
from internal.admin_built_in_templates import admin_built_in_templates_router
from routes.estimation_techniques import router as estimation_techniques_router
from internal.admin_estimation_techniques import admin_estimation_techniques_router
from routes.social_auth import router as social_auth_router
from routes.resource_roles import router as resource_roles_router
from routes.estimation_calculate import router as estimation_calculate_router
from routes.invitation import router as invitation_router


app = FastAPI(title="Estimly Backend")

# CORS for separate frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        # "http://localhost:5000"
                # "https://app.yourdomain.com"  # production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 REQUIRED for Authlib OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key="YI_Ucjder1jd6H9M49K8nJ_siz9stRJ2OK-Lan8LDvo"
)


# Routes
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(company_router) 
app.include_router(project_router) 
app.include_router(dashboard_router)
app.include_router(built_in_templates_router)
app.include_router(custom_template_router)
app.include_router(estimation_calculate_router)
app.include_router(estimation_techniques_router)
app.include_router(admin_built_in_templates_router)
app.include_router(admin_estimation_techniques_router)
app.include_router(social_auth_router)
app.include_router(resource_roles_router)

app.include_router(invitation_router)

@app.get("/")
def health():
    return {"status": "ok"}



