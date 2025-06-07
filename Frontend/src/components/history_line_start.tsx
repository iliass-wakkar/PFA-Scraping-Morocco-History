import { useState } from "react";
import { BiCircle } from "react-icons/bi";
import { BsDot } from "react-icons/bs";
import { useRevealAnimation } from "../hooks/useRevealAnimation";
import { formatDate, extractYear } from "../utils/dateUtils";

interface HistoryLineStartProps {
    title?: string;
    startYear?: string;
    endYear?: string;
}

const HistoryLineStart = ({ title = "", startYear = "", endYear = "" }: HistoryLineStartProps) => {
    const [Lang] = useState(localStorage.getItem("lang") || "en");
    const [calendar, setCalendar] = useState<'hijri' | 'gregorian'>(localStorage.getItem("calendar") as 'hijri' | 'gregorian' || 'gregorian');
    const isLatin = ["en", "fr"].includes(Lang);

    const { ref: containerRef, isVisible: isContainerVisible } = useRevealAnimation();
    const { ref: timelineRef, isVisible: isTimelineVisible } = useRevealAnimation({ threshold: 0.8 });

    const headings = {
        en: "Start of the journey",
        fr: "Début du voyage",
        ar: "بداية الرحلة"
    };

    // Calculate duration in years
    const duration = Math.abs(extractYear(endYear) - extractYear(startYear));

    // Toggle calendar system
    const toggleCalendar = () => {
        const newCalendar = calendar === 'gregorian' ? 'hijri' : 'gregorian';
        setCalendar(newCalendar);
        localStorage.setItem("calendar", newCalendar);
    };

    return (
        <div ref={containerRef} className="relative flex w-full min-h-screen flex-col bg-gradient-to-b from-[#0A0908] to-[#141115] overflow-hidden">
            {/* Decorative background patterns */}
            <div className="absolute inset-0 opacity-5">
                <div className="absolute w-[800px] h-[800px] rounded-full border-2 border-green-500 -top-52 -right-52 animate-[spin_40s_linear_infinite]"></div>
                <div className="absolute w-[1000px] h-[1000px] rounded-full border-2 border-green-500 -bottom-96 -left-96 animate-[spin_50s_linear_infinite_reverse]"></div>
            </div>

            {/* Main content */}
            <div className={`flex flex-col gap-16 justify-center items-center w-full min-h-[85vh] text-white relative z-10 px-4 transition-all duration-1000 ${isContainerVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-20'}`}>
                {/* Calendar Toggle Button */}
                <button
                    onClick={toggleCalendar}
                    className="absolute top-8 right-8 px-4 py-2 bg-[#1A1517]/80 hover:bg-[#1A1517] rounded-lg text-green-400 border-2 border-green-500/20 backdrop-blur-sm shadow-[0_0_15px_rgba(34,197,94,0.1)] hover:shadow-[0_0_25px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300"
                >
                    {calendar === 'gregorian' ? 
                        (Lang === 'ar' ? 'التقويم الهجري' : 'Hijri Calendar') : 
                        (Lang === 'ar' ? 'التقويم الميلادي' : 'Gregorian Calendar')}
                </button>

                {/* Timeline node with animation */}
                <div className={`w-48 h-48 flex justify-center items-center transition-all duration-1000 delay-300 ${isContainerVisible ? 'scale-100' : 'scale-0'}`}>
                    <div className="relative">
                        <BiCircle className="text-green-400 text-9xl relative z-10" />
                        <div className="absolute inset-0 w-full h-full rounded-full bg-gradient-to-br from-green-500/20 to-green-400/10 animate-pulse"></div>
                        <div className="absolute inset-4 w-32 h-32 rounded-full border-2 border-green-400/30 animate-[spin_15s_linear_infinite]"></div>
                        <div className="absolute inset-8 w-24 h-24 rounded-full border-2 border-green-500/20 animate-[spin_20s_linear_infinite_reverse]"></div>
                        <div className="absolute inset-12 w-16 h-16 rounded-full border-2 border-green-400/10 animate-[spin_25s_linear_infinite]"></div>
                    </div>
                </div>

                {/* Heading with animated underline */}
                <div className="relative text-center">
                    <h3 className={`text-5xl md:text-7xl font-bold tracking-wider mb-6 ${isLatin ? "main-font" : "arabic"} transition-all duration-1000 delay-500 ${isContainerVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                        {headings[Lang as keyof typeof headings]}
                    </h3>
                    <div className={`h-1 w-48 bg-gradient-to-r from-transparent via-green-400 to-transparent mx-auto rounded-full transform origin-center transition-all duration-1000 delay-700 ${isContainerVisible ? 'scale-x-100' : 'scale-x-0'}`}></div>
                </div>

                {/* Period title */}
                {title && (
                    <p className={`arabic-secondary text-green-400 text-3xl md:text-5xl text-center max-w-5xl transition-all duration-1000 delay-700 ${isContainerVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                        {title}
                    </p>
                )}

                {/* Year range with enhanced design */}
                <div className={`flex flex-col items-center gap-8 mt-8 transition-all duration-1000 delay-900 ${isContainerVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                    <div className="flex items-center gap-6 text-3xl md:text-5xl font-bold">
                        <div className="px-10 py-6 rounded-2xl bg-[#1A1517]/90 backdrop-blur-sm border-2 border-green-500/20 shadow-[0_0_25px_rgba(34,197,94,0.1)] hover:shadow-[0_0_35px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300">
                            {formatDate(startYear, Lang, calendar)}
                        </div>
                        <BsDot className="text-green-400 text-6xl animate-pulse" />
                        <div className="px-10 py-6 rounded-2xl bg-[#1A1517]/90 backdrop-blur-sm border-2 border-green-500/20 shadow-[0_0_25px_rgba(34,197,94,0.1)] hover:shadow-[0_0_35px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300">
                            {formatDate(endYear, Lang, calendar)}
                        </div>
                    </div>
                </div>
            </div>

            {/* Animated timeline line */}
            <div ref={timelineRef} className="relative flex justify-center h-[15vh]">
                <div className="relative w-[2px]">
                    <div className={`absolute top-0 bottom-0 w-full bg-gradient-to-b from-green-500/50 via-green-500/30 to-green-500/50 transition-all duration-1000 ${isTimelineVisible ? 'h-full' : 'h-0'}`}></div>
                    <div className={`absolute top-0 w-4 h-4 rounded-full bg-gradient-to-br from-green-400 to-green-500 transform -translate-x-[7px] transition-all duration-1000 delay-700 ${isTimelineVisible ? 'opacity-100' : 'opacity-0'}`}></div>
                </div>
            </div>

            {/* Scroll indicator */}
            <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 animate-bounce opacity-50">
                <div className="w-8 h-12 rounded-full border-2 border-green-400 flex justify-center pt-2">
                    <div className="w-1 h-4 bg-green-400 rounded-full animate-scroll"></div>
                </div>
            </div>
        </div>
    );
};

export default HistoryLineStart;