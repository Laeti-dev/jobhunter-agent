from pydantic import BaseModel, Field
from typing import List, Optional


class Experience(BaseModel):
    company: str
    title: str
    location: str
    start_date: str
    end_date: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    keywords: List[str]

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_date: str
    end_date: Optional[str] = None
    achievements: List[str]
    keywords: List[str]

class CVProfile(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    city: str
    zip: str
    linkedin: str
    github: str
    website: Optional[str] = None
    summary: str
    target_role: str
    spoken_languages: List[str]
    output_language: str = Field(default="fr")
    experiences: List[Experience]
    education: List[Education]
    certifications: Optional[List[str]] = None
    tech_skills: List[str]
    soft_skills: Optional[List[str]] = None
