"""
Base Agent Class - Abstract interface for all agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the orchestration system.
    Defines the interface that all agents must implement.
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """
        Initialize base agent.
        
        Args:
            model_name (str): LLM model to use (default: Gemini 1.5 Flash)
        """
        self.model_name = model_name
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Main execution method - must be implemented by subclasses.
        
        Returns:
            Dict with keys:
                - "success" (bool): Whether execution was successful
                - "model" (str): LLM model used
                - "error" (str, optional): Error message if failed
                - Additional agent-specific keys
        """
        pass
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data before processing.
        Override in subclasses for specific validation.
        
        Args:
            input_data: Data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return True
    
    def format_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format output to standard structure.
        
        Args:
            data (Dict): Raw output from agent
            
        Returns:
            Dict: Standardized output with required keys
        """
        if "success" not in data:
            data["success"] = True
        if "model" not in data:
            data["model"] = self.model_name
        return data
