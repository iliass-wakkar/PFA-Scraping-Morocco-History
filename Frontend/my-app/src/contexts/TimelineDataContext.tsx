"use client";
import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import ApiService, { ApiBigEvent } from '../services/apiService';
import { transformApiDataToBigEvents } from '../utils/dataTransformer';
import { TimelineBigEvent } from '../components/Timeline';
import { useLanguage } from "./LanguageContext";

interface TimelineDataContextType {
  bigEvents: TimelineBigEvent[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

const TimelineDataContext = createContext<TimelineDataContextType | undefined>(undefined);

export const TimelineDataProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { language } = useLanguage();
  const [bigEvents, setBigEvents] = useState<TimelineBigEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const apiData: ApiBigEvent[] = await ApiService.getAllEvents(language);
      let transformed = transformApiDataToBigEvents(apiData);
      // Sort big events and their events chronologically
      transformed = transformed
        .slice()
        .sort((a, b) => (a.events[0]?.date.milady.start || 0) - (b.events[0]?.date.milady.start || 0))
        .map(be => ({
          ...be,
          events: be.events.slice().sort((a, b) => a.date.milady.start - b.date.milady.start)
        }));
      setBigEvents(transformed);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch timeline data');
    } finally {
      setLoading(false);
    }
  }, [language]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refresh = () => {
    fetchData();
  };

  return (
    <TimelineDataContext.Provider value={{ bigEvents, loading, error, refresh }}>
      {children}
    </TimelineDataContext.Provider>
  );
};

export const useTimelineData = (): TimelineDataContextType => {
  const context = useContext(TimelineDataContext);
  if (context === undefined) {
    throw new Error('useTimelineData must be used within a TimelineDataProvider');
  }
  return context;
}; 