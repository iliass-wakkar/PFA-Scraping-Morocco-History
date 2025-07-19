"use client";
import LandingHero from "../components/LandingHero";
import About from "../components/About";
import { useLanguage } from "../contexts/LanguageContext";
import { useEffect, useState } from "react";

export default function Home() {
  const { language } = useLanguage();
  const [dir, setDir] = useState('ltr');
  useEffect(() => {
    setDir(language === 'ar' ? 'rtl' : 'ltr');
  }, [language]);
  return (
    <div dir={dir}>
      <LandingHero />
      <About />
      {/* <Timeline /> */}
    </div>
  );
}
