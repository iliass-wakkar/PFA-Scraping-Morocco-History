import HistoryLineMiddle from "./history_line_middle";
import { useState } from "react";

interface Source {
    id: string;
    title: string;
    url?: string;
}

interface Event {
    id: string;
    title: string;
    summary: string;
    sources: Source[];
}

interface Period {
    id: string;
    title: string;
    startYear: number;
    endYear: number;
    events: Event[];
}

interface ExtendedEvent extends Event {
    periodId: string;
    periodTitle: string;
    date: string;
}

const Timeline = ({ periods }: { periods: Period[] }) => {
    const [Lang] = useState(localStorage.getItem("lang") || "en");
   
    // Flatten all events from all periods and add dates
    const allEvents: ExtendedEvent[] = periods.flatMap(period =>
        period.events.map(event => {
            // Extract the date from the event title or use a default format
            let date = '';
            const yearMatch = event.title.match(/\((\d{3,4})\s*م?\)/);
            if (yearMatch) {
                date = `${yearMatch[1]} ${Lang === 'ar' ? 'م' : 'CE'}`;
            }
           
            return {
                ...event,
                periodId: period.id,
                periodTitle: period.title,
                date: date
            };
        })
    );

    return (
        <div className="w-full max-w-4xl mx-auto px-4 py-8">
            <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-1/2 transform -translate-x-1/2 h-full w-0.5 bg-gray-300 dark:bg-gray-700"></div>
                
                {/* Events */}
                {allEvents.map((event, index) => (
                    <div 
                        key={`${event.periodId}-${event.id}`}
                        className={`mb-16 flex items-center w-full ${
                            index % 2 === 0 ? 'flex-row-reverse' : ''
                        }`}
                    >
                        {/* Content */}
                        <div className={`w-5/12 ${index % 2 === 0 ? 'text-left pl-8' : 'text-right pr-8'}`}>
                            <HistoryLineMiddle
                                event={event}
                                index={index}
                                date={event.date}
                            />
                        </div>
                        
                        {/* Timeline dot */}
                        <div className="absolute left-1/2 transform -translate-x-1/2 w-4 h-4 bg-blue-500 rounded-full border-4 border-white dark:border-gray-900"></div>
                        
                        {/* Date */}
                        <div className={`w-5/12 ${index % 2 === 0 ? 'text-right pr-8' : 'text-left pl-8'}`}>
                            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                                {event.date}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Timeline;