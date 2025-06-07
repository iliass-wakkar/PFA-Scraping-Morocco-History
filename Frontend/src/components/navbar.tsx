import { useState, useEffect } from 'react';
import { Link } from 'react-router'; // Updated import path
import { GiFlexibleStar } from "react-icons/gi";

const Navbar: React.FC = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const [activeSection, setActiveSection] = useState('homepage');

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);

            // Update active section based on scroll position
            const sections = ['homepage','about', 'history'];
            sections.forEach(section => {
                const element = document.getElementById(section);
                if (element && section !== 'homepage') {
                    const rect = element.getBoundingClientRect();
                    if (rect.top <= 100 && rect.bottom >= 100) {
                        setActiveSection(section);
                    }
                }
                else if (element && section === 'homepage') {
                    const isAtTop = window.scrollY < 100;
                    if (isAtTop) {
                        setActiveSection('homepage');
                    }
                }
            });
        };

        window.addEventListener('scroll', handleScroll);
        return () => {
            window.removeEventListener('scroll', handleScroll);
        };
    }, []);

    const toggleMenu = () => {
        setIsMenuOpen(!isMenuOpen);
    };

    // Scroll to section function
    const scrollToSection = (sectionId: string) => {
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

    // Check if section is active
    const isActive = (sectionId: string) => {
        return activeSection === sectionId;
    };

    // Handle language change without page reload
    const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newLang = e.target.value;
        localStorage.setItem("lang", newLang);
        window.dispatchEvent(new Event('languagechange'));
        window.location.reload();
    };

    return (
        <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? 'bg-black/80 backdrop-blur-sm' : ''}`}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-24">
                    {/* Logo and Title with Moroccan styling */}
                    <div className="flex-shrink-0 flex items-center">
                        <button onClick={() => scrollToSection('homepage')} className="flex gap-2 items-center group">
                            <div className="relative h-12 w-12 flex items-center justify-center">
                                <div className="absolute inset-0 bg-green-600 rotate-45 transform transition-transform duration-500 group-hover:rotate-90 rounded-sm"></div>
                                <GiFlexibleStar className="h-8 w-8 relative z-10 text-white group-hover:animate-pulse" />
                            </div>
                            <div className="ml-3">
                                <span className={`text-2xl font-bold text-gray-200 font-serif main-font`}>TarikhAlHuroob</span>
                                <span className={`text-[0.55rem] block text-gray-300 tracking-wider arabic-secondary`}>
                                    <span className="arabic">تاريخ الحروب المغربية </span>| History of Moroccan Wars
                                </span>
                            </div>
                        </button>
                    </div>

                    {/* Desktop Navigation with ornate styling */}
                    <div className="hidden md:block">
                        <div className="ml-10 flex items-center space-x-1 arabic-secondary">
                            <button
                                onClick={() => scrollToSection('homepage')}
                                className={`relative px-4 py-2 text-sm font-medium transition-all duration-300 ${isActive('homepage') ? 'text-green-600' : 'text-gray-300 hover:text-green-600'}`}
                            >
                                <span>Home</span>
                                {isActive('homepage') && (
                                    <span className="absolute bottom-0 left-0 w-full h-0.5 bg-green-600"></span>
                                )}
                            </button>
                            <button
                                onClick={() => scrollToSection('about')}
                                className={`relative px-4 py-2 text-sm font-medium transition-all duration-300 ${isActive('about') ? 'text-green-600' : 'text-gray-300 hover:text-green-600'}`}
                            >
                                <span>About</span>
                                {isActive('about') && (
                                    <span className="absolute bottom-0 left-0 w-full h-0.5 bg-green-600"></span>
                                )}
                            </button>
                            <button
                                onClick={() => scrollToSection('history')}
                                className={`relative px-4 py-2 text-sm font-medium transition-all duration-300 ${isActive('history') ? 'text-green-600' : 'text-gray-300 hover:text-green-600'}`}
                            >
                                <span>History</span>
                                {isActive('history') && (
                                    <span className="absolute bottom-0 left-0 w-full h-0.5 bg-green-600"></span>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Language Selector with ornate styling */}
                    <div className="hidden md:flex items-center">
                        <div className="relative">
                            <select
                                className="appearance-none arabic-secondary bg-white border border-green-700 text-gray-700 pl-4 pr-8 py-1 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-transparent"
                                onChange={handleLanguageChange}
                                value={localStorage.getItem("lang") || 'en'}
                            >
                                <option value="en" className="bg-white main-font">🇺🇸 English</option>
                                <option value="ar" className="bg-white">🇲🇦 العربية</option>
                                <option value="fr" className="bg-white main-font">🇫🇷 Français</option>
                            </select>
                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-green-700">
                                <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                                    <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    {/* Mobile Menu Button with Moroccan styling */}
                    <div className="md:hidden flex items-center">
                        <button
                            onClick={toggleMenu}
                            className={`inline-flex items-center justify-center p-2 rounded-md text-gray-300 hover:text-green-700 hover:bg-gray-100 focus:outline-none`}
                            aria-expanded={isMenuOpen}
                        >
                            <span className="sr-only">Open main menu</span>
                            {!isMenuOpen ? (
                                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            ) : (
                                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Menu with Moroccan patterns */}
            {isMenuOpen && (
                <div className="md:hidden bg-white border-t border-green-600 shadow-lg">
                    <div className="px-2 pt-8 pb-3 space-y-1 sm:px-3 arabic-secondary">
                        <button
                            onClick={() => scrollToSection('homepage')}
                            className={`w-full text-left block px-3 py-2 rounded-md text-base font-medium ${isActive('homepage')
                                ? 'bg-gray-100 text-green-700 border-l-4 border-green-600'
                                : 'text-gray-700 hover:bg-gray-100 hover:text-green-700'
                                }`}
                        >
                            Home
                        </button>
                        <button
                            onClick={() => scrollToSection('about')}
                            className={`w-full text-left block px-3 py-2 rounded-md text-base font-medium ${isActive('about')
                                ? 'bg-gray-100 text-green-700 border-l-4 border-green-600'
                                : 'text-gray-700 hover:bg-gray-100 hover:text-green-700'
                                }`}
                        >
                            About
                        </button>
                        <button
                            onClick={() => scrollToSection('history')}
                            className={`w-full text-left block px-3 py-2 rounded-md text-base font-medium ${isActive('history')
                                ? 'bg-gray-100 text-green-700 border-l-4 border-green-600'
                                : 'text-gray-700 hover:bg-gray-100 hover:text-green-700'
                                }`}
                        >
                            History
                        </button>
                    </div>
                    <div className="flex justify-center border-t border-gray-200 px-5 py-3">
                        <select
                            className="w-full appearance-none bg-white border border-green-700 text-gray-700 px-4 py-2 rounded-md text-sm focus:outline-none arabic-secondary"
                            onChange={handleLanguageChange}
                            value={localStorage.getItem("lang") || 'en'}
                        >
                            <option value="en" className="bg-white main-font">🇺🇸 English</option>
                            <option value="ar" className="bg-white">🇲🇦 العربية</option>
                            <option value="fr" className="bg-white main-font">🇫🇷 Français</option>
                        </select>
                    </div>

                    {/* Decorative pattern */}
                    <div className="px-4 py-2 flex justify-center">
                        <div className="w-full h-0.5 bg-green-600 opacity-30"></div>
                    </div>
                </div>
            )}
        </nav>
    );
};

export default Navbar;