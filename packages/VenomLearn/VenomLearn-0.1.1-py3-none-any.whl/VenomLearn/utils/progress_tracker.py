"""Progress Tracker module for VenomLearn learning package.

This module tracks the user's progress through the learning journey.
"""

import os
import json
from VenomLearn.config import PROGRESS_FILE


class ProgressTracker:
    """Class to track user progress through the learning journey."""
    
    def __init__(self):
        """Initialize the progress tracker."""
        self.progress_file = PROGRESS_FILE
        self.progress_data = self._load_progress()
    
    def _load_progress(self):
        """Load progress data from file."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # If file is corrupted or doesn't exist, create a new one
                return self._create_default_progress()
        else:
            return self._create_default_progress()
    
    def _create_default_progress(self):
        """Create default progress data."""
        default_progress = {
            "completed_topics": [],
            "current_topic_index": 0,
            "badges": [],
            "xp": 0
        }
        
        # Save the default progress
        self._save_progress(default_progress)
        
        return default_progress
    
    def _save_progress(self, progress_data=None):
        """Save progress data to file."""
        if progress_data is None:
            progress_data = self.progress_data
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=4)
    
    def get_current_topic_index(self):
        """Get the current topic index."""
        return self.progress_data.get("current_topic_index", 0)
    
    def mark_topic_completed(self, topic_name):
        """Mark a topic as completed."""
        if topic_name not in self.progress_data["completed_topics"]:
            self.progress_data["completed_topics"].append(topic_name)
            self.progress_data["current_topic_index"] += 1
            self.progress_data["xp"] += 10  # Award XP for completing a topic
            
            # Check if user earned a badge
            self._check_badges()
            
            # Save progress
            self._save_progress()
    
    def _check_badges(self):
        """Check if user earned any badges."""
        from VenomLearn.config import BADGE_LEVELS
        
        completed_count = len(self.progress_data["completed_topics"])
        
        for badge, level in BADGE_LEVELS.items():
            if completed_count >= level and badge not in self.progress_data["badges"]:
                self.progress_data["badges"].append(badge)
                print(f"🎖️ Congratulations! You've earned the '{badge}' badge!")
    
    def get_progress_summary(self):
        """Get a summary of the user's progress."""
        completed_count = len(self.progress_data["completed_topics"])
        badges = self.progress_data["badges"]
        xp = self.progress_data["xp"]
        
        return {
            "completed_topics": completed_count,
            "badges": badges,
            "xp": xp
        }