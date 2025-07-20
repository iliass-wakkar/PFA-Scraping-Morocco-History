import { useState, useEffect, useCallback, useRef } from 'react';
import ApiService, { ApiBigEvent, ApiEvent } from '../services/apiService';

// Hook for fetching all events
export const useAllEvents = (language: string = 'ar') => {
  const [data, setData] = useState<ApiBigEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      
      const result = await ApiService.getAllEvents(language);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch events');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [language]);

  const refresh = useCallback(() => {
    fetchData(true);
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refreshing, refresh };
};

// Hook for fetching events by period
export const useEventsByPeriod = (periodName: string, language: string = 'ar') => {
  const [data, setData] = useState<ApiBigEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (!periodName) return;
    
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      
      const result = await ApiService.getEventsByPeriod(periodName, language);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch period events');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [periodName, language]);

  const refresh = useCallback(() => {
    fetchData(true);
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refreshing, refresh };
};

// Hook for searching events
export const useSearchEvents = (query: string, language: string = 'ar') => {
  const [data, setData] = useState<ApiBigEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<NodeJS.Timeout>();

  const search = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setData([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const result = await ApiService.searchEvents(searchQuery, language);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }, [language]);

  useEffect(() => {
    // Debounce search to avoid too many API calls
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      search(query);
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, search]);

  return { data, loading, error };
};

// Hook for fetching a single event by ID
export const useEventById = (eventId: string, language: string = 'ar') => {
  const [event, setEvent] = useState<ApiEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvent = async () => {
      if (!eventId) return;

      try {
        setLoading(true);
        setError(null);
        
        // First try to get all events and find the specific one
        const allEvents = await ApiService.getAllEvents(language);
        
        // Flatten all events and find by ID
        const allFlattenedEvents: ApiEvent[] = [];
        allEvents.forEach(bigEvent => {
          bigEvent.events.forEach(event => {
            allFlattenedEvents.push(event);
          });
        });

        // Find event by ID (assuming eventId is the index or some identifier)
        const foundEvent = allFlattenedEvents[parseInt(eventId) || 0];
        
        if (foundEvent) {
          setEvent(foundEvent);
        } else {
          setError('Event not found');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch event');
      } finally {
        setLoading(false);
      }
    };

    fetchEvent();
  }, [eventId, language]);

  return { event, loading, error };
};

// Hook for API connection status
export const useApiStatus = () => {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(true);

  const checkConnection = useCallback(async () => {
    try {
      setChecking(true);
      await ApiService.getWelcomeMessage();
      setIsConnected(true);
    } catch (err) {
      setIsConnected(false);
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

  return { isConnected, checking, checkConnection };
}; 