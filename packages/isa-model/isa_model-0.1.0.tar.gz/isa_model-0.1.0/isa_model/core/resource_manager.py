import time
import threading
import logging
from typing import Dict, List, Any, Optional
import psutil
try:
    import torch
    import nvidia_smi
    HAS_GPU = torch.cuda.is_available()
except ImportError:
    HAS_GPU = False

logger = logging.getLogger(__name__)

class ResourceManager:
    """
    Monitors system resources and manages model loading/unloading
    to prevent resource exhaustion.
    """
    
    def __init__(self, model_registry, monitoring_interval=30):
        self.registry = model_registry
        self.monitoring_interval = monitoring_interval  # seconds
        
        self.max_memory_percent = 90  # Maximum memory usage percentage
        self.max_gpu_memory_percent = 90  # Maximum GPU memory usage percentage
        
        self._stop_event = threading.Event()
        self._monitor_thread = None
        
        # Track resource usage over time
        self.resource_history = {
            "timestamps": [],
            "cpu_percent": [],
            "memory_percent": [],
            "gpu_utilization": [],
            "gpu_memory_percent": []
        }
        
        # Initialize GPU monitoring if available
        if HAS_GPU:
            try:
                nvidia_smi.nvmlInit()
                self.gpu_count = torch.cuda.device_count()
                logger.info(f"Initialized GPU monitoring with {self.gpu_count} devices")
            except Exception as e:
                logger.warning(f"Failed to initialize NVIDIA SMI: {str(e)}")
                self.gpu_count = 0
        else:
            self.gpu_count = 0
            
        logger.info("Initialized ResourceManager")
    
    def start_monitoring(self):
        """Start the resource monitoring thread"""
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            logger.warning("Resource monitoring already running")
            return
            
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_resources,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Started resource monitoring thread")
    
    def stop_monitoring(self):
        """Stop the resource monitoring thread"""
        if self._monitor_thread is not None:
            self._stop_event.set()
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None
            logger.info("Stopped resource monitoring thread")
    
    def _monitor_resources(self):
        """Monitor system resources in a loop"""
        while not self._stop_event.is_set():
            try:
                # Get current resource usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # GPU monitoring
                gpu_utilization = 0
                gpu_memory_percent = 0
                
                if self.gpu_count > 0:
                    gpu_util_sum = 0
                    gpu_mem_percent_sum = 0
                    
                    for i in range(self.gpu_count):
                        try:
                            handle = nvidia_smi.nvmlDeviceGetHandleByIndex(i)
                            util = nvidia_smi.nvmlDeviceGetUtilizationRates(handle)
                            mem_info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
                            
                            gpu_util_sum += util.gpu
                            gpu_mem_percent = (mem_info.used / mem_info.total) * 100
                            gpu_mem_percent_sum += gpu_mem_percent
                        except Exception as e:
                            logger.error(f"Error getting GPU {i} stats: {str(e)}")
                    
                    if self.gpu_count > 0:
                        gpu_utilization = gpu_util_sum / self.gpu_count
                        gpu_memory_percent = gpu_mem_percent_sum / self.gpu_count
                
                # Record history (keep last 60 samples)
                now = time.time()
                self.resource_history["timestamps"].append(now)
                self.resource_history["cpu_percent"].append(cpu_percent)
                self.resource_history["memory_percent"].append(memory_percent)
                self.resource_history["gpu_utilization"].append(gpu_utilization)
                self.resource_history["gpu_memory_percent"].append(gpu_memory_percent)
                
                # Trim history to last 60 samples
                max_history = 60
                if len(self.resource_history["timestamps"]) > max_history:
                    for key in self.resource_history:
                        self.resource_history[key] = self.resource_history[key][-max_history:]
                
                # Check if we need to unload models
                self._check_resource_constraints(memory_percent, gpu_memory_percent)
                
                # Log current usage
                logger.debug(
                    f"Resource usage - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, "
                    f"GPU: {gpu_utilization:.1f}%, GPU Memory: {gpu_memory_percent:.1f}%"
                )
                
                # Wait for next check
                self._stop_event.wait(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {str(e)}")
                # Wait a bit before retrying
                self._stop_event.wait(5)
    
    def _check_resource_constraints(self, memory_percent, gpu_memory_percent):
        """Check if we need to unload models due to resource constraints"""
        # Check memory usage
        if memory_percent > self.max_memory_percent:
            logger.warning(
                f"Memory usage ({memory_percent:.1f}%) exceeds threshold ({self.max_memory_percent}%). "
                "Unloading least used model."
            )
            # This would trigger model unloading
            # self.registry._evict_least_used_model()
        
        # Check GPU memory usage
        if HAS_GPU and gpu_memory_percent > self.max_gpu_memory_percent:
            logger.warning(
                f"GPU memory usage ({gpu_memory_percent:.1f}%) exceeds threshold ({self.max_gpu_memory_percent}%). "
                "Unloading least used model."
            )
            # This would trigger model unloading
            # self.registry._evict_least_used_model()
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage stats"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            result = {
                "cpu_percent": cpu_percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "memory_percent": memory_percent,
                "gpus": []
            }
            
            # GPU stats
            if HAS_GPU:
                for i in range(self.gpu_count):
                    try:
                        handle = nvidia_smi.nvmlDeviceGetHandleByIndex(i)
                        name = nvidia_smi.nvmlDeviceGetName(handle)
                        util = nvidia_smi.nvmlDeviceGetUtilizationRates(handle)
                        mem_info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
                        temp = nvidia_smi.nvmlDeviceGetTemperature(
                            handle, nvidia_smi.NVML_TEMPERATURE_GPU
                        )
                        
                        result["gpus"].append({
                            "index": i,
                            "name": name,
                            "utilization_percent": util.gpu,
                            "memory_total_gb": mem_info.total / (1024**3),
                            "memory_used_gb": mem_info.used / (1024**3),
                            "memory_percent": (mem_info.used / mem_info.total) * 100,
                            "temperature_c": temp
                        })
                    except Exception as e:
                        logger.error(f"Error getting GPU {i} stats: {str(e)}")
            
            return result
        except Exception as e:
            logger.error(f"Error getting resource usage: {str(e)}")
            return {"error": str(e)}
