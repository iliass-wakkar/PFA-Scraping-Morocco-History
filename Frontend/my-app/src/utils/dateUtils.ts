export function formatDate(year: string | number, lang: string, calendar: 'hijri' | 'gregorian'): string {
    if (calendar === 'hijri') {
        if (lang === 'ar') return `${year} هـ`;
        if (lang === 'fr') return `${year} H`;
        return `${year} AH`;
    } else {
        if (lang === 'ar') return `${year} م`;
        if (lang === 'fr') return `${year} EC`;
        return `${year} CE`;
    }
} 