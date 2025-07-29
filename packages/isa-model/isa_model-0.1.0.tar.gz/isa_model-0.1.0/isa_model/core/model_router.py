import random
import time
from typing import Dict, List, Any, Optional, Callable
import threading

class ModelRouter:
    """
    Routes requests to appropriate model instances based on different strategies:
    - Weighted round-robin
    - Least connections
    - Least response time
    - Dynamic load balancing
    """
    
    def __init__(self, registry):
        self.registry = registry
        self.model_stats = {}  # Track performance metrics for each model
        self.lock = threading.RLock()
        
        # Maps model_type -> list of model_ids of that type
        self.model_type_mapping = {}
        
        # Maps routing_strategy_name -> routing_function
        self.routing_strategies = {
            "round_robin": self._route_round_robin,
            "weighted_random": self._route_weighted_random,
            "least_connections": self._route_least_connections,
            "least_response_time": self._route_least_response_time,
            "dynamic_load": self._route_dynamic_load
        }
        
        # Round-robin counters for each model type
        self.rr_counters = {}
        
    def register_model_type(self, model_type: str, model_ids: List[str], weights: Optional[List[float]] = None):
        """Register models of a specific type with optional weights"""
        with self.lock:
            self.model_type_mapping[model_type] = model_ids
            
            # Initialize stats for each model
            for i, model_id in enumerate(model_ids):
                weight = weights[i] if weights and i < len(weights) else 1.0
                
                if model_id not in self.model_stats:
                    self.model_stats[model_id] = {
                        "active_connections": 0,
                        "total_requests": 0,
                        "avg_response_time": 0,
                        "weight": weight,
                        "last_used": 0
                    }
                else:
                    # Update weight if model already exists
                    self.model_stats[model_id]["weight"] = weight
            
            # Initialize round-robin counter
            self.rr_counters[model_type] = 0
    
    def route_request(self, model_type: str, routing_strategy: str = "round_robin") -> Optional[str]:
        """
        Route a request to an appropriate model of the given type
        
        Args:
            model_type: Type of model needed
            routing_strategy: Strategy to use for routing
            
        Returns:
            model_id: ID of the model to use, or None if no models available
        """
        with self.lock:
            if model_type not in self.model_type_mapping:
                return None
                
            if not self.model_type_mapping[model_type]:
                return None
                
            # Get the routing function
            routing_func = self.routing_strategies.get(routing_strategy, self._route_round_robin)
            
            # Route the request
            model_id = routing_func(model_type)
            
            if model_id:
                # Update stats
                self.model_stats[model_id]["active_connections"] += 1
                self.model_stats[model_id]["total_requests"] += 1
                self.model_stats[model_id]["last_used"] = time.time()
                
            return model_id
    
    def release_connection(self, model_id: str, response_time: float = None):
        """Release a connection and update stats"""
        with self.lock:
            if model_id in self.model_stats:
                stats = self.model_stats[model_id]
                stats["active_connections"] = max(0, stats["active_connections"] - 1)
                
                # Update average response time
                if response_time is not None:
                    old_avg = stats["avg_response_time"]
                    total_req = stats["total_requests"]
                    
                    if total_req > 0:
                        # Weighted average
                        stats["avg_response_time"] = (old_avg * (total_req - 1) + response_time) / total_req
    
    # Routing strategies
    def _route_round_robin(self, model_type: str) -> Optional[str]:
        """Simple round-robin routing"""
        models = self.model_type_mapping.get(model_type, [])
        if not models:
            return None
            
        # Get and increment counter
        counter = self.rr_counters[model_type]
        self.rr_counters[model_type] = (counter + 1) % len(models)
        
        return models[counter]
    
    def _route_weighted_random(self, model_type: str) -> Optional[str]:
        """Weighted random selection based on configured weights"""
        models = self.model_type_mapping.get(model_type, [])
        if not models:
            return None
            
        # Get weights
        weights = [self.model_stats[model_id]["weight"] for model_id in models]
        
        # Weighted random selection
        total = sum(weights)
        r = random.uniform(0, total)
        upto = 0
        
        for i, w in enumerate(weights):
            upto += w
            if upto >= r:
                return models[i]
                
        # Fallback
        return models[-1]
    
    def _route_least_connections(self, model_type: str) -> Optional[str]:
        """Route to the model with the fewest active connections"""
        models = self.model_type_mapping.get(model_type, [])
        if not models:
            return None
            
        # Find model with least connections
        min_connections = float('inf')
        selected_model = None
        
        for model_id in models:
            connections = self.model_stats[model_id]["active_connections"]
            if connections < min_connections:
                min_connections = connections
                selected_model = model_id
                
        return selected_model
    
    def _route_least_response_time(self, model_type: str) -> Optional[str]:
        """Route to the model with the lowest average response time"""
        models = self.model_type_mapping.get(model_type, [])
        if not models:
            return None
            
        # Find model with lowest response time
        min_response_time = float('inf')
        selected_model = None
        
        for model_id in models:
            response_time = self.model_stats[model_id]["avg_response_time"]
            # Skip models with no data yet
            if response_time == 0:
                continue
                
            if response_time < min_response_time:
                min_response_time = response_time
                selected_model = model_id
                
        # If no model has response time data, fall back to least connections
        if selected_model is None:
            return self._route_least_connections(model_type)
            
        return selected_model
    
    def _route_dynamic_load(self, model_type: str) -> Optional[str]:
        """
        Dynamic load balancing based on a combination of:
        - Connection count
        - Response time
        - Recent usage
        """
        models = self.model_type_mapping.get(model_type, [])
        if not models:
            return None
            
        # Calculate a score for each model (lower is better)
        best_score = float('inf')
        selected_model = None
        now = time.time()
        
        for model_id in models:
            stats = self.model_stats[model_id]
            
            # Normalize each factor between 0 and 1
            connections = stats["active_connections"]
            conn_score = connections / (connections + 1)  # Approaches 1 as connections increase
            
            resp_time = stats["avg_response_time"]
            # Max expected response time (adjust as needed)
            max_resp_time = 5.0  
            resp_score = min(1.0, resp_time / max_resp_time)
            
            # Time since last use (for distributing load)
            recency = now - stats["last_used"] if stats["last_used"] > 0 else 60
            recency_score = 1.0 - min(1.0, recency / 60.0)  # Unused for 60s approaches 0
            
            # Combined score (lower is better)
            # Weights can be adjusted based on importance
            score = (0.4 * conn_score) + (0.4 * resp_score) + (0.2 * recency_score)
            
            if score < best_score:
                best_score = score
                selected_model = model_id
                
        return selected_model
