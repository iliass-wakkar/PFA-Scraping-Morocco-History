"use client";
import { useState, useEffect, useRef } from 'react';
import { GiFlexibleStar } from "react-icons/gi";
import { FaSearch } from "react-icons/fa";
import { motion, AnimatePresence } from 'framer-motion';
import i18n from '../i18n';
import { useTimelineData } from '../contexts/TimelineDataContext';
import { TimelineEvent } from './Timeline';
import { useRouter } from 'next/navigation';

// Helper to generate eventId for routing (copied from Timeline.tsx)
const getEventId = (event: TimelineEvent, bigEventIndex: number, eventIndex: number) => {
  return `${event.event_name.replace(/\s+/g, '-').toLowerCase()}-${bigEventIndex}-${eventIndex}`;
};

const Navbar: React.FC = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const [activeSection, setActiveSection] = useState('homepage');
    const [lang, setLang] = useState(typeof window !== 'undefined' ? localStorage.getItem("lang") || "en" : "en");
    const pathname = typeof window !== 'undefined' ? window.location.pathname : '/'; // fallback for SSR
    // Search UI states
    const [searchValue, setSearchValue] = useState('');
    const [showDropdown, setShowDropdown] = useState(false);
    const searchRef = useRef<HTMLDivElement>(null);
    const { bigEvents } = useTimelineData();
    // Instead of just TimelineEvent[], keep event, bigEventIndex, eventIndex
    const [filteredEvents, setFilteredEvents] = useState<{ event: TimelineEvent; bigEventIndex: number; eventIndex: number }[]>([]);
    const debounceTimeout = useRef<NodeJS.Timeout | null>(null);
    const router = useRouter();
    const mobileMenuRef = useRef<HTMLDivElement>(null);

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

    // Debounced search logic
    useEffect(() => {
        if (!showDropdown) return;
        if (debounceTimeout.current) clearTimeout(debounceTimeout.current);
        debounceTimeout.current = setTimeout(() => {
            const query = searchValue.trim();
            if (!query) {
                setFilteredEvents([]);
                return;
            }
            const isNumber = /^\d+$/.test(query);
            const lowerQuery = query.toLowerCase();
            // Flatten events with indices
            const allEvents = bigEvents.flatMap((be, bigEventIndex) =>
                be.events.map((event, eventIndex) => ({ event, bigEventIndex, eventIndex }))
            );
            const filtered: { event: TimelineEvent; bigEventIndex: number; eventIndex: number }[] = allEvents.filter(({ event }) => {
                if (isNumber) {
                    const year = parseInt(query, 10);
                    return (
                        event.date.milady.start === year ||
                        event.date.milady.end === year
                    );
                } else {
                    const inTitle = event.article_title.toLowerCase().includes(lowerQuery);
                    const inFirstParagraph = event.sections[0]?.paragraphs[0]?.text?.toLowerCase().includes(lowerQuery);
                    return inTitle || inFirstParagraph;
                }
            });
            setFilteredEvents(filtered);
        }, 400);
        return () => {
            if (debounceTimeout.current) clearTimeout(debounceTimeout.current);
        };
    }, [searchValue, bigEvents, showDropdown]);

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
        if (isOnTimeline || isOnEvent) {
            if (sectionId === 'homepage') {
                window.location.href = '/';
            } else if (sectionId === 'about') {
                window.location.href = '/#about';
            }
            setIsMenuOpen(false);
            return;
        }
        if (sectionId === 'homepage') {
            window.scrollTo({ top: 0, behavior: 'smooth' });
            setActiveSection('homepage');
        } else {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        }
        setIsMenuOpen(false);
    };

    const isActive = (sectionId: string) => activeSection === sectionId;

    const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newLang = e.target.value;
        localStorage.setItem("lang", newLang);
        setLang(newLang);
        i18n.changeLanguage(newLang); // Update i18next language
        window.dispatchEvent(new Event('languagechange'));
    };

    // Search UI handlers
    const handleSearchFocus = () => setShowDropdown(true);
    const handleSearchButtonClick = () => setShowDropdown(true);
    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => setSearchValue(e.target.value);

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
                                placeholder={lang === 'en' ? 'Search...' : lang === 'ar' ? 'بحث...' : lang === 'fr' ? 'Recherche...' : 'Buscar...'}
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
                            <AnimatePresence>
                                {showDropdown && (
                                    <motion.div
                                        initial={{ opacity: 0, y: -10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        transition={{ duration: 0.2 }}
                                        className="absolute left-0 right-0 mt-2 bg-black/90 border border-green-600/30 rounded-lg shadow-lg z-50 p-2 max-h-80 overflow-y-auto"
                                    >
                                        {filteredEvents.length === 0 ? (
                                            <div className="text-gray-300 text-sm p-4">No results found.</div>
                                        ) : (
                                            filteredEvents.map(({ event, bigEventIndex, eventIndex }, idx) => {
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
                    <div className="hidden md:flex items-center space-x-1">
                        <div className="flex items-center gap-2">
                            {/* Home: scroll to top, About: scroll to #about, History: go to /timeline */}
                            <motion.button
                                key="homepage"
                                onClick={() => scrollToSection('homepage')}
                                className={`relative px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 ${
                                    isActive('homepage') 
                                        ? 'text-white bg-green-600/20' 
                                        : 'text-gray-300 hover:text-white hover:bg-white/10'
                                }`}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                <span className="relative z-10">
                                    {lang === 'en' ? 'Home' : lang === 'ar' ? 'الرئيسية' : lang === 'fr' ? 'Accueil' : 'Inicio'}
                                </span>
                                {isActive('homepage') && (
                                    <motion.div
                                        className="absolute bottom-0 left-0 h-0.5 bg-green-500"
                                        initial={{ width: 0 }}
                                        animate={{ width: '100%' }}
                                        transition={{ duration: 0.3 }}
                                    />
                                )}
                            </motion.button>
                            <motion.button
                                key="about"
                                onClick={() => scrollToSection('about')}
                                className={`relative px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 ${
                                    isActive('about') 
                                        ? 'text-white bg-green-600/20' 
                                        : 'text-gray-300 hover:text-white hover:bg-white/10'
                                }`}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                <span className="relative z-10">
                                    {lang === 'en' ? 'About' : lang === 'ar' ? 'حول' : lang === 'fr' ? 'À propos' : 'Acerca de'}
                                </span>
                                {isActive('about') && (
                                    <motion.div
                                        className="absolute bottom-0 left-0 h-0.5 bg-green-500"
                                        initial={{ width: 0 }}
                                        animate={{ width: '100%' }}
                                        transition={{ duration: 0.3 }}
                                    />
                                )}
                            </motion.button>
                            <motion.button
                                key="history"
                                onClick={() => window.location.href = '/timeline'}
                                className={`relative px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 ${
                                    isActive('history') 
                                        ? 'text-white bg-green-600/20' 
                                        : 'text-gray-300 hover:text-white hover:bg-white/10'
                                }`}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                <span className="relative z-10">
                                    {lang === 'en' ? 'History' : lang === 'ar' ? 'التاريخ' : lang === 'fr' ? 'Histoire' : 'Historia'}
                                </span>
                                {isActive('history') && (
                                    <motion.div
                                        className="absolute bottom-0 left-0 h-0.5 bg-green-500"
                                        initial={{ width: 0 }}
                                        animate={{ width: '100%' }}
                                        transition={{ duration: 0.3 }}
                                    />
                                )}
                            </motion.button>
                        </div>

                        {/* Language Selector */}
                        <motion.div 
                            className="ml-6"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <div className="relative group">
                                <select
                                    className="appearance-none bg-black/40 backdrop-blur-lg border border-green-600/30 text-white pl-10 pr-10 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-600/50 focus:border-transparent transition-all duration-300 hover:border-green-600/70 hover:bg-black/60 cursor-pointer shadow-lg shadow-black/10"
                                    onChange={handleLanguageChange}
                                    value={lang}
                                >
                                    <option value="ar" className="bg-gray-900/90 backdrop-blur-lg text-white py-2">🇲🇦 العربية</option>
                                    <option value="en" className="bg-gray-900/90 backdrop-blur-lg text-white py-2">🇺🇸 English</option>
                                    <option value="fr" className="bg-gray-900/90 backdrop-blur-lg text-white py-2">🇫🇷 Français</option>
                                    <option value="es" className="bg-gray-900/90 backdrop-blur-lg text-white py-2">🇪🇸 Español</option>
                                </select>
                                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                    <svg className="h-4 w-4 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                                    </svg>
                                </div>
                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                                    <svg className="h-4 w-4 text-green-500 transition-transform duration-300 group-hover:translate-y-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                </div>
                            </div>
                        </motion.div>
                    </div>

                    {/* Mobile Menu Button */}
                    {!isMenuOpen && (
                        <motion.button
                            onClick={() => setIsMenuOpen(true)}
                            className="md:hidden p-2 rounded-lg text-gray-300 hover:text-white focus:outline-none z-50 relative"
                            aria-label="Open mobile menu"
                            title="Open menu"
                        >
                            <span className="sr-only">Open main menu</span>
                            <div className="w-6 h-6 flex flex-col justify-between items-center">
                                <span className="w-full h-0.5 bg-current transition-all duration-300" />
                                <span className="w-full h-0.5 bg-current transition-all duration-300" />
                                <span className="w-full h-0.5 bg-current transition-all duration-300" />
                            </div>
                        </motion.button>
                    )}
                    {isMenuOpen && (
                        <motion.button
                            onClick={() => setIsMenuOpen(false)}
                            className="md:hidden p-2 rounded-lg text-gray-300 hover:text-white focus:outline-none z-50 relative"
                            aria-label="Close mobile menu"
                            title="Close menu"
                        >
                            <span className="sr-only">Close main menu</span>
                            <div className="w-6 h-6 flex flex-col justify-between items-center">
                                <span className="w-full h-0.5 bg-current transform rotate-45 translate-y-2.5 transition-all duration-300" />
                                <span className="w-full h-0.5 bg-current opacity-0 transition-all duration-300" />
                                <span className="w-full h-0.5 bg-current transform -rotate-45 -translate-y-2.5 transition-all duration-300" />
                            </div>
                        </motion.button>
                    )}
                </div>
            </div>

            {/* Mobile Menu */}
            <AnimatePresence>
                {isMenuOpen && (
                    <motion.div
                        className="md:hidden"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                        ref={mobileMenuRef}
                    >
                        
                        <div className="glass px-4 pt-2 pb-4 space-y-1">
                            {navItems.map((item) => (
                                <motion.button
                                    key={item.id}
                                    onClick={() => {
                                        if (item.id === 'history') {
                                            window.location.href = '/timeline';
                                        } else {
                                            scrollToSection(item.id);
                                        }
                                    }}
                                    className={`w-full text-left px-4 py-3 rounded-lg text-base font-medium transition-all duration-300 ${
                                        isActive(item.id)
                                            ? 'bg-green-600/20 text-white'
                                            : 'text-gray-300 hover:bg-white/10 hover:text-white'
                                    }`}
                                    whileHover={{ x: 10 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    {item.label[lang as keyof typeof item.label]}
                                </motion.button>
                            ))}

                            {/* Mobile Language Selector */}
                            <div className="pt-2 pb-1">
                                <div className="relative group">
                                    <select
                                        className="w-full appearance-none bg-black/40 backdrop-blur-lg border border-green-600/30 text-white pl-12 pr-10 py-3 rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-green-600/50 focus:border-transparent transition-all duration-300 hover:border-green-600/70 hover:bg-black/60 cursor-pointer shadow-lg shadow-black/10"
                                        onChange={handleLanguageChange}
                                        value={lang}
                                    >
                                        <option value="ar" className="bg-gray-900/90 backdrop-blur-lg text-white py-2">🇲🇦 العربية</option>
                                        <option value="en" className="bg-gray-900/90 backdrop-blur-lg text-white py-2">🇺🇸 English</option>
                                        <option value="fr" className="bg-gray-900/90 backdrop-blur-lg text-white py-2">🇫🇷 Français</option>
                                        <option value="es" className="bg-gray-900/90 backdrop-blur-lg text-white py-2">🇪🇸 Español</option>
                                    </select>
                                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                        <svg className="h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                                        </svg>
                                    </div>
                                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                                        <svg className="h-5 w-5 text-green-500 transition-transform duration-300 group-hover:translate-y-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                </div>
                            </div>
                            {/* Search Bar (Mobile) */}
                        <div className="w-full mb-3 md:hidden" ref={searchRef}>
                            <div className="relative w-full">
                                <input
                                    type="text"
                                    value={searchValue}
                                    onChange={handleSearchChange}
                                    onFocus={handleSearchFocus}
                                    placeholder={lang === 'en' ? 'Search...' : lang === 'ar' ? 'بحث...' : lang === 'fr' ? 'Recherche...' : 'Buscar...'}
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
                                <AnimatePresence>
                                    {showDropdown && (
                                        <motion.div
                                            initial={{ opacity: 0, y: -10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: -10 }}
                                            transition={{ duration: 0.2 }}
                                            className="absolute left-0 right-0 mt-2 bg-black/90 border border-green-600/30 rounded-lg shadow-lg z-50 p-2 max-h-80 overflow-y-auto"
                                        >
                                            {filteredEvents.length === 0 ? (
                                                <div className="text-gray-300 text-sm p-4">No results found.</div>
                                            ) : (
                                                filteredEvents.map(({ event, bigEventIndex, eventIndex }, idx) => {
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
        </motion.nav>
    );
};

export default Navbar; 