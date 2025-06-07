import HeroBackground from "../assets/hero_background.jpg";
import { GiFlexibleStar } from "react-icons/gi";
import { useEffect, useState } from "react";
import { FaArrowDown } from "react-icons/fa";
import HistoryLineStart from "../components/history_line_start";
import { api } from "../hooks/api";
import HistoryLineMiddle from "../components/history_line_middle";
import HistoryLineEnd from "../components/history_line_end";
import AboutPage from "../components/about";
import Timeline from "../components/timeline";

interface Source {
    authors: string;
    journal: string;
    year: number;
    url: string;
}

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

interface PeriodsData {
    big_event_name: string;
    events: PeriodEvent[];
}

const Homepage = () => {
    const [lang, setLang] = useState(localStorage.getItem("lang") || "en");
    const [Periods, setPeriods] = useState<PeriodsData[] | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await api.get<{ data: PeriodsData[], status: string }>(`/api/historical-events/?language=${lang}`);
                console.log('API Response:', response.data);
                if (response.data && response.data.data) {
                    // Transform the date format
                    const transformedData = response.data.data.map(period => ({
                        ...period,
                        events: period.events.map(event => ({
                            ...event,
                            // Ensure date is properly converted to string
                            date: event.date ? JSON.stringify(event.date) : ""
                        }))
                    }));
                    setPeriods(transformedData);
                } else {
                    console.error("Invalid API response format:", response);
                    setPeriods([]);
                }
            } catch (error) {
                console.error("Error fetching data:", error);
                setPeriods([]);
            }
        };

        fetchData();

        return () => {
            console.log("Component unmounted");
        };
    }, [lang]);

    // Calculate total events across all periods
    const totalEvents = Periods?.reduce((sum, period) => sum + period.events.length, 0) || 0;

    return (
        <>
            {/* Hero Section */}
            <div className="relative w-full h-screen" id="homepage">
                {/* Background Image */}
                <div className="absolute inset-0 w-full h-full">
                    <img
                        src={HeroBackground}
                        alt="Historical Moroccan Military"
                        className="h-screen w-full object-cover brightness-75 bg-gray-400"
                    />
                    {/* Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-[#141115] via-transparent to-transparent opacity-80 h-screen"></div>
                </div>
                {/* Hero Content */}
                <div className="relative z-10 flex flex-col items-center justify-center h-screen text-center px-4 backdrop-blur-xs backdrop-brightness-50">
                    <GiFlexibleStar className="text-green-600 w-16 h-16 mb-6  hover:drop-shadow-2xl hover:drop-shadow-green-600 hero-logo transition-all" />
                    <h1 className="text-4xl md:text-6xl font-bold text-white mb-2 font-serif arabic hero-title1">
                        تاريخ الحروب المغربية
                    </h1>
                    <h2 className={`text-3xl md:text-5xl font-bold text-white main-font hero-title2 ${lang === "ar" ? "hidden" : ""} `}>
                        {lang === "en" ? "History of Moroccan Wars" : "L'Historique des guerres marocaines"}
                    </h2>
                    <p className="text-white text-lg md:text-xl max-w-2xl mt-6 mb-8 hero-desc">
                        {lang === "en" ? "Discover the rich military history of Morocco through the ages, from ancient battles to modern conflicts." : (lang === "fr" ? "Découvrez la riche histoire militaire du Maroc à travers les âges, des batailles antiques aux conflits modernes." : "اكتشف التاريخ العسكري الغني للمغرب عبر العصور، من المعارك القديمة إلى الصراعات الحديثة")}
                    </p>
                    <div className="flex flex-col justify-center items-center gap-4 absolute bottom-20 left-0 w-full hero-scroll">
                        <h1 className="font-bold text-md text-white">{lang === "en" ? "Scroll down" : lang === "ar" ? "انتقل للأسفل" : "faire défiler vers le bas"}</h1>
                        <FaArrowDown className="font-extrabold text-3xl text-green-600 animate-bounce" />
                    </div>
                </div>
            </div>

            {/* About Us Section */}
            <div>
                <AboutPage />
            </div>

            {/* History Line Section */}
            <div id="history">
                {Periods && Periods.map((period, periodIndex) => (
                    <div key={period.big_event_name}>
                        {/* If this is not the first period, add a transition element between periods */}
                        {periodIndex > 0 && (
                            <div className="h-32 bg-gradient-to-b from-[#141115] via-[#1A1517] to-[#0A0908] flex justify-center">
                                <div className="w-1 h-full bg-green-600/30"></div>
                            </div>
                        )}

                        <HistoryLineStart
                            title={period.big_event_name}
                            startYear={period.events[0]?.date?.toString() || ""}
                            endYear={period.events[period.events.length - 1]?.date?.toString() || ""}
                        />

                        {/* Alternative if Timeline expects events directly */}
                        {period.events.map((event, eventIndex) => (
                            <HistoryLineMiddle
                                key={event.event_name}
                                event={{
                                    ...event,
                                    date: event.date || ""
                                }}
                                index={periodIndex * 100 + eventIndex}
                                date={event.date || ""}
                            />
                        ))}
                    </div>
                ))}

                {/* Final timeline end - only show once after all periods */}
                {Periods && Periods.length > 0 && (
                    <HistoryLineEnd
                        endYear={Periods[Periods.length - 1].events[Periods[Periods.length - 1].events.length - 1]?.date || ""}
                        totalEvents={totalEvents}
                        totalPeriods={Periods.length}
                    />
                )}
            </div>
        </>
    );
};

export default Homepage;