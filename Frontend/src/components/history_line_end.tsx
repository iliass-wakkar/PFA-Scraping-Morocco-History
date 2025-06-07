import { useState } from "react";
import { BiCircle } from "react-icons/bi";
import { FaCheck } from "react-icons/fa";
import { useRevealAnimation } from "../hooks/useRevealAnimation";
import { formatDate } from "../utils/dateUtils";

interface HistoryLineEndProps {
    title?: string;
    endYear?: string;
    totalEvents?: number;
    totalPeriods?: number;
}

const HistoryLineEnd = ({
    title = "",
    endYear = "",
    totalEvents = 0,
    totalPeriods = 0
}: HistoryLineEndProps) => {
    const [Lang] = useState(localStorage.getItem("lang") || "en");
    const [calendar] = useState<'hijri' | 'gregorian'>(localStorage.getItem("calendar") as 'hijri' | 'gregorian' || 'gregorian');
    const isLatin = ["en", "fr"].includes(Lang);
    const { ref: containerRef, isVisible: isContainerVisible } = useRevealAnimation();
    const { ref: _timelineRef, isVisible: _isTimelineVisible } = useRevealAnimation({ threshold: 0.8 });

    const headings = {
        en: "End of the journey",
        fr: "Fin du voyage",
        ar: "نهاية الرحلة"
    };

    const thanksMessages = {
        en: "Thank you for exploring Morocco's military history",
        fr: "Merci d'avoir exploré l'histoire militaire du Maroc",
        ar: "شكراً لاستكشاف التاريخ العسكري للمغرب"
    };

    const statsLabels = {
        en: { periods: "Historical Periods", events: "Significant Events" },
        fr: { periods: "Périodes Historiques", events: "Événements Significatifs" },
        ar: { periods: "الفترات التاريخية", events: "الأحداث المهمة" }
    };

    return (
        <div ref={containerRef} className="relative flex w-full min-h-screen flex-col bg-gradient-to-b from-[#141115] to-[#0A0908] overflow-hidden">
            {/* Decorative background patterns */}
            <div className="absolute inset-0 opacity-5">
                <div className="absolute w-[800px] h-[800px] rounded-full border-2 border-green-500 -top-52 -right-52 animate-[spin_40s_linear_infinite]"></div>
                <div className="absolute w-[1000px] h-[1000px] rounded-full border-2 border-green-500 -bottom-96 -left-96 animate-[spin_50s_linear_infinite_reverse]"></div>
            </div>

            {/* Timeline line ending */}
            <div className={`absolute inset-0 flex justify-center transition-all duration-1000 ${isContainerVisible ? 'opacity-100' : 'opacity-0'}`}>
                <div className="relative w-[2px]">
                    <div className={`absolute top-0 w-full bg-gradient-to-b from-green-500/30 via-green-500/50 to-green-400/60 transition-all duration-1000 ${isContainerVisible ? 'h-[70vh]' : 'h-0'}`}></div>
                    <div className={`absolute top-[70vh] w-4 h-4 rounded-full bg-gradient-to-br from-green-400 to-green-500 transform -translate-x-[7px] transition-all duration-700 delay-700 ${isContainerVisible ? 'opacity-100' : 'opacity-0'}`}></div>
                </div>
            </div>

            {/* Main content */}
            <div className={`flex flex-col gap-16 justify-center items-center w-full min-h-[85vh] text-white relative z-10 px-4 transition-all duration-1000 ${isContainerVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-20'}`}>
                {/* Timeline end node with animation */}
                <div className="relative">
                    <BiCircle className="text-green-400 text-9xl relative z-10" />
                    <div className="absolute inset-0 w-full h-full rounded-full bg-gradient-to-br from-green-500/20 to-green-400/10 animate-pulse"></div>
                    <div className="absolute inset-4 w-32 h-32 rounded-full border-2 border-green-400/30 animate-[spin_15s_linear_infinite]"></div>
                    <div className="absolute inset-8 w-24 h-24 rounded-full border-2 border-green-500/20 animate-[spin_20s_linear_infinite_reverse]"></div>
                    <div className="absolute inset-12 w-16 h-16 rounded-full border-2 border-green-400/10 animate-[spin_25s_linear_infinite]"></div>
                </div>

                {/* End Year */}
                {endYear && (
                    <div className={`text-3xl md:text-5xl font-bold text-green-400/90 bg-[#1A1517]/90 backdrop-blur-sm px-10 py-6 rounded-2xl border-2 border-green-500/20 shadow-[0_0_25px_rgba(34,197,94,0.1)] hover:shadow-[0_0_35px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300 ${isContainerVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                        {formatDate(endYear, Lang, calendar)}
                    </div>
                )}

                {/* Heading with animated underline */}
                <div className="relative text-center">
                    <h3 className={`text-5xl md:text-7xl font-bold tracking-wider mb-6 ${isLatin ? "main-font" : "arabic"} transition-all duration-1000 delay-500 ${isContainerVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                        {headings[Lang as keyof typeof headings]}
                    </h3>
                    <div className={`h-1 w-48 bg-gradient-to-r from-transparent via-green-400 to-transparent mx-auto rounded-full transform origin-center transition-all duration-1000 delay-700 ${isContainerVisible ? 'scale-x-100' : 'scale-x-0'}`}></div>
                </div>

                {/* Thank you message */}
                <p className={`text-2xl md:text-3xl text-gray-300/90 text-center max-w-3xl transition-all duration-1000 delay-900 ${isContainerVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                    {thanksMessages[Lang as keyof typeof thanksMessages]}
                </p>

                {/* Journey statistics */}
                <div className={`flex flex-wrap justify-center gap-8 mt-8 transition-all duration-1000 delay-1000 ${isContainerVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                    <div className="flex flex-col items-center gap-3 bg-[#1A1517]/90 backdrop-blur-sm p-8 rounded-2xl border-2 border-green-500/20 shadow-[0_0_25px_rgba(34,197,94,0.1)] hover:shadow-[0_0_35px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300">
                        <span className="text-5xl font-bold text-green-400">{totalPeriods}</span>
                        <span className="text-xl text-gray-300/90">{statsLabels[Lang as keyof typeof statsLabels].periods}</span>
                    </div>
                    <div className="flex flex-col items-center gap-3 bg-[#1A1517]/90 backdrop-blur-sm p-8 rounded-2xl border-2 border-green-500/20 shadow-[0_0_25px_rgba(34,197,94,0.1)] hover:shadow-[0_0_35px_rgba(34,197,94,0.2)] hover:border-green-500/30 transition-all duration-300">
                        <span className="text-5xl font-bold text-green-400">{totalEvents}</span>
                        <span className="text-xl text-gray-300/90">{statsLabels[Lang as keyof typeof statsLabels].events}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HistoryLineEnd;