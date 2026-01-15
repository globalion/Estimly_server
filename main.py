from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from routes.auth import router as auth_router
from routes.projects import router as project_router
# from routes.templates import router as template_router
from internal.admin_built_in_templates import admin_built_in_templates_router



app = FastAPI(title="Estimly Backend")

app.include_router(auth_router, prefix="/api")
app.include_router(project_router, prefix="/api") 

# app.include_router(template_router, prefix="/api)
app.include_router(admin_built_in_templates_router)

