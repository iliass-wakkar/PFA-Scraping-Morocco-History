"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAllEvents } from "../../../hooks/useApi";
import { transformApiDataToBigEvents } from "../../../utils/dataTransformer";
import { useEffect, useState } from "react";
import { TimelineEvent } from "../../../components/Timeline";
import { useLanguage } from "../../../contexts/LanguageContext";
// import { useScrollDirection } from "../../../hooks/useScrollDirection"; // If you implement scroll direction

export default function EventDetailPage() {
  const params = useParams();
  const eventId = params.id as string;
  const { language } = useLanguage();
  const [dir, setDir] = useState('ltr');
  useEffect(() => {
    setDir(language === 'ar' ? 'rtl' : 'ltr');
  }, [language]);
  // Remove expandedSources and dropdownRefs
  // const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  // const dropdownRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  // Instead, use a local state for each open dropdown
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  // Simple outside click handler: close dropdown on any document click if open
  useEffect(() => {
    if (!openDropdown) return;
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest('button[class*="text-green-400"]')) {
        return;
      }
      setOpenDropdown(null);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [openDropdown]);
  
  // Fetch all events and find the specific one
  const { data: apiData, loading, error, refresh } = useAllEvents(language);
  const [event, setEvent] = useState<TimelineEvent | null>(null);

  useEffect(() => {
    if (apiData && eventId) {
      const bigEvents = transformApiDataToBigEvents(apiData);
      const parts = eventId.split('-');
      if (parts.length >= 3) {
        const bigEventIndex = parseInt(parts[parts.length - 2]);
        const eventIndex = parseInt(parts[parts.length - 1]);
        if (!isNaN(bigEventIndex) && !isNaN(eventIndex) && 
            bigEventIndex >= 0 && bigEventIndex < bigEvents.length) {
          const bigEvent = bigEvents[bigEventIndex];
          if (eventIndex >= 0 && eventIndex < bigEvent.events.length) {
            setEvent(bigEvent.events[eventIndex]);
            return;
          }
        }
      }
      setEvent(null);
    }
  }, [apiData, eventId]);

  // Remove useEffect for outside click

  // Toggle handler for each paragraph
  const toggleSources = (paragraphId: string) => {
    setOpenDropdown(prev => (prev === paragraphId ? null : paragraphId));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#141115] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-green-400">Loading Event Details...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#141115] flex items-center justify-center">
        <div className="text-center bg-[#1A1517]/80 rounded-xl p-8 shadow-lg border-2 border-red-500/30">
          <div className="w-16 h-16 bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">Error Loading Event</h2>
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={refresh}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="min-h-screen bg-[#141115] flex items-center justify-center">
        <div className="text-center bg-[#1A1517]/80 rounded-xl p-8 shadow-lg border-2 border-green-500/30">
          <div className="w-16 h-16 bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">Event Not Found</h2>
          <p className="text-gray-400 mb-4">The requested event could not be found.</p>
          <div className="text-sm text-gray-500 mb-4">
            Debug: Event ID: {eventId} | Language: {language}
          </div>
          <Link href="/timeline" className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
            Back to Timeline
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div dir={dir}>
      {/* Header */}
      <div className="bg-[#1A1517]/80 shadow-sm border-b border-green-500/20">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <Link href="/timeline" className="inline-flex items-center text-green-400 hover:text-red-400 mb-4">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Timeline
          </Link>
          <motion.div
            initial={{ opacity: 0, y: 60 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
              {event.event_name}
            </h1>
            <div className="flex flex-wrap items-center gap-4">
              <time className="inline-flex items-center px-3 py-1 bg-[#141115] text-green-400 border border-green-500/40 rounded-full text-lg font-bold shadow-md">
                {event.date.milady.start} - {event.date.milady.end} AD
              </time>
              {event.date.hijry && (
                <span className="inline-flex items-center px-3 py-1 bg-[#141115] text-red-400 border border-red-500/40 rounded-full text-lg font-bold shadow-md">
                  {event.date.hijry.start} - {event.date.hijry.end} AH
                  {event.date.hijry.approx && " (approx)"}
                </span>
              )}
            </div>
          </motion.div>
        </div>
      </div>
      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-[#1A1517]/80 rounded-2xl shadow-lg border-2 border-green-500/20 overflow-hidden"
        >
          {event.sections.map((section, sectionIndex) => (
            <div key={sectionIndex} className="p-8 border-b border-green-500/10 last:border-b-0">
              <h2 className="text-2xl font-bold text-green-400 mb-6">
                {section.subtitle}
              </h2>
              {section.paragraphs.map((paragraph, paragraphIndex) => (
                <div key={paragraph.paragraph_id || paragraphIndex} className="mb-8 last:mb-0">
                  <p className="text-lg text-gray-200 leading-relaxed mb-4">
                    {paragraph.text}
                  </p>
                  {paragraph.source_URLs && paragraph.source_URLs.length > 0 && (
                    <div className="relative">
                      <button
                        onClick={e => {
                          e.stopPropagation();
                          toggleSources(paragraph.paragraph_id);
                        }}
                        className="text-green-400 hover:text-red-400 font-semibold underline text-sm"
                      >
                        {openDropdown === paragraph.paragraph_id ? "Hide Sources" : "Show Sources"}
                      </button>
                      {openDropdown === paragraph.paragraph_id && (
                        <div 
                          className="absolute left-0 mt-2 w-72 bg-[#141115] border border-green-500/30 rounded-xl shadow-lg p-4 z-20"
                        >
                          <h3 className="text-green-400 font-bold mb-2 text-sm">Sources</h3>
                          <ul className="list-disc list-inside text-gray-300 text-sm">
                            {paragraph.source_URLs.map((url, i) => (
                              <li key={i} className="mb-1">
                                <a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-red-400 underline break-all">{url}</a>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
} 