from pydantic import BaseModel
from typing import Optional

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None
    timezone: Optional[str] = None
