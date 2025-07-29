"""
Learning session management and progress tracking
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import os


@dataclass
class LearningSession:
    """Represents a single learning session"""
    session_id: str
    concept_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    phase_completed: str = "study"
    notes: List[str] = field(default_factory=list)
    mastery_before: float = 0.0
    mastery_after: float = 0.0
    time_spent_minutes: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "concept_name": self.concept_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "phase_completed": self.phase_completed,
            "notes": self.notes,
            "mastery_before": self.mastery_before,
            "mastery_after": self.mastery_after,
            "time_spent_minutes": self.time_spent_minutes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LearningSession':
        return cls(
            session_id=data["session_id"],
            concept_name=data["concept_name"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data["end_time"] else None,
            phase_completed=data["phase_completed"],
            notes=data["notes"],
            mastery_before=data["mastery_before"],
            mastery_after=data["mastery_after"],
            time_spent_minutes=data["time_spent_minutes"]
        )


class SessionManager:
    """Manages learning sessions and progress tracking"""
    
    def __init__(self, storage_path: str = "learning_sessions.json"):
        self.storage_path = storage_path
        self.current_session: Optional[LearningSession] = None
        self.sessions: List[LearningSession] = []
        self.load_sessions()
    
    def start_session(self, concept_name: str, initial_mastery: float = 0.0) -> str:
        """Start a new learning session"""
        session_id = f"{concept_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = LearningSession(
            session_id=session_id,
            concept_name=concept_name,
            start_time=datetime.now(),
            mastery_before=initial_mastery
        )
        
        return session_id
    
    def add_note(self, note: str):
        """Add a note to the current session"""
        if self.current_session:
            self.current_session.notes.append(note)
    
    def update_phase(self, phase: str):
        """Update the current learning phase"""
        if self.current_session:
            self.current_session.phase_completed = phase
    
    def end_session(self, final_mastery: float = 0.0):
        """End the current learning session"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.mastery_after = final_mastery
            
            if self.current_session.end_time and self.current_session.start_time:
                time_diff = self.current_session.end_time - self.current_session.start_time
                self.current_session.time_spent_minutes = int(time_diff.total_seconds() / 60)
            
            self.sessions.append(self.current_session)
            self.save_sessions()
            self.current_session = None
    
    def get_concept_history(self, concept_name: str) -> List[LearningSession]:
        """Get learning history for a specific concept"""
        return [session for session in self.sessions if session.concept_name == concept_name]
    
    def get_recent_sessions(self, days: int = 7) -> List[LearningSession]:
        """Get sessions from the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [session for session in self.sessions if session.start_time >= cutoff_date]
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        if not self.sessions:
            return {
                "total_sessions": 0,
                "total_time_minutes": 0,
                "concepts_studied": 0,
                "average_session_time": 0,
                "mastery_improvement": 0.0,
                "most_studied_concept": None,
                "learning_streak_days": 0
            }
        
        total_sessions = len(self.sessions)
        total_time = sum(session.time_spent_minutes for session in self.sessions)
        concepts = set(session.concept_name for session in self.sessions)
        
        mastery_improvements = [
            session.mastery_after - session.mastery_before 
            for session in self.sessions 
            if session.mastery_after > 0
        ]
        avg_mastery_improvement = sum(mastery_improvements) / len(mastery_improvements) if mastery_improvements else 0.0
        
        concept_counts = {}
        for session in self.sessions:
            concept_counts[session.concept_name] = concept_counts.get(session.concept_name, 0) + 1
        
        most_studied = max(concept_counts.items(), key=lambda x: x[1])[0] if concept_counts else None
        
        streak = self._calculate_learning_streak()
        
        return {
            "total_sessions": total_sessions,
            "total_time_minutes": total_time,
            "concepts_studied": len(concepts),
            "average_session_time": total_time / total_sessions if total_sessions > 0 else 0,
            "mastery_improvement": avg_mastery_improvement,
            "most_studied_concept": most_studied,
            "learning_streak_days": streak,
            "concept_breakdown": concept_counts
        }
    
    def _calculate_learning_streak(self) -> int:
        """Calculate current learning streak in days"""
        if not self.sessions:
            return 0
        
        # Sort sessions by date
        sorted_sessions = sorted(self.sessions, key=lambda x: x.start_time, reverse=True)
        
        # Get unique days with sessions
        session_dates = set()
        for session in sorted_sessions:
            session_dates.add(session.start_time.date())
        
        sorted_dates = sorted(session_dates, reverse=True)
        
        if not sorted_dates:
            return 0
        
        # Check if today has a session
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        streak = 0
        current_date = today if today in sorted_dates else yesterday
        
        for date in sorted_dates:
            if date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def get_concept_progress(self, concept_name: str) -> Dict[str, Any]:
        """Get detailed progress for a specific concept"""
        concept_sessions = self.get_concept_history(concept_name)
        
        if not concept_sessions:
            return {
                "concept_name": concept_name,
                "sessions_count": 0,
                "total_time_minutes": 0,
                "current_mastery": 0.0,
                "mastery_trend": [],
                "phases_completed": [],
                "last_session": None
            }
        
        total_time = sum(session.time_spent_minutes for session in concept_sessions)
        mastery_trend = [(session.start_time.isoformat(), session.mastery_after) for session in concept_sessions if session.mastery_after > 0]
        phases = list(set(session.phase_completed for session in concept_sessions))
        latest_session = max(concept_sessions, key=lambda x: x.start_time)
        
        return {
            "concept_name": concept_name,
            "sessions_count": len(concept_sessions),
            "total_time_minutes": total_time,
            "current_mastery": latest_session.mastery_after,
            "mastery_trend": mastery_trend,
            "phases_completed": phases,
            "last_session": latest_session.start_time.isoformat()
        }
    
    def suggest_next_session(self) -> Dict[str, Any]:
        """Suggest what to study next based on history"""
        if not self.sessions:
            return {"suggestion": "Start with a new concept", "reason": "No previous sessions found"}
        
        # Find concepts that need more work (low mastery or not studied recently)
        concept_mastery = {}
        concept_last_studied = {}
        
        for session in self.sessions:
            concept = session.concept_name
            if session.mastery_after > 0:
                concept_mastery[concept] = session.mastery_after
            concept_last_studied[concept] = max(
                concept_last_studied.get(concept, session.start_time),
                session.start_time
            )
        
        # Find concepts with low mastery
        low_mastery_concepts = [
            concept for concept, mastery in concept_mastery.items() 
            if mastery < 0.7
        ]
        
        # Find concepts not studied in the last week
        week_ago = datetime.now() - timedelta(days=7)
        neglected_concepts = [
            concept for concept, last_studied in concept_last_studied.items()
            if last_studied < week_ago
        ]
        
        if low_mastery_concepts:
            suggestion = f"Continue working on {low_mastery_concepts[0]}"
            reason = f"Mastery level is {concept_mastery[low_mastery_concepts[0]]:.1f}"
        elif neglected_concepts:
            suggestion = f"Review {neglected_concepts[0]}"
            reason = "Not studied recently"
        else:
            suggestion = "Start a new concept or review existing ones"
            reason = "All concepts are well-mastered and recently studied"
        
        return {
            "suggestion": suggestion,
            "reason": reason,
            "low_mastery_concepts": low_mastery_concepts,
            "neglected_concepts": neglected_concepts
        }
    
    def save_sessions(self):
        """Save sessions to file"""
        try:
            data = [session.to_dict() for session in self.sessions]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")
    
    def load_sessions(self):
        """Load sessions from file"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.sessions = [LearningSession.from_dict(session_data) for session_data in data]
        except Exception as e:
            print(f"Error loading sessions: {e}")
            self.sessions = []
    
    def export_progress_report(self, output_path: str = "learning_report.json") -> str:
        """Export a comprehensive progress report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": self.get_learning_statistics(),
            "concept_progress": {},
            "recent_sessions": []
        }
        
        # Add concept progress for all studied concepts
        concepts = set(session.concept_name for session in self.sessions)
        for concept in concepts:
            report["concept_progress"][concept] = self.get_concept_progress(concept)
        
        # Add recent sessions
        recent = self.get_recent_sessions(30)  # Last 30 days
        report["recent_sessions"] = [session.to_dict() for session in recent]
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_path