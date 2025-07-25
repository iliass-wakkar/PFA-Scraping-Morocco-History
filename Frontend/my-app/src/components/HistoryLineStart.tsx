import { motion } from "framer-motion";
import { formatDate } from "../utils/dateUtils";
import React, { useState } from "react";

interface HistoryLineStartProps {
    title: string;
    startYear: string;
    endYear: string;
}

const HistoryLineStart = ({ title, startYear, endYear }: HistoryLineStartProps) => {
    const [Lang] = useState(typeof window !== 'undefined' ? localStorage.getItem("lang") || "en" : "en");
    const [calendar] = useState<'hijri' | 'gregorian'>(typeof window !== 'undefined' ? (localStorage.getItem("calendar") as 'hijri' | 'gregorian') || 'gregorian' : 'gregorian');

    return (
        <motion.div 
            className="relative w-full min-h-[400px] bg-[#141115] flex flex-col items-center justify-center py-20 mb-44"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
        >
            {/* Decorative Start Circle */}
            <motion.div
                className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10"
                initial={{ scale: 0, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1, delay: 0.2 }}
            >
                <div className="relative w-32 h-32 flex items-center justify-center">
                    <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-green-600 rounded-full animate-spin-slow" />
                    <span className="h-16 w-16 relative z-10 text-white text-2xl font-bold flex items-center justify-center">
                        <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 512 512" className="h-16 w-16">
                            <path d="M144.938 18.063l8.437 19.187c17.36 39.43 27.86 79.965 32.563 120.313-50.01 4.028-99.724 4.15-144.688 1.656l-21.188-1.19L33.5 174.438c42.232 51.6 93.612 82.498 148.438 110.907-12.137 69.664-39.726 134.1-77.282 185.312L92 487.906l21.25-2.437c99.754-11.457 177.9-51.146 236.688-106.064 33.06 23.513 65.993 52.01 98.093 88.97l15.095 17.374 1.28-22.97c3.558-63.803-8.63-128.11-33.655-187.53 37.76-67.647 57.985-143.224 63.563-214.656l2-25.532-17.97 18.22c-35.647 36.18-86.34 61.284-143.468 78.124-46.935-47.74-104.638-85.32-170.03-106.812l-19.907-6.532zm82.75 65.312c10.37.018 23.587 4.884 39.312 14.47 16.552 11.965 32.193 25.124 46.813 39.31-35.065 8.896-72.027 14.882-109.188 18.626-1.033-8.865-2.353-17.75-3.938-26.624-.003-.02.004-.042 0-.062-.856-30.68 8.666-45.75 27-45.72zm183.062 46.688c30.66-.583 46.988 17.807 38.875 56.343-7.78 22.997-17.28 45.628-28.594 67.47-18.614-38.538-42.71-74.62-71.436-106.75 12.818-4.06 25.32-8.585 37.437-13.564 8.605-2.196 16.553-3.363 23.72-3.5zm-81.313 22.968c33.327 35.83 60.508 77.187 80.282 121.47-9.032 15.405-19.007 30.317-30 44.563-7.257 9.4-15.006 18.48-23.158 27.25-21.106-6.102-43.19-14.988-60.812-23-.074-.034-.144-.06-.22-.094-19.852-11.155-39.46-21.245-58.624-30.908-11.675-5.886-22.84-11.594-34.125-17.343 4.355-30.108 5.87-61.04 4.126-92.283 25.76-7.15 54.416-13.28 78.313-19.25 14.972-2.99 29.75-6.43 44.217-10.406zm-39.843 32.657c-.847-.002-1.68.018-2.5.063-6.556.363-12.224 2.22-16.813 5.125-9.177 5.81-15.155 16.127-15.155 32.063 0 31.87 28.156 70.8 61 82.812 16.422 6.007 29.822 4.435 39-1.375s15.156-16.127 15.156-32.063c0-31.87-28.124-70.767-60.967-82.78-7.185-2.63-13.79-3.828-19.72-3.845zm-101.22 2.532c1.17 26.25-.064 52.25-3.374 77.686-8.285-4.346-16.454-8.732-24.47-13.25-45.842-30.138-18.07-49.58 27.845-64.437zm11.095 106.03c9.662 4.89 19.185 9.8 29 14.75 34.664 17.48 70.195 36.024 105.686 59.625-6.714 6.15-13.702 12.07-20.937 17.78-66.568 32.47-115.528 2.77-118.25-70.78 1.656-7.067 3.155-14.187 4.5-21.375zm219.124 1.53c3.838 9.98 7.273 20.084 10.344 30.283 3.064 27.392-20.972 31.225-51.75 25.312 6.026-6.788 11.806-13.74 17.312-20.875 8.65-11.207 16.628-22.84 24.094-34.72z"></path>
                        </svg>
                    </span>
                </div>
            </motion.div>
            {/* Timeline Line */}
            <motion.div 
                className="absolute left-1/2 top-0 -translate-x-1/2 flex justify-center"
                style={{ height: "calc(100% + 11rem)" }}
                initial={{ scaleY: 0 }}
                whileInView={{ scaleY: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1, delay: 0.5 }}
            >
                <div className="w-[2px] h-full bg-gradient-to-b from-transparent via-green-600/50 to-red-600/30"></div>
            </motion.div>
            {/* Content */}
            <motion.div 
                className="relative z-10 text-center max-w-7xl mx-auto px-4 mt-16"
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, delay: 0.2 }}
            >
                <h2
                  className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-8"
                  dangerouslySetInnerHTML={{
                    __html: title.replace(/_/g, " "),
                  }}
                />
                <div className="flex flex-col md:flex-row items-center justify-center gap-6 md:gap-12 max-md:flex-row ">
                    <motion.div 
                        className="glass p-6 rounded-xl backdrop-blur-md border border-green-500/40 "
                        whileHover={{ scale: 1.05 }}
                        transition={{ duration: 0.3 }}
                    >
                        <p className="text-green-400 text-lg mb-2">{Lang === "en" ? "Start Year" : Lang === "ar" ? "سنة البداية" : "Année de début"}</p>
                        <h3 className="text-2xl md:text-3xl font-bold text-white">
                            {formatDate(startYear, Lang, calendar)}
                        </h3>
                    </motion.div>
                    <div className="hidden md:block w-24 h-[2px] bg-gradient-to-r from-green-500 via-red-500 to-green-500"></div>
                    <motion.div 
                        className="glass p-6 rounded-xl backdrop-blur-md border border-red-500/40"
                        whileHover={{ scale: 1.05 }}
                        transition={{ duration: 0.3 }}
                    >
                        <p className="text-red-400 text-lg mb-2">{Lang === "en" ? "End Year" : Lang === "ar" ? "سنة النهاية" : "Année de fin"}</p>
                        <h3 className="text-2xl md:text-3xl font-bold text-white">
                            {formatDate(endYear, Lang, calendar)}
                        </h3>
                    </motion.div>
                </div>
            </motion.div>
        </motion.div>
    );
};

export default HistoryLineStart; 