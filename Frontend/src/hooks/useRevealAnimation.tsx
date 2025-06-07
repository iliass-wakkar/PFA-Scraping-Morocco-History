import { useEffect, useRef, useState } from 'react';

interface UseRevealAnimationOptions {
    threshold?: number;
    rootMargin?: string;
    once?: boolean;
}

export const useRevealAnimation = (options: UseRevealAnimationOptions = {}) => {
    const { threshold = 0.1, rootMargin = '0px', once = true } = options;
    const ref = useRef<HTMLDivElement>(null);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const element = ref.current;
        if (!element) return;

        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setIsVisible(true);
                    if (once && observer) {
                        observer.disconnect();
                    }
                } else if (!once) {
                    setIsVisible(false);
                }
            },
            { threshold, rootMargin }
        );

        observer.observe(element);

        return () => {
            observer.disconnect();
        };
    }, [threshold, rootMargin, once]);

    return { ref, isVisible };
};