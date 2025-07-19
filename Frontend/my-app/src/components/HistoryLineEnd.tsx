import { motion } from "framer-motion";
import { formatDate } from "../utils/dateUtils";
import React, { useState } from "react";
import { FaHistory, FaCalendarAlt, FaBookOpen } from "react-icons/fa";

interface HistoryLineEndProps {
    endYear: string;
    totalEvents: number;
    totalPeriods: number;
}

const HistoryLineEnd = ({ endYear, totalEvents, totalPeriods }: HistoryLineEndProps) => {
    const [Lang] = useState(typeof window !== 'undefined' ? localStorage.getItem("lang") || "en" : "en");
    const [calendar] = useState<'hijri' | 'gregorian'>(typeof window !== 'undefined' ? (localStorage.getItem("calendar") as 'hijri' | 'gregorian') || 'gregorian' : 'gregorian');

    const stats = [
        {
            icon: <FaHistory className="w-8 h-8 text-green-500" />,
            value: totalPeriods,
            label: Lang === "en" ? "Historical Periods" : Lang === "ar" ? "الفترات التاريخية" : "Périodes historiques"
        },
        {
            icon: <FaCalendarAlt className="w-8 h-8 text-red-500" />,
            value: formatDate(endYear, Lang, calendar),
            label: Lang === "en" ? "End Year" : Lang === "ar" ? "سنة النهاية" : "Année de fin"
        },
        {
            icon: <FaBookOpen className="w-8 h-8 text-green-500" />,
            value: totalEvents,
            label: Lang === "en" ? "Total Events" : Lang === "ar" ? "مجموع الأحداث" : "Total des événements"
        }
    ];

    return (
        <motion.div 
            className="relative w-full min-h-[500px] bg-[#141115] flex flex-col items-center justify-center pb-20"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 1 }}
        >
            {/* Timeline Line End */}
            <motion.div 
                className="absolute inset-0 flex justify-center"
                initial={{ scaleY: 0 }}
                whileInView={{ scaleY: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1, delay: 0.5 }}
                style={{ transformOrigin: 'top' }}
            >
            </motion.div>
            {/* End Circle */}
            <motion.div 
                className="relative z-10 mb-16"
                initial={{ scale: 0 }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.5 }}
            >
                <div className="w-16 h-16 rounded-full bg-green-600 flex items-center justify-center shadow-lg shadow-green-600/20 border-4 border-red-500">
                    <div className="w-8 h-8 rounded-full bg-white"></div>
                </div>
            </motion.div>
            {/* Content */}
            <motion.div 
                className="relative z-10 text-center max-w-5xl mx-auto px-4"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, delay: 0.8 }}
            >
                <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
                    {Lang === "en" ? "Journey's End" : Lang === "ar" ? "نهاية الرحلة" : "Fin du voyage"}
                </h2>
                <p className="text-gray-400 text-lg mb-12 max-w-2xl mx-auto">
                    {Lang === "en" 
                        ? "Explore the rich tapestry of Moroccan history through these significant events and periods."
                        : Lang === "ar"
                        ? "اكتشف النسيج الغني للتاريخ المغربي من خلال هذه الأحداث والفترات المهمة."
                        : "Explorez la riche tapisserie de l'histoire marocaine à travers ces événements et périodes importantes."}
                </p>
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {stats.map((stat, index) => (
                        <motion.div
                            key={index}
                            className="glass p-6 rounded-xl text-center border border-green-500/30 hover:border-red-500/40"
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: 1 + index * 0.2 }}
                            whileHover={{ scale: 1.05 }}
                        >
                            <div className="mb-4 flex justify-center">
                                {stat.icon}
                            </div>
                            <div className="text-2xl font-bold text-white mb-2">
                                {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
                            </div>
                            <div className="text-gray-400">
                                {stat.label}
                            </div>
                        </motion.div>
                    ))}
                </div>
            </motion.div>
        </motion.div>
    );
};

export default HistoryLineEnd; 