import { ApiEvent, ApiBigEvent } from '../services/apiService';
import { TimelineEvent, TimelineBigEvent } from '../components/Timeline';

// Parse date string like "429-534 م" or "683-710 AD" to structured format
const parseDate = (dateString: string) => {
  // Remove common suffixes and clean the string
  const cleanDate = dateString.replace(/[م\sAD]/g, '').trim();
  
  // Handle different date formats
  if (cleanDate.includes('-')) {
    const [start, end] = cleanDate.split('-').map(s => s.trim());
    const startYear = parseInt(start);
    const endYear = parseInt(end);
    
    if (!isNaN(startYear) && !isNaN(endYear)) {
      return {
        milady: {
          start: startYear,
          end: endYear
        }
      };
    }
  } else {
    // Single year
    const year = parseInt(cleanDate);
    if (!isNaN(year)) {
      return {
        milady: {
          start: year,
          end: year
        }
      };
    }
  }
  
  // Fallback
  return {
    milady: {
      start: 0,
      end: 0
    }
  };
};

// Transform API event to TimelineEvent format
export const transformApiEventToTimelineEvent = (apiEvent: ApiEvent): TimelineEvent => {
  // Handle structured date format from API
  let dateStructure;
  if (typeof apiEvent.date === 'string') {
    // Handle string date format (legacy)
    dateStructure = parseDate(apiEvent.date);
  } else if (apiEvent.date && typeof apiEvent.date === 'object' && 'milady' in apiEvent.date) {
    // Handle structured date format from API
    dateStructure = {
      milady: {
        start: apiEvent.date.milady.start || 0,
        end: apiEvent.date.milady.end || 0
      }
    };
  } else {
    // Fallback
    dateStructure = {
      milady: {
        start: 0,
        end: 0
      }
    };
  }

  return {
    event_name: apiEvent.event_name,
    article_title: apiEvent.article_title,
    date: dateStructure,
    sections: apiEvent.sections.map(section => ({
      subtitle: section.subtitle,
      paragraphs: section.paragraphs.map(paragraph => ({
        paragraph_id: paragraph.paragraph_id || `${section.subtitle}-${paragraph.text.substring(0, 10)}`, // Use existing ID or generate one
        text: paragraph.text,
        source_URLs: paragraph.source_URLs || []
      }))
    }))
  };
};

// Transform API big event to component format
export const transformApiBigEventToComponentFormat = (apiBigEvent: ApiBigEvent): TimelineBigEvent => {
  return {
    big_event_name: apiBigEvent.big_event_name,
    events: apiBigEvent.events.map(transformApiEventToTimelineEvent),
    score: 'score' in apiBigEvent && typeof apiBigEvent.score === 'number' ? apiBigEvent.score as number : undefined
  };
};

// Transform API data to big events structure (don't flatten)
export const transformApiDataToBigEvents = (apiBigEvents: ApiBigEvent | ApiBigEvent[]): TimelineBigEvent[] => {
  const bigEvents: TimelineBigEvent[] = [];
  
  // Handle both single object and array
  const eventsArray = Array.isArray(apiBigEvents) ? apiBigEvents : [apiBigEvents];
  
  eventsArray.forEach((bigEvent) => {
    
    // Handle the API response structure where events are nested in a "data" property
    let eventsToProcess: ApiBigEvent[] = [];
    
    if (bigEvent && typeof bigEvent === 'object') {
      // Check if it's the API response structure with "data" property
      if ('data' in bigEvent && Array.isArray(bigEvent.data)) {
        eventsToProcess = bigEvent.data;
      } else if ('events' in bigEvent && Array.isArray(bigEvent.events)) {
        // Direct events structure
        eventsToProcess = [bigEvent as ApiBigEvent];
      } else {
      }
    }
    
    // Process the events
    eventsToProcess.forEach((eventData, eventIndex) => {
      
      if (eventData && 'events' in eventData && Array.isArray(eventData.events)) {
        try {
          const transformedBigEvent = transformApiBigEventToComponentFormat(eventData);
          bigEvents.push(transformedBigEvent);
        } catch (err) {
          console.error(`Error transforming big event ${eventIndex}:`, err);
        }
      } else {
      }
    });
  });
  
  return bigEvents;
};

// Flatten all events from multiple big events or a single big event (for backward compatibility)
export const flattenAllEvents = (apiBigEvents: ApiBigEvent | ApiBigEvent[]): TimelineEvent[] => {
  const bigEvents = transformApiDataToBigEvents(apiBigEvents);
  const allEvents: TimelineEvent[] = [];
  
  bigEvents.forEach(bigEvent => {
    allEvents.push(...bigEvent.events);
  });
  
  return allEvents;
};

// Find event by ID (updated to handle new ID format)
export const findEventById = (events: TimelineEvent[], eventId: string): TimelineEvent | null => {
  // Parse the event ID format: event-name-bigEventIndex-eventIndex
  const parts = eventId.split('-');
  
  // We need at least 3 parts: event-name, bigEventIndex, eventIndex
  if (parts.length < 3) {
    return null;
  }
  
  // Extract the indices from the end
  const bigEventIndex = parseInt(parts[parts.length - 2]);
  const eventIndex = parseInt(parts[parts.length - 1]);
  
  // Check if indices are valid numbers
  if (isNaN(bigEventIndex) || isNaN(eventIndex)) {
    return null;
  }
  
  // For now, we'll use a simple approach: find the event by its position in the flattened array
  // This assumes events are in the same order as they appear in the timeline
  if (eventIndex >= 0 && eventIndex < events.length) {
    const foundEvent = events[eventIndex];
    return foundEvent;
  }
  
  return null;
};

// Generate event ID for routing
export const generateEventId = (event: TimelineEvent, index: number): string => {
  return `${event.event_name.replace(/\s+/g, '-').toLowerCase()}-${index}`;
}; 