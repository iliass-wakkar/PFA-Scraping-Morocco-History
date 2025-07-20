"use client";
import { useState, useEffect, useRef } from 'react';
import { GiFlexibleStar } from "react-icons/gi";
import { FaSearch } from "react-icons/fa";
import { motion, AnimatePresence } from 'framer-motion';
import i18n from '../i18n';
import { TimelineEvent } from './Timeline';
import { useRouter } from 'next/navigation';
import { useSearchEvents } from '../hooks/useApi';
import { useLanguage } from '../contexts/LanguageContext';

// Helper to generate eventId for routing (copied from Timeline.tsx)
const getEventId = (event: TimelineEvent, bigEventIndex: number, eventIndex: number) => {
  return `${event.event_name.replace(/\s+/g, '-').toLowerCase()}-${bigEventIndex}-${eventIndex}`;
};

const Navbar: React.FC = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const [activeSection, setActiveSection] = useState('homepage');
    const pathname = typeof window !== 'undefined' ? window.location.pathname : '/'; // fallback for SSR
    // Search UI states
    const [searchValue, setSearchValue] = useState('');
    const [showDropdown, setShowDropdown] = useState(false);
    const searchRef = useRef<HTMLDivElement>(null);
    const router = useRouter();
    const mobileMenuRef = useRef<HTMLDivElement>(null);
    const { language, setLanguage } = useLanguage();
    
    // Use API search hook
    const { data: searchResults, loading: searchLoading } = useSearchEvents(searchValue, language);

    useEffect(() => {
        // If on /timeline, always set activeSection to 'history'
        if (pathname.startsWith('/timeline')) {
            setActiveSection('history');
            return;
        }
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
            const sections = ['homepage', 'about', 'history'];
            sections.forEach(section => {
                const element = document.getElementById(section);
                if (element && section !== 'homepage') {
                    const rect = element.getBoundingClientRect();
                    if (rect.top <= 100 && rect.bottom >= 100) {
                        setActiveSection(section);
                    }
                } else if (element && section === 'homepage') {
                    const isAtTop = window.scrollY < 100;
                    if (isAtTop) {
                        setActiveSection('homepage');
                    }
                }
            });
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [pathname]);

    // Dropdown close on outside click
    useEffect(() => {
        if (!showDropdown) return;
        function handleClickOutside(event: MouseEvent) {
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setShowDropdown(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showDropdown]);

    // Close mobile menu on outside click
    useEffect(() => {
        if (!isMenuOpen) return;
        function handleClickOutside(event: MouseEvent) {
            if (mobileMenuRef.current && !mobileMenuRef.current.contains(event.target as Node)) {
                setIsMenuOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isMenuOpen]);

    const scrollToSection = (sectionId: string) => {
        const isOnTimeline = pathname === '/timeline';
        const isOnEvent = pathname.startsWith('/event/');
        
        // Handle navigation from timeline or event pages
        if (isOnTimeline || isOnEvent) {
            if (sectionId === 'homepage') {
                window.location.href = '/';
            } else if (sectionId === 'about') {
                window.location.href = '/#about';
            } else if (sectionId === 'history') {
                // Already on timeline page, do nothing or refresh
                if (isOnTimeline) {
                    window.location.reload();
                } else {
                    window.location.href = '/timeline';
                }
            }
            setIsMenuOpen(false);
            return;
        }
        
        // Handle navigation from homepage
        if (sectionId === 'homepage') {
            window.scrollTo({ top: 0, behavior: 'smooth' });
            setActiveSection('homepage');
        } else if (sectionId === 'about') {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
            setActiveSection('about');
        } else if (sectionId === 'history') {
            // Navigate to timeline page
            window.location.href = '/timeline';
        }
        
        setIsMenuOpen(false);
    };

    const isActive = (sectionId: string) => activeSection === sectionId;

    const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newLang = e.target.value;
        localStorage.setItem("lang", newLang);
        setLanguage(newLang); // Update the context
        i18n.changeLanguage(newLang); // Update i18next language
        window.dispatchEvent(new Event('languagechange'));
    };

    // Search UI handlers
    const handleSearchFocus = () => setShowDropdown(true);
    const handleSearchButtonClick = () => setShowDropdown(true);
    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => setSearchValue(e.target.value);

    // Transform search results to match the expected format
    const transformedSearchResults = searchResults.flatMap((bigEvent, bigEventIndex) =>
        bigEvent.events.map((event, eventIndex) => ({
            event: {
                ...event,
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
                }
            } as TimelineEvent,
            bigEventIndex,
            eventIndex
        }))
    );

    const navItems = [
        { id: 'homepage', label: { en: 'Home', ar: 'الرئيسية', fr: 'Accueil', es: 'Inicio' } },
        { id: 'about', label: { en: 'About', ar: 'حول', fr: 'À propos', es: 'Acerca de' } },
        { id: 'history', label: { en: 'History', ar: 'التاريخ', fr: 'Histoire', es: 'Historia' } }
    ];

    return (
        <motion.nav 
            className={`fixed top-0 w-full z-50 bg-black transition-all duration-300 ${
                scrolled ? 'shadow-lg shadow-black/10' : ''
            }`}
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-20">
                    {/* Logo */}
                    <motion.div 
                        className="flex-shrink-0"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <button onClick={() => scrollToSection('homepage')} className="flex items-center gap-3 group">
                            <div className="relative h-10 w-10 flex items-center justify-center">
                                <motion.div 
                                    className="absolute inset-0 bg-gradient-to-r from-green-500 to-green-600 rounded-lg"
                                    animate={{ rotate: [0, 360] }}
                                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                                />
                                <GiFlexibleStar className="h-6 w-6 relative z-10 text-white" />
                            </div>
                            <div>
                                <span className="text-xl font-bold text-white font-serif main-font tracking-wide">
                                    TarikhAlHuroob
                                </span>
                                <span className="text-[0.6rem] block text-gray-300 tracking-wider arabic-secondary">
                                    <span className="arabic">تاريخ الحروب المغربية </span>| History of Moroccan Wars
                                </span>
                            </div>
                        </button>
                    </motion.div>

                    {/* Search Bar (Desktop) */}
                    <div className="hidden md:flex items-center mx-6 flex-1 max-w-xs" ref={searchRef}>
                        <div className="relative w-full">
                            <input
                                type="text"
                                value={searchValue}
                                onChange={handleSearchChange}
                                onFocus={handleSearchFocus}
                                placeholder={language === 'en' ? 'Search...' : language === 'ar' ? 'بحث...' : language === 'fr' ? 'Recherche...' : 'Buscar...'}
                                className="w-full py-2 pl-4 pr-10 rounded-lg bg-black/40 text-white border border-green-600/30 focus:outline-none focus:ring-2 focus:ring-green-600/50 focus:border-transparent transition-all duration-300 placeholder-gray-400 shadow-lg shadow-black/10"
                            />
                            <button
                                className="absolute right-2 top-1/2 -translate-y-1/2 text-green-400 hover:text-green-300 p-1"
                                tabIndex={-1}
                                type="button"
                                onClick={handleSearchButtonClick}
                            >
                                <FaSearch className="w-5 h-5" />
                            </button>
                            
                            {/* Search Dropdown */}
                            <AnimatePresence>
                                {showDropdown && (
                                    <motion.div
                                        initial={{ opacity: 0, y: -10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        transition={{ duration: 0.2 }}
                                        className="absolute top-full left-0 right-0 mt-2 bg-black/95 backdrop-blur-sm border border-green-600/30 rounded-lg shadow-xl max-h-96 overflow-y-auto z-50"
                                    >
                                        {searchLoading ? (
                                            <div className="p-4 text-center text-green-400">
                                                {language === 'en' ? 'Searching...' : language === 'ar' ? 'جاري البحث...' : language === 'fr' ? 'Recherche...' : 'Buscando...'}
                                            </div>
                                        ) : searchValue.trim() === '' ? (
                                            <div className="p-4 text-center text-gray-400">
                                                {language === 'en' ? 'Start typing to search...' : language === 'ar' ? 'ابدأ الكتابة للبحث...' : language === 'fr' ? 'Commencez à taper pour rechercher...' : 'Comience a escribir para buscar...'}
                                            </div>
                                        ) : transformedSearchResults.length === 0 ? (
                                            <div className="p-4 text-center text-gray-400">
                                                {language === 'en' ? 'No results found' : language === 'ar' ? 'لم يتم العثور على نتائج' : language === 'fr' ? 'Aucun résultat trouvé' : 'No se encontraron resultados'}
                                            </div>
                                        ) : (
                                            transformedSearchResults.map(({ event, bigEventIndex, eventIndex }, idx) => {
                                                const eventId = getEventId(event, bigEventIndex, eventIndex);
                                                return (
                                                    <button
                                                        key={event.article_title + idx}
                                                        className="block w-full text-left p-3 border-b border-green-600/10 last:border-b-0 hover:bg-green-600/10 cursor-pointer"
                                                        onClick={() => {
                                                            setSearchValue('');
                                                            setShowDropdown(false);
                                                            router.push(`/event/${eventId}`);
                                                        }}
                                                    >
                                                        <div className="font-semibold text-white">{event.article_title}</div>
                                                        <div className="text-xs text-green-400 mb-1">{event.date.milady.start}{event.date.milady.end !== event.date.milady.start ? ` - ${event.date.milady.end}` : ''}</div>
                                                        <div className="text-gray-300 text-xs line-clamp-2">{event.sections[0]?.paragraphs[0]?.text}</div>
                                                    </button>
                                                );
                                            })
                                        )}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center space-x-8">
                        {navItems.map((item) => (
                            <motion.button
                                key={item.id}
                                onClick={() => scrollToSection(item.id)}
                                className={`relative px-3 py-2 text-sm font-medium transition-colors duration-300 ${
                                    isActive(item.id) 
                                        ? 'text-green-400' 
                                        : 'text-gray-300 hover:text-green-400'
                                }`}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                {item.label[language as keyof typeof item.label] || item.label.en}
                                {isActive(item.id) && (
                                    <motion.div
                                        className="absolute -bottom-1 left-0 right-0 h-0.5 bg-green-400"
                                        layoutId="activeSection"
                                    />
                                )}
                            </motion.button>
                        ))}
                    </div>

                    {/* Language Selector & Mobile Menu Button */}
                    <div className="flex items-center space-x-4">
                        {/* Language Selector */}
                        <div className="relative group">
                            <div className="relative">
                                <select
                                    value={language}
                                    onChange={handleLanguageChange}
                                    className="appearance-none bg-black/40 text-white border border-green-600/30 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-green-600/50 focus:border-transparent transition-all duration-300 cursor-pointer text-sm font-medium shadow-lg shadow-black/10"
                                >
                                    <option value="en">EN</option>
                                    <option value="ar">AR</option>
                                    <option value="fr">FR</option>
                                    <option value="es">ES</option>
                                </select>
                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                                    <svg className="h-5 w-5 text-green-500 transition-transform duration-300 group-hover:translate-y-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                </div>
                            </div>
                        </div>
                        
                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="md:hidden p-2 text-gray-300 hover:text-green-400 transition-colors duration-300"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                {isMenuOpen ? (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                ) : (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                )}
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Mobile Menu */}
                <AnimatePresence>
                    {isMenuOpen && (
                        <motion.div
                            ref={mobileMenuRef}
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3 }}
                            className="md:hidden bg-black/95 backdrop-blur-sm border-t border-green-600/30"
                        >
                            <div className="px-4 py-6 space-y-4">
                                {/* Mobile Navigation */}
                                <div className="space-y-2">
                                    {navItems.map((item) => (
                                        <button
                                            key={item.id}
                                            onClick={() => scrollToSection(item.id)}
                                            className={`block w-full text-left px-4 py-3 rounded-lg transition-colors duration-300 ${
                                                isActive(item.id) 
                                                    ? 'bg-green-600/20 text-green-400' 
                                                    : 'text-gray-300 hover:bg-green-600/10 hover:text-green-400'
                                            }`}
                                        >
                                            {item.label[language as keyof typeof item.label] || item.label.en}
                                        </button>
                                    ))}
                                </div>
                                
                                {/* Search Bar (Mobile) */}
                                <div className="w-full mb-3 md:hidden" ref={searchRef}>
                                    <div className="relative w-full">
                                        <input
                                            type="text"
                                            value={searchValue}
                                            onChange={handleSearchChange}
                                            onFocus={handleSearchFocus}
                                            placeholder={language === 'en' ? 'Search...' : language === 'ar' ? 'بحث...' : language === 'fr' ? 'Recherche...' : 'Buscar...'}
                                            className="w-full py-2 pl-4 pr-10 rounded-lg bg-black/40 text-white border border-green-600/30 focus:outline-none focus:ring-2 focus:ring-green-600/50 focus:border-transparent transition-all duration-300 placeholder-gray-400 shadow-lg shadow-black/10"
                                        />
                                        <button
                                            className="absolute right-2 top-1/2 -translate-y-1/2 text-green-400 hover:text-green-300 p-1"
                                            tabIndex={-1}
                                            type="button"
                                            onClick={handleSearchButtonClick}
                                        >
                                            <FaSearch className="w-5 h-5" />
                                        </button>
                                        
                                        {/* Mobile Search Dropdown */}
                                        <AnimatePresence>
                                            {showDropdown && (
                                                <motion.div
                                                    initial={{ opacity: 0, y: -10 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    exit={{ opacity: 0, y: -10 }}
                                                    transition={{ duration: 0.2 }}
                                                    className="absolute top-full left-0 right-0 mt-2 bg-black/95 backdrop-blur-sm border border-green-600/30 rounded-lg shadow-xl max-h-96 overflow-y-auto z-50"
                                                >
                                                    {searchLoading ? (
                                                        <div className="p-4 text-center text-green-400">
                                                            {language === 'en' ? 'Searching...' : language === 'ar' ? 'جاري البحث...' : language === 'fr' ? 'Recherche...' : 'Buscando...'}
                                                        </div>
                                                    ) : searchValue.trim() === '' ? (
                                                        <div className="p-4 text-center text-gray-400">
                                                            {language === 'en' ? 'Start typing to search...' : language === 'ar' ? 'ابدأ الكتابة للبحث...' : language === 'fr' ? 'Commencez à taper pour rechercher...' : 'Comience a escribir para buscar...'}
                                                        </div>
                                                    ) : transformedSearchResults.length === 0 ? (
                                                        <div className="p-4 text-center text-gray-400">
                                                            {language === 'en' ? 'No results found' : language === 'ar' ? 'لم يتم العثور على نتائج' : language === 'fr' ? 'Aucun résultat trouvé' : 'No se encontraron resultados'}
                                                        </div>
                                                    ) : (
                                                        transformedSearchResults.map(({ event, bigEventIndex, eventIndex }, idx) => {
                                                            const eventId = getEventId(event, bigEventIndex, eventIndex);
                                                            return (
                                                                <button
                                                                    key={event.article_title + idx}
                                                                    className="block w-full text-left p-3 border-b border-green-600/10 last:border-b-0 hover:bg-green-600/10 cursor-pointer"
                                                                    onClick={() => {
                                                                        setSearchValue('');
                                                                        setShowDropdown(false);
                                                                        setIsMenuOpen(false); // Close mobile menu
                                                                        router.push(`/event/${eventId}`);
                                                                    }}
                                                                >
                                                                    <div className="font-semibold text-white">{event.article_title}</div>
                                                                    <div className="text-xs text-green-400 mb-1">{event.date.milady.start}{event.date.milady.end !== event.date.milady.start ? ` - ${event.date.milady.end}` : ''}</div>
                                                                    <div className="text-gray-300 text-xs line-clamp-2">{event.sections[0]?.paragraphs[0]?.text}</div>
                                                                </button>
                                                            );
                                                        })
                                                    )}
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.nav>
    );
};

export default Navbar; 