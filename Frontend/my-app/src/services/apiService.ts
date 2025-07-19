// API Types
export interface ApiParagraph {
  text: string;
  source_URLs?: string[];
  paragraph_id?: string;
}

export interface ApiSection {
  subtitle: string;
  paragraphs: ApiParagraph[];
}

export interface ApiDate {
  hijry?: {
    approx?: boolean;
    end?: number | null;
    note?: string | null;
    start?: number | null;
  };
  milady: {
    start: number;
    end: number;
  };
}

export interface ApiEvent {
  event_name: string;
  article_title: string;
  date: string | ApiDate;
  sections: ApiSection[];
}

export interface ApiBigEvent {
  big_event_name: string;
  events: ApiEvent[];
  score?: number;
}

export interface ApiResponse {
  data: ApiBigEvent[];
  status: string;
}

export interface ApiError {
  status: string;
  message: string;
}

// API Configuration
const API_BASE_URL = 'http://localhost:5000';
const DEFAULT_LANGUAGE = 'en';

// Cache configuration
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const cache = new Map<string, { data: any; timestamp: number }>();

class ApiService {
  private static async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  private static getCacheKey(endpoint: string, params?: Record<string, string>): string {
    const paramString = params ? `?${new URLSearchParams(params).toString()}` : '';
    return `${endpoint}${paramString}`;
  }

  private static isCacheValid(timestamp: number): boolean {
    return Date.now() - timestamp < CACHE_DURATION;
  }

  private static async getCachedOrFetch<T>(
    endpoint: string, 
    params?: Record<string, string>
  ): Promise<T> {
    const cacheKey = this.getCacheKey(endpoint, params);
    const cached = cache.get(cacheKey);

    if (cached && this.isCacheValid(cached.timestamp)) {
      return cached.data;
    }

    const paramString = params ? `?${new URLSearchParams(params).toString()}` : '';
    const data = await this.makeRequest<T>(`${endpoint}${paramString}`);
    
    cache.set(cacheKey, { data, timestamp: Date.now() });
    return data;
  }

  // Get all historical events
  static async getAllEvents(language: string = DEFAULT_LANGUAGE): Promise<ApiBigEvent[]> {
    try {
      const result = await this.getCachedOrFetch<any>('/api/historical-events/', { language });
      
      // Handle both array and single object responses
      if (Array.isArray(result)) {
        return result;
      } else if (result && typeof result === 'object') {
        // If it's a single object, wrap it in an array
        return [result];
      } else {
        console.warn('Unexpected API response format:', result);
        return [];
      }
    } catch (error) {
      console.error('Failed to fetch all events:', error);
      return [];
    }
  }

  // Get events by period
  static async getEventsByPeriod(
    periodName: string, 
    language: string = DEFAULT_LANGUAGE
  ): Promise<ApiBigEvent> {
    const encodedPeriod = encodeURIComponent(periodName);
    return this.getCachedOrFetch<ApiBigEvent>(
      `/api/historical-events/${encodedPeriod}`, 
      { language }
    );
  }

  // Get welcome message (for testing API connection)
  static async getWelcomeMessage(): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/');
  }

  // Clear cache
  static clearCache(): void {
    cache.clear();
  }

  // Clear specific cache entry
  static clearCacheEntry(endpoint: string, params?: Record<string, string>): void {
    const cacheKey = this.getCacheKey(endpoint, params);
    cache.delete(cacheKey);
  }
}

export default ApiService; 