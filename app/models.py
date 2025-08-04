# app/models.py

from pydantic import BaseModel
from typing import Optional

class UserInput(BaseModel):
    name: str
    birthdate: str
    dream: Optional[str] = None
