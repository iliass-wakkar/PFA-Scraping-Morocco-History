"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAllEvents } from "../../../hooks/useApi";
import { useEffect, useState, useRef } from "react";
import { TimelineEvent } from "../../../components/Timeline";
import { useLanguage } from "../../../contexts/LanguageContext";
// import { useScrollDirection } from "../../../hooks/useScrollDirection"; // If you implement scroll direction

export default function EventDetailPage() {
  // Scroll to top on mount
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

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

  // Ref for the open dropdown
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  // Only close dropdown when clicking outside
  useEffect(() => {
    if (!openDropdown) return;
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (dropdownRef.current && dropdownRef.current.contains(target)) {
        // Clicked inside the dropdown, do not close
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
      let foundEvent: TimelineEvent | null = null;
      const searchedName = decodeURIComponent(eventId);
      const allNames: string[] = [];
      outer: for (const bigEvent of apiData) {
        for (let eventIndex = 0; eventIndex < bigEvent.events.length; eventIndex++) {
          const event = bigEvent.events[eventIndex];
          allNames.push(event.event_name);
          if (event.event_name === searchedName) {
            foundEvent = {
              event_name: event.event_name,
              article_title: event.article_title,
              date: {
                milady: {
                  start: event.date?.milady?.start || 0,
                  end: event.date?.milady?.end || event.date?.milady?.start || 0
                },
                hijry: event.date?.hijri ? {
                  start: event.date.hijri.start,
                  end: event.date.hijri.end || event.date.hijri.start,
                  approx: false
                } : undefined
              },
              sections: event.sections.map(section => ({
                subtitle: section.subtitle,
                paragraphs: section.paragraphs.map(paragraph => ({
                  paragraph_id: paragraph.paragraph_id || `${section.subtitle}-${paragraph.text.substring(0, 10)}`,
                  text: paragraph.text,
                  source_URLs: paragraph.source_URLs || []
                }))
              }))
            };
            break outer;
          }
        }
      }
      setEvent(foundEvent);
    }
  }, [apiData, eventId]);

  // Helper function to generate event ID (same as in Timeline and Navbar)
  // Removed getEventId as it is no longer used

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
              {event.article_title}
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
                          ref={dropdownRef}
                          onMouseDown={e => e.stopPropagation()}
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