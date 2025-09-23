from pydantic import BaseModel, Field
from typing import TypedDict, Optional, List, Dict, Any, Union

class SentimentScore(BaseModel):
    pos: float = Field(description="Positive sentiment score (0.0-1.0)", ge=0.0, le=1.0)
    neg: float = Field(description="Negative sentiment score (0.0-1.0)", ge=0.0, le=1.0) 
    neu: float = Field(description="Neutral sentiment score (0.0-1.0)", ge=0.0, le=1.0)
    context_type: str = Field(description="Context: personal|general|question|academic")
    personal_relevance: float = Field(description="Personal relevance (0.0-1.0)", ge=0.0, le=1.0)
    

class FilteredResult(BaseModel):
    id: str = Field(description="Document ID")
    similarity: float = Field(description="Similarity score", ge=0.0, le=1.0)
    status: str = Field(description="Status/label of the document")
    text: str = Field(description="Text content", max_length=350)
    
# Schema for label generator
class FilterCategory(BaseModel):
    category: str = Field(description="One category: research|report|conversation|article")
    
     
# Schema for document grading
class DocumentGrade(BaseModel):
    id: str = Field(description="Document ID")
    grade: int = Field(description="Relevance grade 1-100", ge=1, le=100)

class GradingDocument(BaseModel):
    grades: List[DocumentGrade] = Field(description="List of document grades")
    
# Schema for evaluation response
class EvaluationResponse(BaseModel):
    score: int = Field(description="Response quality score 0-100", ge=0, le=100)
    feedback: str = Field(description="Improvement feedback (under 200 words)")