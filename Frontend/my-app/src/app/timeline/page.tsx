"use client";
import Timeline from "../../components/Timeline";
import Image from "next/image";
import { useAllEvents } from "../../hooks/useApi";
import { transformApiDataToBigEvents } from "../../utils/dataTransformer";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useLanguage } from "../../contexts/LanguageContext";
import { useSearch } from '../../contexts/SearchContext';

export default function TimelinePage() {
  const { language } = useLanguage();
  const [dir, setDir] = useState('ltr');
  useEffect(() => {
    setDir(language === 'ar' ? 'rtl' : 'ltr');
  }, [language]);
  const { data: apiData, loading, error, refresh } = useAllEvents(language);
  const { searchQuery } = useSearch();
  
  // Debug logging
  useEffect(() => {
    console.log('API Data received:', apiData);
    console.log('API Data type:', typeof apiData);
    console.log('Is Array:', Array.isArray(apiData));
    if (apiData) {
      console.log('API Data structure:', JSON.stringify(apiData, null, 2));
      console.log('API Data length:', Array.isArray(apiData) ? apiData.length : 'Not an array');
    }
  }, [apiData]);
  
  // Transform API data to big events structure with better error handling
  const bigEvents = (() => {
    if (!apiData) {
      return [];
    }
    try {
      const transformedBigEvents = transformApiDataToBigEvents(apiData);
      // If no search query, return all
      if (!searchQuery.trim()) return transformedBigEvents;
      // Filter events by search query (title or description)
      const q = searchQuery.trim().toLowerCase();
      return transformedBigEvents
        .map(be => ({
          ...be,
          events: be.events.filter(ev => {
            // Check event_name, article_title
            if (
              ev.event_name.toLowerCase().includes(q) ||
              ev.article_title.toLowerCase().includes(q)
            ) return true;
            // Check all paragraphs in all sections
            return ev.sections.some(section =>
              section.paragraphs.some(p => p.text.toLowerCase().includes(q))
            );
          })
        }))
        .filter(be => be.events.length > 0); // Only periods with at least one match
    } catch {
      return [];
    }
  })();

  console.log('Final bigEvents array:', bigEvents);
  console.log('BigEvents length:', bigEvents.length);

  if (loading) {
    return (
      <div className="relative min-h-screen">
        <Image
          src="/assets/still-life-soldier-helmet.webp"
          alt="Historical Moroccan Military Background"
          fill
          className="object-cover brightness-50"
          style={{ zIndex: 0 }}
        />
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="text-center bg-white/90 backdrop-blur-sm rounded-xl p-8 shadow-lg">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900">Loading Historical Events...</h2>
            <p className="text-gray-600 mt-2">Please wait while we fetch the timeline data.</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="relative min-h-screen">
        <Image
          src="/assets/still-life-soldier-helmet.webp"
          alt="Historical Moroccan Military Background"
          fill
          className="object-cover brightness-50"
          style={{ zIndex: 0 }}
        />
        <div className="relative z-10 flex items-center justify-center min-h-screen">
          <div className="text-center bg-white/90 backdrop-blur-sm rounded-xl p-8 shadow-lg">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Events</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={refresh}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div dir={dir}>
      {/* Background Image */}
      <Image
        src="/assets/still-life-soldier-helmet.webp"
        alt="Historical Moroccan Military Background"
        fill
        className="object-cover brightness-50 min-h-screen"
        style={{ zIndex: 0 }}
      />
      
      {/* Content Overlay */}
      <div className="relative z-10 pt-20 pb-10">
        {bigEvents.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Timeline bigEvents={bigEvents} />
          </motion.div>
        ) : (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="text-center bg-white/90 backdrop-blur-sm rounded-xl p-8 shadow-lg">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">No Events Found</h2>
              <p className="text-gray-600">
                No historical events available for the selected language.
              </p>
              <div className="mt-4 text-sm text-gray-500">
                Debug: API Data received: {apiData ? 'Yes' : 'No'} | BigEvents count: {bigEvents.length}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 