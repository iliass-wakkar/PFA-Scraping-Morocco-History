import { FaGithub, FaLinkedin, FaEnvelope } from 'react-icons/fa';
import { GiFlexibleStar } from 'react-icons/gi';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import '../i18n';
import Image from 'next/image';

const About = () => {
  const { t } = useTranslation();
  const developers = [
    {
      name: "Iliass Wakkar",
      role: t('about.developers.0.role'),
      bio: t('about.developers.0.bio'),
      image: "/assets/iliass_pfp.jpg",
      github: "https://github.com/iliass-wakkar",
      linkedin: "https://linkedin.com/in/iliass",
      email: "iliass@example.com"
    },
    {
      name: "Rochdi Mohamed Amine",
      role: t('about.developers.1.role'),
      bio: t('about.developers.1.bio'),
      image: "/assets/rocmine_pfp.jpg",
      github: "https://github.com/rocmine",
      linkedin: "https://linkedin.com/in/rocmine",
      email: "rochdi@example.com"
    }
  ];

  const features = [
    {
      icon: <GiFlexibleStar className="h-8 w-8 text-green-600" />,
      title: t('about.features.0.title'),
      description: t('about.features.0.description')
    },
    {
      icon: <GiFlexibleStar className="h-8 w-8 text-red-500" />,
      title: t('about.features.1.title'),
      description: t('about.features.1.description')
    },
    {
      icon: <GiFlexibleStar className="h-8 w-8 text-green-600" />,
      title: t('about.features.2.title'),
      description: t('about.features.2.description')
    }
  ];

  return (
    <div className="relative bg-gray-100 min-h-screen flex flex-col items-center w-9/12 mx-auto border-0 rounded-lg" id="about">
      {/* Content */}
      <div className="relative z-10  flex flex-col mx-auto py-15 bg-white border-0 rounded-xl">
        {/* Hero Section */}
        <motion.div
          className="px-4 sm:px-6 lg:px-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <div className="text-center mb-20">
            <motion.h1
              className="text-4xl md:text-6xl font-bold text-gray-900 mb-6"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              {t('about.title')}
            </motion.h1>
            <motion.p
              className="text-xl text-gray-600 max-w-3xl mx-auto mb-12"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              {t('about.desc')}
            </motion.p>
            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mx-auto">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  className="bg-white border border-gray-200 p-6 rounded-xl text-center shadow-md hover:shadow-lg transition-shadow"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.6 + index * 0.2 }}
                  whileHover={{ scale: 1.05 }}
                >
                  <div className="mb-4 flex justify-center">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-500">
                    {feature.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
        {/* Team Section */}
        <motion.div
          className="px-4 sm:px-6 lg:px-8 py-20"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <motion.h2
            className="text-3xl md:text-5xl font-bold text-gray-900 text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            {t('about.team')}
          </motion.h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            {developers.map((dev, index) => (
              <motion.div
                key={dev.name}
                className="bg-white border border-gray-200 rounded-xl p-8 shadow-md hover:shadow-lg transition-shadow"
                initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, delay: 0.2 + index * 0.2 }}
                whileHover={{ scale: 1.02 }}
              >
                <div className="flex flex-col md:flex-row items-center gap-8">
                  <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-green-500">
                    <Image
                      src={dev.image}
                      alt={dev.name}
                      width={128}
                      height={128}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1 text-center md:text-left">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{dev.name}</h3>
                    <p className="text-green-600 mb-4">{dev.role}</p>
                    <p className="text-gray-500 mb-6">{dev.bio}</p>
                    <div className="flex justify-center md:justify-start gap-4">
                      <a href={dev.github} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-green-600 transition-colors">
                        <FaGithub className="w-6 h-6" />
                      </a>
                      <a href={dev.linkedin} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-green-600 transition-colors">
                        <FaLinkedin className="w-6 h-6" />
                      </a>
                      <a href={`mailto:${dev.email}`} className="text-gray-400 hover:text-red-500 transition-colors">
                        <FaEnvelope className="w-6 h-6" />
                      </a>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default About; 