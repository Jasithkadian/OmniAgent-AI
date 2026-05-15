import redis.asyncio as redis
from app.core.config import settings
import json
from typing import List, Dict, Any, Optional

class RedisEventStore:
    def __init__(self):
        self.client = redis.from_url(settings.redis_url, decode_responses=True)
        self.ttl = 86400  # 24 hours

    def _stream_key(self, workflow_id: str) -> str:
        return f"events:{workflow_id}"

    async def add_event(self, workflow_id: str, event_data: Dict[str, Any]) -> str:
        """
        Adds an event to a Redis Stream and sets a 24h TTL on the key.
        Returns the Redis message ID.
        """
        key = self._stream_key(workflow_id)
        # Convert data to string for storage
        event_json = json.dumps(event_data)
        
        # XADD key ID field value
        message_id = await self.client.xadd(key, {"data": event_json})
        
        # Ensure the stream expires after 24 hours of inactivity
        await self.client.expire(key, self.ttl)
        
        return message_id

    async def get_events_since(self, workflow_id: str, last_message_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all events from the stream that occurred after last_message_id.
        """
        key = self._stream_key(workflow_id)
        # (last_message_id is non-inclusive, hence the '+' suffix in XRANGE if needed, 
        # but Redis XREAD/XRANGE with exclusive start is better)
        # Using XRANGE with (ID syntax for exclusive
        events = await self.client.xrange(key, min=f"({last_message_id}", max="+")
        
        results = []
        for msg_id, payload in events:
            data = json.loads(payload["data"])
            data["message_id"] = msg_id
            results.append(data)
            
        return results

    async def close(self):
        await self.client.close()

redis_event_store = RedisEventStore()
