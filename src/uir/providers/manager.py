"""Provider management and health monitoring"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog

from ..models import Provider, ProviderType, ProviderConfig, ProviderHealth
from ..core.adapter import ProviderAdapter, ProviderFactory

logger = structlog.get_logger()


class ProviderManager:
    """Manages provider instances and health monitoring"""
    
    def __init__(self):
        self.adapters: Dict[str, ProviderAdapter] = {}
        self.configs: Dict[str, ProviderConfig] = {}
        self.health_status: Dict[str, ProviderHealth] = {}
        self.health_check_interval = 60  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self.logger = logger.bind(component="provider_manager")
    
    async def initialize(self, configs: Dict[str, ProviderConfig]):
        """Initialize providers with configurations"""
        for name, config in configs.items():
            try:
                adapter = ProviderFactory.create(config)
                self.adapters[name] = adapter
                self.configs[name] = config
                self.logger.info(f"Initialized provider: {name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize provider {name}: {e}")
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_monitor())
    
    async def get_adapter(self, provider_name: str) -> Optional[ProviderAdapter]:
        """Get provider adapter by name"""
        return self.adapters.get(provider_name)
    
    async def get_available_providers(
        self,
        requested_providers: Optional[List[str]] = None,
        provider_type: Optional[ProviderType] = None
    ) -> List[str]:
        """Get list of available providers"""
        available = []
        
        for name, adapter in self.adapters.items():
            # Filter by requested providers
            if requested_providers and name not in requested_providers:
                continue
            
            # Filter by type
            if provider_type and self.configs[name].type != provider_type:
                continue
            
            # Check health status
            health = self.health_status.get(name)
            if health and health.status in ["healthy", "degraded"]:
                available.append(name)
            elif not health:
                # No health check yet, assume available
                available.append(name)
        
        return available
    
    async def check_provider_health(self, provider_name: str) -> ProviderHealth:
        """Check health of a specific provider"""
        adapter = self.adapters.get(provider_name)
        if not adapter:
            return ProviderHealth(
                provider=provider_name,
                status="unhealthy",
                last_check=datetime.now(),
                error_message="Provider not found"
            )
        
        try:
            start_time = datetime.now()
            health = await adapter.health_check()
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update latency in health status
            health.latency_ms = latency_ms
            
            # Determine status based on latency
            if latency_ms > 5000:
                health.status = "degraded"
            
            self.health_status[provider_name] = health
            return health
            
        except Exception as e:
            self.logger.error(f"Health check failed for {provider_name}: {e}")
            health = ProviderHealth(
                provider=provider_name,
                status="unhealthy",
                last_check=datetime.now(),
                error_message=str(e)
            )
            self.health_status[provider_name] = health
            return health
    
    async def _health_monitor(self):
        """Background task for health monitoring"""
        while True:
            try:
                # Check health of all providers
                tasks = []
                for provider_name in self.adapters.keys():
                    tasks.append(self.check_provider_health(provider_name))
                
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Log health summary
                healthy = sum(1 for h in self.health_status.values() if h.status == "healthy")
                degraded = sum(1 for h in self.health_status.values() if h.status == "degraded")
                unhealthy = sum(1 for h in self.health_status.values() if h.status == "unhealthy")
                
                self.logger.info(
                    "Health check completed",
                    healthy=healthy,
                    degraded=degraded,
                    unhealthy=unhealthy
                )
                
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
            
            await asyncio.sleep(self.health_check_interval)
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics about providers"""
        stats = {
            "total_providers": len(self.adapters),
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "providers": {}
        }
        
        for name, health in self.health_status.items():
            if health.status == "healthy":
                stats["healthy"] += 1
            elif health.status == "degraded":
                stats["degraded"] += 1
            else:
                stats["unhealthy"] += 1
            
            stats["providers"][name] = {
                "status": health.status,
                "latency_ms": health.latency_ms,
                "last_check": health.last_check.isoformat() if health.last_check else None,
                "error": health.error_message
            }
        
        return stats
    
    async def failover(self, failed_provider: str) -> Optional[str]:
        """Get alternative provider for failover"""
        # Get provider type
        config = self.configs.get(failed_provider)
        if not config:
            return None
        
        # Find alternative provider of same type
        alternatives = await self.get_available_providers(provider_type=config.type)
        
        # Remove the failed provider
        alternatives = [p for p in alternatives if p != failed_provider]
        
        if alternatives:
            # Return provider with best health
            best_provider = None
            best_latency = float('inf')
            
            for provider in alternatives:
                health = self.health_status.get(provider)
                if health and health.latency_ms and health.latency_ms < best_latency:
                    best_latency = health.latency_ms
                    best_provider = provider
            
            return best_provider or alternatives[0]
        
        return None
    
    async def shutdown(self):
        """Shutdown provider manager"""
        # Cancel health monitoring
        if self._health_check_task:
            self._health_check_task.cancel()
        
        # Close all adapters
        for adapter in self.adapters.values():
            try:
                await adapter.close()
            except Exception as e:
                self.logger.error(f"Error closing adapter: {e}")