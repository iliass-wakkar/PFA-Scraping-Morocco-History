import { FaGithub, FaLinkedin, FaEnvelope } from 'react-icons/fa';
import { GiFlexibleStar } from 'react-icons/gi';
import { useEffect, useRef, useState } from 'react';

const AboutPage = () => {
    const developers = [
        {
            name: "Iliass Wakkar",
            role: {
                en: "Project Lead & Developer",
                ar: "رئيس المشروع & مطور",
                fr: "Chef de projet & Développeur"
            },
            bio: {
                en: "Passionate about creating digital solutions that preserve and celebrate Moroccan history. Specializing in React and modern web technologies.",
                ar: "شغوف بإنشاء حلول رقمية تحافظ على وتحتفل بتاريخ المغرب. متخصص في React وتقنيات الويب الحديثة.",
                fr: "Passionné par la création de solutions numériques qui préservent et célèbrent l'histoire du Maroc. Spécialisé dans React et les technologies web modernes."
            },
            image: "/iliass_pfp.jpg",
            github: "https://github.com/iliass-wakkar",
            linkedin: "https://linkedin.com/in/iliass",
            email: "iliass@example.com"
        },
        {
            name: "Rochdi Mohamed Amine",
            role: {
                en: "Developer & UI/UX Designer",
                ar: "مطور & مصمم واجهات المستخدم/تجربة المستخدم",
                fr: "Développeur & Designer UI/UX"
            },
            bio: {
                en: "Dedicated to creating beautiful, intuitive interfaces that bring historical narratives to life. Focused on user experience and responsive design.",
                ar: "مكرس لإنشاء واجهات جميلة وبديهية تحيي السرد التاريخي. يركز على تجربة المستخدم والتصميم المتجاوب.",
                fr: "Dédié à la création d'interfaces belles et intuitives qui donnent vie aux récits historiques. Axé sur l'expérience utilisateur et le design réactif."
            },
            image: "/rocmine_pfp.jpg",
            github: "https://github.com/rocmine",
            linkedin: "https://linkedin.com/in/rocmine",
            email: "rochdi@example.com"
        }
    ];


    // Custom hook for reveal animation
    const useReveal = (options = {}) => {
        const ref = useRef(null);
        const [isVisible, setIsVisible] = useState(false);

        useEffect(() => {
            const observer = new IntersectionObserver(([entry]) => {
                if (entry.isIntersecting) {
                    setIsVisible(true);
                    observer.unobserve(entry.target);
                }
            }, {
                threshold: 0.1,
                ...options
            });

            if (ref.current) {
                observer.observe(ref.current);
            }

            return () => {
                if (ref.current) {
                    observer.unobserve(ref.current);
                }
            };
        }, []);

        return [ref, isVisible];
    };

    // Animation variants
    const fadeInUp = {
        hidden: "opacity-0 translate-y-10",
        visible: "opacity-100 translate-y-0"
    };

    const fadeInLeft = {
        hidden: "opacity-0 -translate-x-10",
        visible: "opacity-100 translate-x-0"
    };

    const fadeInRight = {
        hidden: "opacity-0 translate-x-10",
        visible: "opacity-100 translate-x-0"
    };

    const scaleIn = {
        hidden: "opacity-0 scale-95",
        visible: "opacity-100 scale-100"
    };

    // Reveal hooks for different sections
    const [heroRef, heroVisible] = useReveal();
    const [missionRef, missionVisible] = useReveal();
    const [offerRef, offerVisible] = useReveal();
    const [developersRef, developersVisible] = useReveal();
    const [contactRef, contactVisible] = useReveal();

    const Lang = localStorage.getItem("lang");

    return (
        <div className="pt-20 min-h-screen bg-gradient-to-b from-black to-gray-900" id="about">
            {/* Hero Section */}
            <div className="relative overflow-hidden">
                <div className="absolute inset-0 bg-[url('/moroccan-pattern.svg')] opacity-5"></div>
                <div
                    ref={heroRef}
                    className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20"
                >
                    <div className="text-center">
                        <h1 className={`text-4xl md:text-5xl font-bold text-white mb-6 font-serif transition-all duration-1000 ${heroVisible ? fadeInUp.visible : fadeInUp.hidden}`}>
                            {
                                Lang === "en"
                                    ? "About TarikhAlHuroob"
                                    : Lang === "ar"
                                        ? "نبذة عن تاريخ الحروب"
                                        : "À propos de Tarikh AlHuroob"
                            }
                        </h1>
                        <p className={`text-xl text-gray-300 max-w-3xl mx-auto mb-8 transition-all duration-1000 delay-200 ${heroVisible ? fadeInUp.visible : fadeInUp.hidden}`}>
                            {
                                Lang === "en"
                                    ? "A digital chronicle dedicated to preserving and sharing the rich history of Moroccan wars. Our platform brings historical narratives to life through modern technology and thoughtful design."
                                    : Lang === "ar"
                                        ? "سجلّ رقمي مُخصّص لحفظ ومشاركة التاريخ الغني للحروب المغربية. منصتنا تُضفي حيويةً على السرديات التاريخية من خلال تقنيات حديثة وتصميم مُدروس."
                                        : "Une chronique numérique dédiée à la préservation et au partage de la riche histoire des guerres marocaines. Notre plateforme donne vie aux récits historiques grâce à une technologie moderne et un design soigné."
                            }
                        </p>
                        <div className={`flex justify-center space-x-6 transition-all duration-1000 delay-400 ${heroVisible ? fadeInUp.visible : fadeInUp.hidden}`}>
                            {[
                                {
                                    icon: <GiFlexibleStar className="h-8 w-8 mr-2" />,
                                    text: {
                                        en: "Historical Accuracy",
                                        ar: "الدقة التاريخية",
                                        fr: "Précision historique"
                                    }
                                },
                                {
                                    icon: <GiFlexibleStar className="h-8 w-8 mr-2" />,
                                    text: {
                                        en: "Modern Technology",
                                        ar: "التكنولوجيا الحديثة",
                                        fr: "Technologie moderne"
                                    }
                                },
                                {
                                    icon: <GiFlexibleStar className="h-8 w-8 mr-2" />,
                                    text: {
                                        en: "Cultural Heritage",
                                        ar: "التراث الثقافي",
                                        fr: "Patrimoine culturel"
                                    }
                                }

                            ].map((item, index) => (
                                <div
                                    key={index}
                                    className={`flex items-center text-emerald-400 transition-all duration-1000 transform ${heroVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}
                                    style={{ transitionDelay: `${600 + index * 200}ms` }}
                                >
                                    {item.icon}
                                    <span className="text-lg font-semibold">
                                        {
                                            Lang === "en"
                                                ? item.text.en
                                                : Lang === "ar"
                                                    ? item.text.ar
                                                    : item.text.fr
                                        }
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Mission Section */}
            <div className="bg-black/50 backdrop-blur-lg py-16">
                <div ref={missionRef} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid md:grid-cols-2 gap-12 items-center">
                        <div className={`transition-all duration-1000 ${missionVisible ? fadeInLeft.visible : fadeInLeft.hidden}`}>
                            <h2 className="text-3xl font-bold text-white mb-6">
                                {
                                    Lang === "en"
                                        ? "Our Mission"
                                        : Lang === "ar"
                                            ? "مهمتنا"
                                            : "Notre Mission"
                                }
                            </h2>
                            <p className="text-gray-300 mb-4">
                                {
                                    Lang === "en"
                                        ? "TarikhAlHuroob is more than just a historical archive. We aim to bridge the gap between Morocco's glorious past and the digital age, making history accessible and engaging for future generations."
                                        : Lang === "ar"
                                            ? "تاريخ الحروب هو أكثر من مجرد أرشيف تاريخي. نحن نسعى لسد الفجوة بين ماضي المغرب المجيد والعصر الرقمي، مما يجعل التاريخ متاحًا وجذابًا للأجيال القادمة."
                                            : "TarikhAlHuroob est bien plus qu'un simple archive historique. Nous visons à combler le fossé entre le passé glorieux du Maroc et l'ère numérique, rendant l'histoire accessible et engageante pour les générations futures."
                                }
                            </p>
                            <p className="text-gray-300 mb-4">
                                {
                                    Lang === "en"
                                        ? "Through careful research, interactive presentations, and immersive storytelling, we bring the epic tales of Moroccan military history to life, celebrating victories and learning from the past."
                                        : Lang === "ar"
                                            ? "من خلال البحث الدقيق، والعروض التفاعلية، وسرد القصص الغامرة، نعيد إحياء الحكايات الملحمية لتاريخ المغرب العسكري، نحتفل بالانتصارات ونتعلم من الماضي."
                                            : "À travers des recherches approfondies, des présentations interactives et un récit immersif, nous donnons vie aux récits épiques de l'histoire militaire du Maroc, célébrant les victoires et apprenant du passé."
                                }
                            </p>
                            <p className="text-gray-300">
                                {
                                    Lang === "en"
                                        ? "Our platform serves as a comprehensive resource for students, historians, and anyone interested in understanding the strategic brilliance and cultural significance of Morocco's military heritage."
                                        : Lang === "ar"
                                            ? "تعمل منصتنا كمورد شامل للطلاب والمؤرخين وأي شخص مهتم بفهم البراعة الاستراتيجية والأهمية الثقافية لتراث المغرب العسكري."
                                            : "Notre plateforme sert de ressource complète pour les étudiants, les historiens et toute personne intéressée à comprendre l'ingéniosité stratégique et la signification culturelle de l'héritage militaire du Maroc."
                                }
                            </p>
                        </div>

                        <div ref={offerRef} className={`relative hidden md:block transition-all duration-1000 ${offerVisible ? fadeInRight.visible : fadeInRight.hidden}`}>
                            <div className="absolute inset-0 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-lg transform rotate-3"></div>
                            <div className="relative bg-black/80 backdrop-blur-sm p-8 rounded-lg">
                                <h3 className="text-2xl font-bold text-white mb-4">
                                    {
                                        Lang === "en"
                                            ? "What We Offer"
                                            : Lang === "ar"
                                                ? "ماذا نقدم"
                                                : "Ce que nous offrons"
                                    }
                                </h3>
                                <ul className="space-y-3">
                                    {[
                                        Lang === "en" ? "Comprehensive battle archives" : Lang === "ar" ? "أرشيف المعارك الشامل" : "Archives complètes des batailles",
                                        Lang === "en" ? "Interactive historical maps" : Lang === "ar" ? "خرائط تاريخية تفاعلية" : "Cartes historiques interactives",
                                        Lang === "en" ? "Multimedia presentations" : Lang === "ar" ? "العروض التقديمية متعددة الوسائط" : "Présentations multimédia",
                                        Lang === "en" ? "Educational resources" : Lang === "ar" ? "الموارد التعليمية" : "Ressources éducatives",
                                        Lang === "en" ? "Multi-language support" : Lang === "ar" ? "دعم متعدد اللغات" : "Support multilingue"
                                    ].map((item, index) => (
                                        <li
                                            key={index}
                                            className={`flex items-center text-gray-300 transition-all duration-500 transform ${offerVisible ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0'}`}
                                            style={{ transitionDelay: `${index * 100}ms` }}
                                        >
                                            <span className="h-2 w-2 bg-emerald-400 rounded-full mr-3"></span>
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Developers Section */}
            <div className="py-20">
                <div ref={developersRef} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className={`text-center mb-16 transition-all duration-1000 ${developersVisible ? fadeInUp.visible : fadeInUp.hidden}`}>
                        <h2 className="text-3xl font-bold text-white mb-4">
                            {
                                Lang === "en"
                                    ? "Meet the Developers"
                                    : Lang === "ar"
                                        ? "تعرف على المطورين"
                                        : "Rencontrez les développeurs"
                            }
                        </h2>
                        <p className="text-gray-300 max-w-2xl mx-auto">
                            {
                                Lang === "en"
                                    ? "The talented team behind TarikhAlHuroob - passionate developers committed to preserving and sharing Morocco's military heritage through innovative digital solutions."
                                    : Lang === "ar"
                                        ? "فريق موهوب وراء تاريخ الحروب - مطورون شغوفون ملتزمون بالحفاظ على تراث المغرب العسكري ومشاركته من خلال الحلول الرقمية المبتكرة."
                                        : "L'équipe talentueuse derrière TarikhAlHuroob - des développeurs passionnés engagés à préserver et partager l'héritage militaire du Maroc à travers des solutions numériques innovantes."
                            }
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8">
                        {developers.map((dev, index) => (
                            <div
                                key={index}
                                className={`bg-black/30 backdrop-blur-sm rounded-lg overflow-hidden border border-emerald-500/20 hover:border-emerald-500/40 transition-all duration-700 hover:shadow-lg hover:shadow-emerald-500/10 ${developersVisible ? scaleIn.visible : scaleIn.hidden}`}
                                style={{ transitionDelay: `${index * 200}ms` }}
                            >
                                <div className="md:flex">
                                    <div className="md:w-1/3">
                                        <div className="w-full h-[290px] max-md:h-full relative overflow-hidden">
                                            <img
                                                src={dev.image}
                                                alt={dev.name}
                                                className={`absolute inset-0 w-96 h-full object-cover transition-transform duration-700 ${developersVisible ? '' : 'scale-120'}`}
                                            />
                                            <div className="absolute inset-0 bg-gradient-to-r from-black/70 to-transparent"></div>
                                        </div>
                                    </div>
                                    <div className="p-8 md:w-2/3">
                                        <h3 className="text-2xl font-bold text-white mb-2">{dev.name}</h3>
                                        <p className="text-emerald-400 font-medium mb-4">
                                            {
                                                Lang === "en"
                                                    ? dev.role.en
                                                    : Lang === "ar"
                                                        ? dev.role.ar
                                                        : dev.role.fr
                                            }
                                        </p>
                                        <p className="text-gray-300 mb-6">
                                            {
                                                Lang === "en"
                                                    ? dev.bio.en
                                                    : Lang === "ar"
                                                        ? dev.bio.ar
                                                        : dev.bio.fr
                                            }
                                        </p>
                                        <div className="flex space-x-4">
                                            {[
                                                { icon: <FaGithub className="h-6 w-6" />, href: dev.github, label: "GitHub Profile" },
                                                { icon: <FaLinkedin className="h-6 w-6" />, href: dev.linkedin, label: "LinkedIn Profile" },
                                                { icon: <FaEnvelope className="h-6 w-6" />, href: `mailto:${dev.email}`, label: "Email Contact" }
                                            ].map((social, idx) => (
                                                <a
                                                    key={idx}
                                                    href={social.href}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className={`text-gray-400 hover:text-emerald-400 transition-all duration-300 transform ${developersVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`}
                                                    style={{ transitionDelay: `${400 + idx * 100}ms` }}
                                                    aria-label={social.label}
                                                >
                                                    {social.icon}
                                                </a>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                </div>
            </div>

            {/* Contact Section */}
            <div ref={contactRef} className="bg-emerald-600 py-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className={`text-center transition-all duration-1000 ${contactVisible ? fadeInUp.visible : fadeInUp.hidden}`}>
                        <h2 className="text-3xl font-bold text-white mb-4">Get in Touch</h2>
                        <p className="text-emerald-100 mb-8 max-w-2xl mx-auto">
                            Have questions or want to contribute to our project? We'd love to hear from you.
                        </p>
                        <a
                            href="mailto:contact@tarikhalhuroob.com"
                            className="inline-flex items-center px-6 py-3 border border-white text-base font-medium rounded-md text-white hover:bg-white/10 transition-all duration-300 transform hover:scale-105"
                        >
                            Contact Us
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AboutPage;