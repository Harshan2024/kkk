import time
from typing import Dict, Any, Optional

class InProcessCache:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._expires: Dict[str, float] = {}
        self.force_degraded: bool = False

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if self.force_degraded:
            return False
        try:
            self._store[key] = value
            if ttl is not None:
                self._expires[key] = time.time() + ttl
            elif key in self._expires:
                del self._expires[key]
            return True
        except Exception:
            return False

    def get(self, key: str) -> Optional[Any]:
        if self.force_degraded:
            return None
        try:
            if key in self._expires and time.time() > self._expires[key]:
                self.delete(key)
                return None
            return self._store.get(key)
        except Exception:
            return None

    def delete(self, key: str) -> bool:
        if self.force_degraded:
            return False
        try:
            if key in self._store:
                del self._store[key]
            if key in self._expires:
                del self._expires[key]
            return True
        except Exception:
            return False

    def delete_pattern(self, pattern: str) -> bool:
        if self.force_degraded:
            return False
        try:
            keys_to_del = [k for k in self._store.keys() if pattern in k]
            for k in keys_to_del:
                self.delete(k)
            return True
        except Exception:
            return False

    def clear(self) -> bool:
        if self.force_degraded:
            return False
        try:
            self._store.clear()
            self._expires.clear()
            return True
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        if self.force_degraded:
            return False
        try:
            if key in self._expires and time.time() > self._expires[key]:
                self.delete(key)
                return False
            return key in self._store
        except Exception:
            return False

    def validate(self) -> str:
        """
        Verify:
        - cache exists
        - cache readable
        - cache writable
        Returns "healthy" or "degraded"
        """
        if self.force_degraded:
            return "degraded"
        
        test_key = "__health_check_test__"
        test_value = "ok"
        try:
            # Test Write
            write_success = self.set(test_key, test_value, ttl=10)
            if not write_success:
                return "degraded"
            
            # Test Read / Exist
            if not self.exists(test_key) or self.get(test_key) != test_value:
                return "degraded"
            
            # Test Delete
            delete_success = self.delete(test_key)
            if not delete_success:
                return "degraded"
                
            return "healthy"
        except Exception:
            return "degraded"

global_cache = InProcessCache()
