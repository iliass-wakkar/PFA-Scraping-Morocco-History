import axios from 'axios';

const BASE_URL = 'http://localhost:5000';

export interface HistoricalEvent {
  event_name: string;
  article_title: string;
  date: string;
  sections: {
    subtitle: string;
    paragraphs: {
      text: string;
    }[];
  }[];
}

export interface Period {
  big_event_name: string;
  events: HistoricalEvent[];
}

export interface SearchResult extends Period {
  score: number;
}

const api = {
  getAllEvents: async (language: string = 'ar') => {
    const response = await axios.get<Period[]>(`${BASE_URL}/api/historical-events/`, {
      params: { language }
    });
    return response.data;
  },

  getPeriodEvents: async (periodName: string, language: string = 'ar') => {
    const response = await axios.get<Period>(`${BASE_URL}/api/historical-events/${encodeURIComponent(periodName)}`, {
      params: { language }
    });
    return response.data;
  },

  searchEvents: async (query: string, language: string = 'ar') => {
    const response = await axios.get<SearchResult[]>(`${BASE_URL}/api/historical-events/search`, {
      params: { q: query, language }
    });
    return response.data;
  }
};

export default api; 