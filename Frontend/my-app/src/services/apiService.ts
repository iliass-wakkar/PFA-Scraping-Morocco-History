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

export interface ApiEvent {
  _id?: { $oid: string };
  event_name: string;
  article_title: string;
  sections: ApiSection[];
  date?: {
    hijri: {
      start: number;
      end?: number;
    };
    milady: {
      start: number;
      end?: number;
    };
  };
}

export interface ApiBigEvent {
  big_event_name: string;
  events: ApiEvent[];
}

export interface ApiResponse {
  data: ApiBigEvent[];
  status: string;
}

export interface ApiError {
  status: string;
  message: string;
}

// API Configuration - Updated to use local Next.js API
const API_BASE_URL = '/api';
const DEFAULT_LANGUAGE = 'ar'; // Changed to match LanguageContext default

// Cache configuration
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const cache = new Map<string, { data: unknown; timestamp: number }>();

class ApiService {
  private static async makeRequest<T = unknown>(
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

  private static async getCachedOrFetch<T = unknown>(
    endpoint: string, 
    params?: Record<string, string>
  ): Promise<T> {
    const cacheKey = this.getCacheKey(endpoint, params);
    const cached = cache.get(cacheKey);

    if (cached && this.isCacheValid(cached.timestamp)) {
      return cached.data as T; // Cast to the expected type
    }

    const paramString = params ? `?${new URLSearchParams(params).toString()}` : '';
    const data = await this.makeRequest<T>(`${endpoint}${paramString}`);
    
    cache.set(cacheKey, { data, timestamp: Date.now() });
    return data;
  }

  // Get all historical events
  static async getAllEvents(language: string = DEFAULT_LANGUAGE): Promise<ApiBigEvent[]> {
    try {
      const result = await this.getCachedOrFetch<ApiResponse>(
        '/historical-events/', { language }
      );
      // Handle the new API response format with status and data
      if (result && result.status === 'success' && result.data) {
        return result.data;
      } else if (Array.isArray(result)) {
        return result as unknown as ApiBigEvent[];
      } else if (result && typeof result === 'object') {
        // If it's a single object, wrap it in an array
        return [result as unknown as ApiBigEvent];
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
    const result = await this.getCachedOrFetch<ApiResponse>(
      `/historical-events/${encodedPeriod}`, 
      { language }
    );
    // Handle the new API response format
    if (result && result.status === 'success' && result.data) {
      if (Array.isArray(result.data)) {
        if (result.data.length > 0) {
          return result.data[0];
        } else {
          throw new Error('No events found for this period');
        }
      } else {
        return result.data as ApiBigEvent;
      }
    }
    throw new Error('Unexpected API response format for getEventsByPeriod');
  }

  // Search events
  static async searchEvents(query: string, language: string = DEFAULT_LANGUAGE): Promise<ApiBigEvent[]> {
    try {
      const result = await this.getCachedOrFetch<ApiResponse>(
        '/historical-events/search', { 
          q: query, 
          language 
        }
      );
      // Handle the new API response format
      if (result && result.status === 'success' && result.data) {
        return result.data;
      }
      return [];
    } catch (error) {
      console.error('Failed to search events:', error);
      return [];
    }
  }

  // Get welcome message (for testing API connection)
  static async getWelcomeMessage(): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/');
  }

  // Clear all cache
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