"""
Review progress tracking.

This module provides utilities for tracking the progress of review steps.
"""

from enum import Enum
from typing import Dict, List, Optional, Any


class ReviewStepStatus(Enum):
    """Status of a review step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ReviewProgress:
    """
    Tracks the progress of review steps.
    
    This class provides utilities for tracking and updating the progress
    of review steps during a code review.
    """
    
    def __init__(self):
        """Initialize the review progress tracker."""
        self.step_statuses: Dict[str, ReviewStepStatus] = {}
        self.step_times: Dict[str, Dict[str, float]] = {}
        self.current_step: Optional[str] = None
    
    def register_step(self, step_id: str) -> None:
        """
        Register a review step for progress tracking.
        
        Args:
            step_id: ID of the review step to register
        """
        if step_id not in self.step_statuses:
            self.step_statuses[step_id] = ReviewStepStatus.PENDING
            self.step_times[step_id] = {
                "start_time": 0.0,
                "end_time": 0.0,
                "duration": 0.0
            }
    
    def register_steps(self, step_ids: List[str]) -> None:
        """
        Register multiple review steps for progress tracking.
        
        Args:
            step_ids: List of review step IDs to register
        """
        for step_id in step_ids:
            self.register_step(step_id)
    
    def start_step(self, step_id: str) -> None:
        """
        Mark a review step as in progress.
        
        Args:
            step_id: ID of the review step to start
        """
        import time
        
        if step_id not in self.step_statuses:
            self.register_step(step_id)
        
        self.step_statuses[step_id] = ReviewStepStatus.IN_PROGRESS
        self.step_times[step_id]["start_time"] = time.time()
        self.current_step = step_id
    
    def complete_step(self, step_id: str) -> None:
        """
        Mark a review step as completed.
        
        Args:
            step_id: ID of the review step to complete
        """
        import time
        
        if step_id not in self.step_statuses:
            self.register_step(step_id)
        
        self.step_statuses[step_id] = ReviewStepStatus.COMPLETED
        self.step_times[step_id]["end_time"] = time.time()
        self.step_times[step_id]["duration"] = (
            self.step_times[step_id]["end_time"] - self.step_times[step_id]["start_time"]
        )
        
        if self.current_step == step_id:
            self.current_step = None
    
    def fail_step(self, step_id: str) -> None:
        """
        Mark a review step as failed.
        
        Args:
            step_id: ID of the review step that failed
        """
        import time
        
        if step_id not in self.step_statuses:
            self.register_step(step_id)
        
        self.step_statuses[step_id] = ReviewStepStatus.FAILED
        self.step_times[step_id]["end_time"] = time.time()
        self.step_times[step_id]["duration"] = (
            self.step_times[step_id]["end_time"] - self.step_times[step_id]["start_time"]
        )
        
        if self.current_step == step_id:
            self.current_step = None
    
    def skip_step(self, step_id: str) -> None:
        """
        Mark a review step as skipped.
        
        Args:
            step_id: ID of the review step to skip
        """
        if step_id not in self.step_statuses:
            self.register_step(step_id)
        
        self.step_statuses[step_id] = ReviewStepStatus.SKIPPED
    
    def get_step_status(self, step_id: str) -> ReviewStepStatus:
        """
        Get the status of a review step.
        
        Args:
            step_id: ID of the review step
        
        Returns:
            Status of the review step
        """
        if step_id not in self.step_statuses:
            self.register_step(step_id)
        
        return self.step_statuses[step_id]
    
    def get_step_duration(self, step_id: str) -> float:
        """
        Get the duration of a review step in seconds.
        
        Args:
            step_id: ID of the review step
        
        Returns:
            Duration of the review step in seconds
        """
        if step_id not in self.step_times:
            return 0.0
        
        return self.step_times[step_id]["duration"]
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the review progress.
        
        Returns:
            Dictionary containing the progress summary
        """
        total_steps = len(self.step_statuses)
        completed_steps = sum(1 for status in self.step_statuses.values() 
                             if status == ReviewStepStatus.COMPLETED)
        in_progress_steps = sum(1 for status in self.step_statuses.values() 
                               if status == ReviewStepStatus.IN_PROGRESS)
        failed_steps = sum(1 for status in self.step_statuses.values() 
                          if status == ReviewStepStatus.FAILED)
        skipped_steps = sum(1 for status in self.step_statuses.values() 
                           if status == ReviewStepStatus.SKIPPED)
        pending_steps = sum(1 for status in self.step_statuses.values() 
                           if status == ReviewStepStatus.PENDING)
        
        # Calculate total duration of completed steps
        total_duration = sum(self.step_times[step_id]["duration"] 
                            for step_id in self.step_statuses 
                            if self.step_statuses[step_id] in 
                            [ReviewStepStatus.COMPLETED, ReviewStepStatus.FAILED])
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "in_progress_steps": in_progress_steps,
            "failed_steps": failed_steps,
            "skipped_steps": skipped_steps,
            "pending_steps": pending_steps,
            "progress_percentage": (completed_steps + skipped_steps) / total_steps * 100 if total_steps > 0 else 0,
            "total_duration": total_duration,
            "current_step": self.current_step,
        }
    
    def reset(self) -> None:
        """Reset the progress tracker."""
        self.step_statuses = {}
        self.step_times = {}
        self.current_step = None
