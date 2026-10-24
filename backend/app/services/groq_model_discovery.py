"""
Groq Model Discovery Service

Automatically discovers available Groq models, selects compatible models,
and manages model lifecycle with caching and failover support.
"""

import os
import logging
import httpx
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

GROQ_MODELS_ENDPOINT = "https://api.groq.com/openai/v1/models"
MODEL_DISCOVERY_CACHE_TTL = timedelta(hours=1)

# Preferred models in order of preference for structured itinerary generation
# Note: Only models with explicit json_schema support should be in this list
PREFERRED_MODELS = [
    "openai/gpt-oss-20b",  # Current strict-schema compatible model with bounded reasoning overhead.
    "qwen/qwen3.8-27b",  # Supports structured output (json_schema)
    "llama-3.3-70b-versatile",  # Supports structured output
    "llama-3.1-70b-versatile",  # Supports structured output
    "allam-2-7b",  # Fallback if no schema support available
]

# Models known to work well with structured JSON output (json_schema support)
COMPATIBLE_MODEL_PATTERNS = [
    "llama-3",
    "qwen",  # Qwen supports structured output
    "allam",  # Allam as fallback
    "openai/gpt-oss-20b",  # Strict structured output without the 120B reasoning-token issue.
]

# Models to explicitly exclude (too small, specialized, or problematic)
EXCLUDE_PATTERNS = [
    "prompt-guard",
    "whisper",
    "embeddings",
    "3b-",  # Too small for complex itineraries
    "mixtral",  # Older model, may not have schema support
]

# Models known to have issues with extended reasoning or structured output
AVOID_MODELS = [
    "openai/gpt-oss-120b",  # Uses extended thinking, exhausts tokens on reasoning
]

# Models with explicit json_schema support
SCHEMA_SUPPORTED_MODELS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
]


@dataclass
class ModelInfo:
    """Information about an available Groq model."""
    id: str
    owned_by: str
    created: int
    object: str = "model"
    active: bool = True  # Some models may have this field
    
    def __post_init__(self):
        """Normalize the model after initialization."""
        pass
    
    def is_compatible(self) -> bool:
        """Check if model is compatible with chat completions."""
        model_id_lower = self.id.lower()
        
        # Filter out models with known issues
        for avoid_pattern in AVOID_MODELS:
            if avoid_pattern.lower() in model_id_lower:
                return False
        
        # Filter out explicitly excluded patterns
        for exclude in EXCLUDE_PATTERNS:
            if exclude.lower() in model_id_lower:
                return False
        
        # Accept only models with known good patterns
        for pattern in COMPATIBLE_MODEL_PATTERNS:
            if pattern.lower() in model_id_lower:
                return True
        
        return False
    
    def is_preferred(self) -> bool:
        """Check if model is in the preferred models list."""
        return self.id in PREFERRED_MODELS


@dataclass
class ModelDiscoveryResult:
    """Result of model discovery operation."""
    available_models: List[ModelInfo]
    selected_model: Optional[str]
    discovery_timestamp: datetime
    error: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if discovery was successful and a model was selected."""
        return self.error is None and self.selected_model is not None


class GroqModelDiscovery:
    """
    Manages Groq model discovery, selection, and caching.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize model discovery service."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self._cache: Optional[ModelDiscoveryResult] = None
        self._cache_timestamp: Optional[datetime] = None
        self._selected_model: Optional[str] = None
    
    def get_selected_model(self, force_refresh: bool = False) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the selected model ID and any associated reason/error message.
        
        Args:
            force_refresh: Force discovery even if cached
        
        Returns:
            Tuple of (model_id, reason/error) where model_id is None if no model available
        """
        if not force_refresh and self._selected_model:
            return self._selected_model, None
        
        if not self.api_key:
            reason = "GROQ_API_KEY not configured"
            logger.warning(f"Model discovery: {reason}")
            return None, reason
        
        # Use cache if available and not expired
        if not force_refresh and self._cache and self._is_cache_valid():
            if self._cache.is_valid():
                return self._cache.selected_model, None
            elif self._cache.error:
                return None, self._cache.error
        
        # Discover models
        result = self._discover_models()
        self._cache = result
        self._cache_timestamp = datetime.now()
        
        if result.is_valid():
            self._selected_model = result.selected_model
            logger.info(f"Model discovery successful: selected {result.selected_model}")
            logger.info(f"Available compatible models: {[m.id for m in result.available_models if m.is_compatible()]}")
            return result.selected_model, None
        else:
            reason = result.error or "No compatible models found"
            logger.warning(f"Model discovery failed: {reason}")
            return None, reason
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache_timestamp:
            return False
        age = datetime.now() - self._cache_timestamp
        return age < MODEL_DISCOVERY_CACHE_TTL
    
    def _discover_models(self) -> ModelDiscoveryResult:
        """
        Discover available Groq models.
        
        Returns:
            ModelDiscoveryResult with discovered models and selected model
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    GROQ_MODELS_ENDPOINT,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                
                if response.status_code != 200:
                    error_msg = f"Groq API returned {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg = error_data["error"].get("message", error_msg)
                    except:
                        pass
                    
                    return ModelDiscoveryResult(
                        available_models=[],
                        selected_model=None,
                        discovery_timestamp=datetime.now(),
                        error=error_msg
                    )
                
                data = response.json()
                models_data = data.get("data", [])
                models = []
                
                for m in models_data:
                    # Extract only the fields we need, ignore extras
                    model_info = ModelInfo(
                        id=m.get("id", ""),
                        owned_by=m.get("owned_by", "groq"),
                        created=m.get("created", 0),
                        object=m.get("object", "model")
                    )
                    models.append(model_info)
                
                # Filter compatible models
                compatible = [m for m in models if m.is_compatible()]
                
                if not compatible:
                    return ModelDiscoveryResult(
                        available_models=models,
                        selected_model=None,
                        discovery_timestamp=datetime.now(),
                        error=f"No compatible models found. Available: {[m.id for m in models[:5]]}"
                    )
                
                # Select model: prefer list, then by creation date (newer is better)
                selected = self._select_model(compatible)
                
                logger.debug(f"Model discovery: found {len(models)} total, {len(compatible)} compatible")
                
                return ModelDiscoveryResult(
                    available_models=compatible,
                    selected_model=selected.id if selected else None,
                    discovery_timestamp=datetime.now(),
                    error=None
                )
        
        except httpx.TimeoutException:
            return ModelDiscoveryResult(
                available_models=[],
                selected_model=None,
                discovery_timestamp=datetime.now(),
                error="Model discovery timed out"
            )
        except httpx.RequestError as e:
            return ModelDiscoveryResult(
                available_models=[],
                selected_model=None,
                discovery_timestamp=datetime.now(),
                error=f"Network error during model discovery: {str(e)}"
            )
        except Exception as e:
            logger.exception("Unexpected error during model discovery")
            return ModelDiscoveryResult(
                available_models=[],
                selected_model=None,
                discovery_timestamp=datetime.now(),
                error=f"Unexpected error: {str(e)}"
            )
    
    def _select_model(self, compatible_models: List[ModelInfo]) -> Optional[ModelInfo]:
        """
        Select the best model from compatible options.
        
        Priority:
        1. Models with json_schema support (from SCHEMA_SUPPORTED_MODELS)
        2. Models in PREFERRED_MODELS list (by list order)
        3. Newer models (by creation date)
        4. First available
        
        Args:
            compatible_models: List of compatible models
        
        Returns:
            Selected ModelInfo or None
        """
        if not compatible_models:
            return None
        
        # First, check for models with explicit json_schema support
        for schema_model in SCHEMA_SUPPORTED_MODELS:
            for model in compatible_models:
                if model.id == schema_model:
                    logger.info(f"Selected model with json_schema support: {model.id}")
                    return model
        
        # Then check preferred models in order
        for preferred_id in PREFERRED_MODELS:
            for model in compatible_models:
                if model.id == preferred_id:
                    logger.info(f"Selected preferred model: {model.id}")
                    return model
        
        # Sort by creation date (newest first) and pick the best
        sorted_models = sorted(compatible_models, key=lambda m: m.created, reverse=True)
        selected = sorted_models[0]
        logger.info(f"Selected model by creation date: {selected.id}")
        return selected


# Global instance
_discovery_service: Optional[GroqModelDiscovery] = None


def get_model_discovery() -> GroqModelDiscovery:
    """Get or create the global model discovery service."""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = GroqModelDiscovery()
    return _discovery_service


def get_available_model(force_refresh: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Get the currently available Groq model.
    
    Args:
        force_refresh: Force model discovery
    
    Returns:
        Tuple of (model_id, reason) where reason is non-None if no model available
    """
    discovery = get_model_discovery()
    return discovery.get_selected_model(force_refresh=force_refresh)
