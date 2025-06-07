interface ParsedDate {
    startYear: number;
    endYear?: number;
    era: 'AD' | 'AH' | 'BC';  // Added AH (After Hijra)
}

// Helper function to convert Gregorian year to Hijri year
const gregorianToHijri = (gregorianYear: number): number => {
    // Approximate conversion formula
    // H = (G-622) * 33/32
    return Math.floor((gregorianYear - 622) * (33/32));
};

// Helper function to convert Hijri year to Gregorian year
const hijriToGregorian = (hijriYear: number): number => {
    // Approximate conversion formula
    // G = H * 32/33 + 622
    return Math.floor(hijriYear * (32/33) + 622);
};

// Helper function to extract year from title format
const extractYearFromTitle = (title: string): { year: number, isRange: boolean, endYear?: number } | null => {
    // Match patterns like "(788 م)" or "(1590-1599 م)"
    const match = title.match(/\((\d+)(?:-(\d+))?\s*م\)/);
    if (match) {
        const startYear = parseInt(match[1]);
        const endYear = match[2] ? parseInt(match[2]) : undefined;
        return {
            year: startYear,
            isRange: !!match[2],
            endYear
        };
    }
    return null;
};

export const parseDate = (dateStr: string | null | undefined): ParsedDate | null => {
    if (!dateStr) return null;

    try {
        // Remove any whitespace and normalize
        const normalizedDate = dateStr.trim();
        
        // First try to parse the direct date format (e.g., "429-534 م")
        const directMatch = normalizedDate.match(/^(\d+)(?:-(\d+))?\s*(م|هـ|BC|AD|AH)?$/);
        if (directMatch) {
            const startYear = parseInt(directMatch[1]);
            const endYear = directMatch[2] ? parseInt(directMatch[2]) : undefined;
            const eraMarker = directMatch[3] || 'م';
            
            const era = eraMarker === 'هـ' || eraMarker === 'AH' ? 'AH' :
                       eraMarker === 'BC' || eraMarker === 'ق.م' ? 'BC' : 'AD';
            
            return {
                startYear,
                endYear,
                era
            };
        }
        
        // Try to extract year from title format
        const titleMatch = extractYearFromTitle(normalizedDate);
        if (titleMatch) {
            return {
                startYear: titleMatch.year,
                endYear: titleMatch.endYear,
                era: 'AD' // Title format uses Gregorian dates with 'م'
            };
        }

        // If no match found, try to parse just the number
        const numberMatch = normalizedDate.match(/\d+/);
        if (numberMatch) {
            return {
                startYear: parseInt(numberMatch[0]),
                era: 'AD' // Default to AD if no era marker
            };
        }

        return null;
    } catch (error) {
        console.error('Error parsing date:', error);
        return null;
    }
};

export const formatDate = (dateStr: string | null | undefined, language: string, targetCalendar: 'hijri' | 'gregorian' = 'gregorian'): string => {
    if (!dateStr) return '';
    
    try {
        const parsedDate = parseDate(dateStr);
        if (!parsedDate) return dateStr; // Return original string if parsing fails
        
        const { startYear, endYear, era } = parsedDate;
        
        // Convert years based on target calendar
        let displayStartYear = startYear;
        let displayEndYear = endYear;
        let displayEra = era;

        if (era === 'AD' && targetCalendar === 'hijri') {
            displayStartYear = gregorianToHijri(startYear);
            if (endYear) displayEndYear = gregorianToHijri(endYear);
            displayEra = 'AH';
        } else if (era === 'AH' && targetCalendar === 'gregorian') {
            displayStartYear = hijriToGregorian(startYear);
            if (endYear) displayEndYear = hijriToGregorian(endYear);
            displayEra = 'AD';
        }

        // Format based on language and calendar
        if (language === 'ar') {
            const yearStr = Math.abs(displayStartYear).toString();
            const suffix = displayEra === 'BC' ? 'ق.م' : (displayEra === 'AH' ? 'هـ' : 'م');
            
            if (displayEndYear) {
                return `${yearStr}-${displayEndYear} ${suffix}`;
            }
            return `${yearStr} ${suffix}`;
        } else {
            const yearStr = Math.abs(displayStartYear).toString();
            
            if (displayEndYear) {
                return `${yearStr}-${displayEndYear} ${displayEra}`;
            }
            return `${yearStr} ${displayEra}`;
        }
    } catch (error) {
        console.error('Error formatting date:', error);
        return dateStr; // Return original string if formatting fails
    }
};

export const extractYear = (dateStr: string | null | undefined): number => {
    if (!dateStr) return 0;
    
    try {
        const parsedDate = parseDate(dateStr);
        if (!parsedDate) return 0;
        
        const { startYear, era } = parsedDate;
        
        // Convert Hijri dates to Gregorian for consistent timeline
        if (era === 'AH') {
            return hijriToGregorian(startYear);
        }
        
        return era === 'BC' ? -startYear : startYear;
    } catch (error) {
        console.error('Error extracting year:', error);
        return 0;
    }
}; 