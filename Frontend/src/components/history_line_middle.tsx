import { useState } from "react";
import { useRevealAnimation } from "../hooks/useRevealAnimation";
import { formatDate } from "../utils/dateUtils";

interface Section {
    subtitle: string;
    paragraphs: {
        text: string;
    }[];
}

interface PeriodEvent {
    event_name: string;
    article_title: string;
    date: string;
    sections: Section[];
}

interface HistoryLineMiddleProps {
    event: PeriodEvent;
    index: number;
    date: string;
}

const HistoryLineMiddle = ({ event, index, date }: HistoryLineMiddleProps) => {
    const [Lang] = useState(localStorage.getItem("lang") || "en");
    const [calendar] = useState<'hijri' | 'gregorian'>(localStorage.getItem("calendar") as 'hijri' | 'gregorian' || 'gregorian');
    const [isHovered, setIsHovered] = useState(false);
    const { ref: eventRef, isVisible: isEventVisible } = useRevealAnimation();

    // Determine if the event should appear on the left or right
    const isEven = index % 2 === 0;

    return (
        <div ref={eventRef} className="relative mx-auto flex w-full min-h-[700px] flex-col gap-1 bg-[#141115]">
            {/* Timeline Line */}
            <div className={`absolute inset-0 flex justify-center transition-all duration-1000 ${isEventVisible ? 'opacity-100' : 'opacity-0'}`}>
                <div className="w-[2px] h-full bg-gradient-to-b from-green-600/30 via-green-600/50 to-green-600/30"></div>
            </div>

            {/* Main Content Container */}
            <div className={`relative flex items-center justify-center min-h-[500px] py-24 ${isEventVisible ? 'opacity-100' : 'opacity-0'}`}>
                {/* Event Circle */}
                <div className="absolute left-1/2 transform -translate-x-1/2 z-50">
                    <div
                        className={`relative w-8 h-8 bg-gradient-to-br from-green-400 to-green-600 rounded-full transform cursor-pointer hover:scale-150 transition-all duration-300 flex items-center justify-center ${isEventVisible ? 'scale-100' : 'scale-0'}`}
                        onMouseEnter={() => setIsHovered(true)}
                        onMouseLeave={() => setIsHovered(false)}
                    >
                        <div className="absolute w-12 h-12 rounded-full bg-green-500/20 animate-pulse"></div>
                        <div className="absolute w-6 h-6 rounded-full bg-green-400/80"></div>
                        <div className="absolute w-3 h-3 rounded-full bg-white/90"></div>
                    </div>
                </div>

                {/* Date Display */}
                <div className={`absolute w-[45%] ${isEven ? 'right-[5%]' : 'left-[5%]'} flex ${isEven ? 'justify-start' : 'justify-end'} items-center transition-all duration-700 delay-300 ${isEventVisible ? 'translate-x-0 opacity-100' : (isEven ? 'translate-x-10 opacity-0' : '-translate-x-10 opacity-0')}`}>
                    <div className="text-2xl md:text-3xl font-bold text-green-400 bg-[#1A1517]/80 px-8 py-4 rounded-2xl border-2 border-green-500/20 backdrop-blur-sm shadow-[0_0_15px_rgba(34,197,94,0.1)] hover:shadow-[0_0_25px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300">
                        {formatDate(date, Lang, calendar)}
                    </div>
                </div>

                {/* Content Container */}
                <div className={`absolute ${isEven ? 'left-[5%]' : 'right-[5%]'} w-[45%] flex flex-col ${isEven ? 'items-start' : 'items-end'} transition-all duration-700 delay-500 ${isEventVisible ? 'translate-x-0 opacity-100' : (isEven ? '-translate-x-10 opacity-0' : 'translate-x-10 opacity-0')}`}>
                    <div className={`w-full max-w-2xl bg-[#1A1517]/80 backdrop-blur-sm p-8 rounded-2xl border-2 border-green-500/20 shadow-[0_0_25px_rgba(34,197,94,0.1)] hover:shadow-[0_0_35px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300 ${isHovered ? 'scale-105' : 'scale-100'}`}>
                        <h3 className="text-2xl md:text-3xl font-bold text-white mb-6">{event.event_name}</h3>
                        {event.sections && event.sections[0] && (
                            <div>
                                <h4 className="text-green-400/90 mb-4 font-semibold text-lg md:text-xl">{event.sections[0].subtitle}</h4>
                                <p className="leading-8 text-gray-300/80">{event.sections[0].paragraphs[0]?.text}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default HistoryLineMiddle;