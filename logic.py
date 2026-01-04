import random
import json
import os

class ExperimentManager:
    def __init__(self):
        self.session_id = f"sess_{random.randint(10000, 99999)}"
        
    def log_assignment(self, condition):
        print(f"Session {self.session_id} assigned to condition: {condition}")

class ScriptManager:
    def __init__(self, script_path="script.json"):
        # Load script from JSON file
        try:
            with open(script_path, "r") as f:
                self.script = json.load(f)
        except Exception as e:
            print(f"Error loading script: {e}")
            self.script = []
            
    def get_total_steps(self):
        return len(self.script)

    def get_step(self, index, condition):
        """
        Returns the step data for the given index.
        Includes resolved text for the condition.
        """
        if index >= len(self.script):
            return None
            
        step_raw = self.script[index]
        
        # Resolve text based on condition
        text_variation = step_raw.get("text", {})
        # Fallback to High_Empathy if condition key missing, or just use the whole object if it's a string
        if isinstance(text_variation, dict):
            resolved_text = text_variation.get(condition, text_variation.get("High_Empathy", ""))
        else:
            resolved_text = str(text_variation)
            
        return {
            "id": step_raw.get("id"),
            "type": step_raw.get("type"),
            "text": resolved_text,
            "image": step_raw.get("image", None)
        }
