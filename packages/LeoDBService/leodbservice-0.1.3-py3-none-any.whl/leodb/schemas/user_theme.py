import uuid
from pydantic import BaseModel, Field
from typing import List

# --- Schemas for reading user configuration ---

class UserThemeIndicatorSchema(BaseModel):
    indicator_key: str

    class Config:
        orm_mode = True

class UserThemeSchema(BaseModel):
    theme_key: str
    indicators: List[UserThemeIndicatorSchema]

    class Config:
        orm_mode = True

class UserConfigurationResponse(BaseModel):
    themes: List[UserThemeSchema]

# --- Schemas for creating/updating user configuration ---

class SelectedIndicator(BaseModel):
    indicator_key: str

class SelectedTheme(BaseModel):
    theme_key: str
    indicators: List[SelectedIndicator]

class UserConfigurationCreate(BaseModel):
    user_id: uuid.UUID
    themes: List[SelectedTheme]