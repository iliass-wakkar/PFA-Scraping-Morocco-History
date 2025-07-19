import { useEffect, useRef, useState } from "react";

export function useRevealAnimation<T extends HTMLElement = HTMLElement>() {
    const ref = useRef<T | null>(null);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (!ref.current) return;
        const observer = new window.IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) setIsVisible(true);
            },
            { threshold: 0.15 }
        );
        observer.observe(ref.current);
        return () => {
            if (ref.current) observer.unobserve(ref.current);
        };
    }, [ref]);

    return { ref, isVisible };
} 