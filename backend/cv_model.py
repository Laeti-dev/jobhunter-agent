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

class Project(BaseModel):
    title: str
    description: str
    technologies: List[str] = Field(default_factory=list)


class Identity(BaseModel):
    name: str
    email: str
    phone: str
    city: str
    target_role: str


class SkillsSection(BaseModel):
    tech_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)


class LanguagesSection(BaseModel):
    spoken_languages: List[str] = Field(default_factory=list)


class CVProfile(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    summary: str
    target_role: str
    spoken_languages: List[str] = Field(default_factory=list)
    output_language: str = Field(default="fr")
    experiences: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: Optional[List[str]] = None
    tech_skills: List[str] = Field(default_factory=list)
    soft_skills: Optional[List[str]] = None
    projects: List[Project] = Field(default_factory=list)
