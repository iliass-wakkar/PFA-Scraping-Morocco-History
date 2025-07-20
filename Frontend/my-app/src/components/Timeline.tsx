import React from "react";
import HistoryLineStart from "./HistoryLineStart";
import HistoryLineMiddle from "./HistoryLineMiddle";
import HistoryLineEnd from "./HistoryLineEnd";

export type TimelineParagraph = {
  paragraph_id: string;
  text: string;
  source_URLs?: string[];
};

export type TimelineSection = {
  subtitle: string;
  paragraphs: TimelineParagraph[];
};

export type TimelineEvent = {
  event_name: string;
  article_title: string;
  date: {
    milady: {
      start: number;
      end: number;
    };
    hijry?: {
      start: number;
      end: number;
      approx: boolean;
    };
  };
  sections: TimelineSection[];
};

export type TimelineBigEvent = {
  big_event_name: string;
  events: TimelineEvent[];
  score?: number;
};

export interface TimelineProps {
  bigEvents: TimelineBigEvent[];
}

const Timeline: React.FC<TimelineProps> = ({ bigEvents }) => {
  // Get the latest event's end year for HistoryLineEnd
  const allEvents = bigEvents.flatMap(be => be.events);
  const maxEndYear = allEvents.length
    ? Math.max(...allEvents.map(e => e.date.milady.end))
    : "";
  const endYear = maxEndYear ? maxEndYear.toString() : "";
  const totalEvents = bigEvents.reduce((acc, be) => acc + be.events.length, 0);
  const totalPeriods = bigEvents.length;

  return (
    <div className="w-full max-w-11/12 mx-auto px-2 md:px-12 py-16 bg-[#141115] rounded-2xl shadow-lg">
      <h1 className="text-5xl md:text-6xl font-extrabold text-green-400 mb-16 mt-10 drop-shadow-lg text-center">
        Morocco Historical Timeline
      </h1>
      {bigEvents
        .slice()
        .sort((a, b) => (a.events[0]?.date.milady.start || 0) - (b.events[0]?.date.milady.start || 0))
        .map((bigEvent, bigEventIndex) => (
        <div key={bigEvent.big_event_name} className="mb-16">
            {/* Start of Period */}
            <HistoryLineStart
              title={bigEvent.big_event_name}
              startYear={bigEvent.events[0]?.date.milady.start.toString() || ""}
              endYear={bigEvent.events[bigEvent.events.length - 1]?.date.milady.end.toString() || ""}
            />
            {/* Events in this period */}
            {bigEvent.events
              .slice()
              .sort((a, b) => a.date.milady.start - b.date.milady.start)
              .map((event, eventIndex) => {
                const eventId = encodeURIComponent(event.event_name);
                return (
                  <HistoryLineMiddle
                    key={event.event_name + bigEventIndex + eventIndex}
                    event={{
                      event_name: event.event_name,
                      article_title: event.article_title,
                      date: event.date.milady.start.toString(),
                      sections: event.sections,
                    }}
                    index={eventIndex}
                    date={event.date.milady.start.toString()}
                    eventId={eventId}
                  />
                );
              })}
        </div>
      ))}
      {/* End of Timeline */}
      <HistoryLineEnd
        endYear={endYear}
        totalEvents={totalEvents}
        totalPeriods={totalPeriods}
      />
    </div>
  );
};

export default Timeline; 