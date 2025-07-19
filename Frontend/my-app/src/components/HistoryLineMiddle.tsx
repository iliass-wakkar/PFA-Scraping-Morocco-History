import React, { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { formatDate } from "../utils/dateUtils";

export interface Section {
    subtitle: string;
    paragraphs: {
        text: string;
    }[];
}

export interface PeriodEvent {
    event_name: string;
    article_title: string;
    date: string;
    sections: Section[];
}

interface HistoryLineMiddleProps {
    event: PeriodEvent;
    index: number;
    date: string;
    eventId: string;
}

const HistoryLineMiddle: React.FC<HistoryLineMiddleProps> = ({ event, index, date, eventId }) => {
    const [Lang] = useState(typeof window !== 'undefined' ? localStorage.getItem("lang") || "en" : "en");
    const [calendar] = useState<'hijri' | 'gregorian'>(typeof window !== 'undefined' ? (localStorage.getItem("calendar") as 'hijri' | 'gregorian') || 'gregorian' : 'gregorian');
    const [isHovered, setIsHovered] = useState(false);
    const isEven = index % 2 === 0;

    return (
        <div className="relative mx-auto flex w-full min-h-[600px] flex-col gap-1 bg-[#141115]">
            {/* Timeline Line */}
            <motion.div
                className="absolute inset-0 flex justify-center"
                initial={{ scaleY: 0 }}
                whileInView={{ scaleY: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1, delay: 0.5 }}
                style={{ transformOrigin: 'top' }}
            >
                <div className="w-[2px] h-[130%] bg-gradient-to-b from-green-600/30 via-red-600/50 to-green-600/30 "></div>
            </motion.div>
            {/* Main Content Container */}
            {/* Mobile (md and below): stacked layout */}
            <motion.div
                className="block lg:hidden relative flex flex-col items-center justify-center min-h-[400px] py-24"
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7, delay: index * 0.08 }}
            >
                {/* Event Circle */}
                <div className="z-50 mb-6">
                    <div
                        className="relative w-8 h-8 bg-gradient-to-br from-green-400 via-red-500 to-green-600 rounded-full transform cursor-pointer hover:scale-150 transition-all duration-300 flex items-center justify-center"
                        onMouseEnter={() => setIsHovered(true)}
                        onMouseLeave={() => setIsHovered(false)}
                    >
                        <div className="absolute w-12 h-12 rounded-full bg-green-500/20 animate-pulse"></div>
                        <div className="absolute w-6 h-6 rounded-full bg-red-400/80"></div>
                        <div className="absolute w-3 h-3 rounded-full bg-white/90"></div>
                    </div>
                </div>
                {/* Date Display */}
                <div className="w-full flex justify-center">
                    <div className="text-2xl md:text-3xl font-bold text-green-400 bg-[#1A1517]/80 px-8 py-4 rounded-2xl border-2 border-green-500/20 backdrop-blur-sm shadow-[0_0_15px_rgba(34,197,94,0.1)] hover:shadow-[0_0_25px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300">
                        {formatDate(date, Lang, calendar)}
                    </div>
                </div>
                {/* Content Container */}
                <div className="w-full flex flex-col items-center mt-8">
                    <Link href={`/event/${eventId}`}>
                        <div className={`w-full max-w-2xl bg-[#1A1517]/80 backdrop-blur-sm p-8 rounded-2xl border-2 border-green-500/20 shadow-[0_0_25px_rgba(34,197,94,0.1)] hover:shadow-[0_0_35px_rgba(239,68,68,0.2)] hover:border-red-500/30 transition-all duration-300 ${isHovered ? 'scale-105' : 'scale-100'}`}
                            onMouseEnter={() => setIsHovered(true)}
                            onMouseLeave={() => setIsHovered(false)}
                        >
                            <h3 className="text-2xl md:text-3xl font-bold text-white mb-6">{event.article_title}</h3>
                            {event.sections && event.sections[0] && (
                                <div>
                                    <h4 className="text-green-400/90 mb-4 font-semibold text-lg md:text-xl">{event.sections[0].subtitle}</h4>
                                    <p className="leading-8 text-gray-300/80">{event.sections[0].paragraphs[0]?.text}</p>
                                    <div className="text-green-400 py-2 rounded-lg transition-all duration-300 flex items-center gap-2 group mt-4">
                                        {Lang === "en" ? "Read More" : Lang === "ar" ? "اقرأ المزيد" : "Lire la suite"}
                                        <span className="ml-2 w-4 h-4 inline-block group-hover:translate-x-1 transition-all duration-300">
                                            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-4 h-4 text-red-500"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </Link>
                </div>
            </motion.div>
            {/* Desktop (lg and up): original layout */}
            <motion.div
                className={`hidden lg:flex relative items-center justify-center min-h-[400px] py-24`}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7, delay: index * 0.08 }}
            >
                {/* Event Circle */}
                <div className="absolute left-1/2 transform -translate-x-1/2 z-50 ">
                    <div
                        className={`relative w-8 h-8 bg-gradient-to-br from-green-400 via-red-500 to-green-600 rounded-full transform cursor-pointer hover:scale-150 transition-all duration-300 flex items-center justify-center`}
                        onMouseEnter={() => setIsHovered(true)}
                        onMouseLeave={() => setIsHovered(false)}
                    >
                        <div className="absolute w-12 h-12 rounded-full bg-green-500/20 animate-pulse"></div>
                        <div className="absolute w-6 h-6 rounded-full bg-red-400/80"></div>
                        <div className="absolute w-3 h-3 rounded-full bg-white/90"></div>
                    </div>
                </div>
                {/* Date Display */}
                <div className={`absolute w-[38%] ${isEven ? 'right-[8%]' : 'left-[8%]'} flex ${isEven ? 'justify-start' : 'justify-end'} items-center transition-all duration-700 delay-300`}>
                    <div className="text-2xl md:text-3xl font-bold text-green-400 bg-[#1A1517]/80 px-8 py-4 rounded-2xl border-2 border-green-500/20 backdrop-blur-sm shadow-[0_0_15px_rgba(34,197,94,0.1)] hover:shadow-[0_0_25px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300">
                        {formatDate(date, Lang, calendar)}
                    </div>
                </div>
                {/* Content Container */}
                <div className={`absolute ${isEven ? 'left-[8%]' : 'right-[8%]'} w-[38%] flex flex-col ${isEven ? 'items-start' : 'items-end'} transition-all duration-700 delay-500 z-50`}>
                    <Link href={`/event/${eventId}`}>
                        <div className={`w-full max-w-2xl bg-[#1A1517]/80 backdrop-blur-sm p-8 rounded-2xl border-2 border-green-500/20 shadow-[0_0_25px_rgba(34,197,94,0.1)] hover:shadow-[0_0_35px_rgba(239,68,68,0.2)] hover:border-red-500/30 transition-all duration-300 ${isHovered ? 'scale-105' : 'scale-100'}`}
                            onMouseEnter={() => setIsHovered(true)}
                            onMouseLeave={() => setIsHovered(false)}
                        >
                            <h3 className="text-2xl md:text-3xl font-bold text-white mb-6">{event.article_title}</h3>
                            {event.sections && event.sections[0] && (
                                <div>
                                    <h4 className="text-green-400/90 mb-4 font-semibold text-lg md:text-xl">{event.sections[0].subtitle}</h4>
                                    <p className="leading-8 text-gray-300/80">{event.sections[0].paragraphs[0]?.text}</p>
                                    <div className="text-green-400 py-2 rounded-lg transition-all duration-300 flex items-center gap-2 group mt-4">
                                        {Lang === "en" ? "Read More" : Lang === "ar" ? "اقرأ المزيد" : "Lire la suite"}
                                        <span className="ml-2 w-4 h-4 inline-block group-hover:translate-x-1 transition-all duration-300">
                                            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-4 h-4 text-red-500"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </Link>
                </div>
            </motion.div>
        </div>
    );
};

export default HistoryLineMiddle; 