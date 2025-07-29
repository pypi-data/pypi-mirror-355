"""
AI-powered explanation and learning assistance
"""

from typing import List, Dict, Optional
import json
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        pass


class OpenAICompatibleProvider(AIProvider):
    """OpenAI-compatible provider for OpenAI and custom endpoints (e.g., local models, vLLM, etc.)"""
    
    def __init__(
        self, 
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        timeout: Optional[float] = None,
        organization: Optional[str] = None
    ):
        """
        Initialize OpenAI-compatible provider
        
        Args:
            api_key: API key (required for OpenAI, can be dummy for local endpoints)
            base_url: Base URL of the API endpoint (defaults to OpenAI)
            model: Model name to use
            timeout: Request timeout in seconds
            organization: Organization ID (for OpenAI)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.organization = organization
        
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                organization=self.organization
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            return "OpenAI library not installed. Run: pip install openai"
        except Exception as e:
            return f"Error generating response: {str(e)}"





class AIExplainer:
    """AI-powered learning assistant using the Feynman Technique"""
    
    def __init__(self, provider: AIProvider):
        self.provider = provider
        
    def enhance_understanding(self, content: str) -> str:
        """Enhance understanding of the content with AI assistance"""
        prompt = f"""
        Help me understand this concept better by providing:
        1. Key points and main ideas
        2. Real-world examples
        3. Common misconceptions to avoid
        4. Prerequisites I should know
        
        Content: {content}
        
        Please provide a comprehensive but concise explanation.
        """
        
        return self.provider.generate_response(prompt, max_tokens=800)
    
    def generate_simple_explanation(self, content: str, target_audience: str = "beginner") -> str:
        """Generate a simple explanation using the Feynman Technique"""
        prompt = f"""
        Using the Feynman Technique, explain this concept as if you're teaching a {target_audience}.
        Use simple language, analogies, and avoid jargon. Break it down into digestible pieces.
        
        Content: {content}
        
        Requirements:
        - Use everyday language
        - Include analogies or metaphors
        - Break complex ideas into smaller parts
        - Make it engaging and easy to understand
        """
        
        return self.provider.generate_response(prompt, max_tokens=600)
    
    def identify_gaps(self, original_content: str, explanations: List[str]) -> List[str]:
        """Identify knowledge gaps in the explanations"""
        explanations_text = "\n\n".join(explanations)
        
        prompt = f"""
        Compare the original content with the simplified explanations and identify knowledge gaps.
        What important concepts or details are missing from the explanations?
        
        Original Content: {original_content}
        
        Simplified Explanations: {explanations_text}
        
        Please list specific gaps or missing elements that should be addressed.
        Format as a JSON array of strings.
        """
        
        response = self.provider.generate_response(prompt, max_tokens=400)
        
        try:
            gaps = json.loads(response)
            return gaps if isinstance(gaps, list) else [response]
        except json.JSONDecodeError:
            return [line.strip() for line in response.split('\n') if line.strip()]
    
    def improve_explanation(self, content: str, gaps: List[str]) -> str:
        """Improve explanation by addressing identified gaps"""
        gaps_text = "\n".join([f"- {gap}" for gap in gaps])
        
        prompt = f"""
        Improve this explanation by addressing the following identified gaps.
        Maintain simple language while ensuring completeness.
        
        Original Content: {content}
        
        Gaps to Address:
        {gaps_text}
        
        Provide an improved explanation that covers these gaps while staying accessible.
        """
        
        return self.provider.generate_response(prompt, max_tokens=700)
    
    def assess_mastery(self, concept) -> float:
        """Assess mastery level based on explanations and gaps"""
        explanations_count = len(concept.simplified_explanations)
        gaps_count = len(concept.gaps_identified)
        
        prompt = f"""
        Assess the mastery level for this learning concept on a scale of 0.0 to 1.0.
        
        Concept: {concept.name}
        Original Content: {concept.content}
        Number of Explanations: {explanations_count}
        Number of Gaps Identified: {gaps_count}
        Latest Explanation: {concept.simplified_explanations[-1] if concept.simplified_explanations else "None"}
        
        Consider:
        - Quality of explanations
        - Number of remaining gaps
        - Clarity and simplicity
        - Completeness
        
        Return only a decimal number between 0.0 and 1.0.
        """
        
        response = self.provider.generate_response(prompt, max_tokens=50)
        
        try:
            score = float(response.strip())
            return max(0.0, min(1.0, score))  # Clamp between 0 and 1
        except ValueError:
            # Fallback scoring based on simple heuristics
            base_score = 0.3 if explanations_count > 0 else 0.1
            explanation_bonus = min(0.4, explanations_count * 0.2)
            gap_penalty = min(0.3, gaps_count * 0.1)
            
            return max(0.0, min(1.0, base_score + explanation_bonus - gap_penalty))
    
    def generate_quiz_questions(self, content: str, difficulty: str = "medium") -> List[Dict]:
        """Generate quiz questions to test understanding"""
        prompt = f"""
        Create 3-5 quiz questions based on this content to test understanding.
        Difficulty level: {difficulty}
        
        Content: {content}
        
        Format as JSON array with objects containing:
        - "question": the question text
        - "type": "multiple_choice", "short_answer", or "explanation"
        - "answer": correct answer or key points
        - "options": array of choices (for multiple choice only)
        """
        
        response = self.provider.generate_response(prompt, max_tokens=600)
        
        try:
            questions = json.loads(response)
            return questions if isinstance(questions, list) else []
        except json.JSONDecodeError:
            return [{"question": "Explain the main concept in your own words", "type": "explanation", "answer": "Various valid explanations possible"}]
    
    def suggest_related_topics(self, content: str) -> List[str]:
        """Suggest related topics for further learning"""
        prompt = f"""
        Based on this content, suggest 3-5 related topics that would be good to learn next.
        Consider both prerequisites and advanced topics.
        
        Content: {content}
        
        Format as a JSON array of strings.
        """
        
        response = self.provider.generate_response(prompt, max_tokens=300)
        
        try:
            topics = json.loads(response)
            return topics if isinstance(topics, list) else [response]
        except json.JSONDecodeError:
            return [line.strip() for line in response.split('\n') if line.strip()]