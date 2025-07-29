"""
Core Feynman Learning implementation
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class LearningPhase(Enum):
    STUDY = "study"
    EXPLAIN = "explain"
    IDENTIFY_GAPS = "identify_gaps"
    SIMPLIFY = "simplify"
    REVIEW = "review"


@dataclass
class LearningConcept:
    name: str
    content: str
    complexity_level: int = 1
    mastery_score: float = 0.0
    gaps_identified: List[str] = None
    simplified_explanations: List[str] = None
    
    def __post_init__(self):
        if self.gaps_identified is None:
            self.gaps_identified = []
        if self.simplified_explanations is None:
            self.simplified_explanations = []


class FeynmanLearner:
    """Main class implementing the Feynman Technique for learning"""
    
    def __init__(self, ai_explainer=None):
        self.concepts: Dict[str, LearningConcept] = {}
        self.current_phase = LearningPhase.STUDY
        self.ai_explainer = ai_explainer
        
    def add_concept(self, name: str, content: str, complexity_level: int = 1) -> LearningConcept:
        """Add a new concept to learn"""
        concept = LearningConcept(
            name=name,
            content=content,
            complexity_level=complexity_level
        )
        self.concepts[name] = concept
        return concept
    
    def study_concept(self, concept_name: str) -> str:
        """Phase 1: Study the concept"""
        if concept_name not in self.concepts:
            raise ValueError(f"Concept '{concept_name}' not found")
        
        self.current_phase = LearningPhase.STUDY
        concept = self.concepts[concept_name]
        
        if self.ai_explainer:
            enhanced_content = self.ai_explainer.enhance_understanding(concept.content)
            concept.content = enhanced_content
        
        return concept.content
    
    def explain_concept(self, concept_name: str, target_audience: str = "beginner") -> str:
        """Phase 2: Explain the concept in simple terms"""
        if concept_name not in self.concepts:
            raise ValueError(f"Concept '{concept_name}' not found")
        
        self.current_phase = LearningPhase.EXPLAIN
        concept = self.concepts[concept_name]
        
        if self.ai_explainer:
            explanation = self.ai_explainer.generate_simple_explanation(
                concept.content, target_audience
            )
            concept.simplified_explanations.append(explanation)
            return explanation
        
        return f"Please explain '{concept_name}' in simple terms for a {target_audience}"
    
    def identify_knowledge_gaps(self, concept_name: str) -> List[str]:
        """Phase 3: Identify gaps in understanding"""
        if concept_name not in self.concepts:
            raise ValueError(f"Concept '{concept_name}' not found")
        
        self.current_phase = LearningPhase.IDENTIFY_GAPS
        concept = self.concepts[concept_name]
        
        if self.ai_explainer:
            gaps = self.ai_explainer.identify_gaps(concept.content, concept.simplified_explanations)
            concept.gaps_identified.extend(gaps)
            return gaps
        
        return []
    
    def improve_explanation(self, concept_name: str) -> str:
        """Phase 4: Improve and simplify explanation"""
        if concept_name not in self.concepts:
            raise ValueError(f"Concept '{concept_name}' not found")
        
        self.current_phase = LearningPhase.SIMPLIFY
        concept = self.concepts[concept_name]
        
        if self.ai_explainer and concept.gaps_identified:
            improved = self.ai_explainer.improve_explanation(
                concept.content, concept.gaps_identified
            )
            concept.simplified_explanations.append(improved)
            return improved
        
        return "Review your explanation and address any gaps identified"
    
    def review_concept(self, concept_name: str) -> Dict:
        """Phase 5: Review and assess mastery"""
        if concept_name not in self.concepts:
            raise ValueError(f"Concept '{concept_name}' not found")
        
        self.current_phase = LearningPhase.REVIEW
        concept = self.concepts[concept_name]
        
        if self.ai_explainer:
            mastery_score = self.ai_explainer.assess_mastery(concept)
            concept.mastery_score = mastery_score
        
        return {
            "concept": concept_name,
            "mastery_score": concept.mastery_score,
            "gaps_count": len(concept.gaps_identified),
            "explanations_count": len(concept.simplified_explanations),
            "next_steps": self._get_next_steps(concept)
        }
    
    def _get_next_steps(self, concept: LearningConcept) -> List[str]:
        """Suggest next steps based on current progress"""
        steps = []
        
        if concept.mastery_score < 0.7:
            steps.append("Continue studying the core material")
        
        if len(concept.gaps_identified) > 0:
            steps.append("Address identified knowledge gaps")
        
        if len(concept.simplified_explanations) < 2:
            steps.append("Practice explaining in different ways")
        
        if concept.mastery_score >= 0.8:
            steps.append("Move to more advanced topics or teach others")
        
        return steps
    
    def get_learning_progress(self) -> Dict:
        """Get overall learning progress"""
        total_concepts = len(self.concepts)
        if total_concepts == 0:
            return {"total_concepts": 0, "average_mastery": 0.0}
        
        total_mastery = sum(c.mastery_score for c in self.concepts.values())
        average_mastery = total_mastery / total_concepts
        
        return {
            "total_concepts": total_concepts,
            "average_mastery": average_mastery,
            "concepts_mastered": len([c for c in self.concepts.values() if c.mastery_score >= 0.8]),
            "current_phase": self.current_phase.value
        }