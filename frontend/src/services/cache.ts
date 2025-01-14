interface CacheItem<T> {
  value: T;
  timestamp: number;
  ttl: number;  // Time to live in milliseconds
}

export class CacheService {
  private static instance: CacheService;
  private prefix = 'realestagent_';

  private constructor() {}

  static getInstance(): CacheService {
    if (!CacheService.instance) {
      CacheService.instance = new CacheService();
    }
    return CacheService.instance;
  }

  set<T>(key: string, value: T, ttl: number = 1000 * 60 * 5): void {  // Default 5 min TTL
    const item: CacheItem<T> = {
      value,
      timestamp: Date.now(),
      ttl
    };
    localStorage.setItem(this.prefix + key, JSON.stringify(item));
  }

  get<T>(key: string): T | null {
    const item = localStorage.getItem(this.prefix + key);
    if (!item) return null;

    const cacheItem: CacheItem<T> = JSON.parse(item);
    const now = Date.now();

    if (now - cacheItem.timestamp > cacheItem.ttl) {
      this.remove(key);
      return null;
    }

    return cacheItem.value;
  }

  remove(key: string): void {
    localStorage.removeItem(this.prefix + key);
  }

  invalidate(pattern: string): void {
    const keys = Object.keys(localStorage);
    const cacheKeys = keys.filter(key => 
      key.startsWith(this.prefix) && 
      key.includes(pattern)
    );
    
    cacheKeys.forEach(key => localStorage.removeItem(key));
  }
}

export default CacheService; 