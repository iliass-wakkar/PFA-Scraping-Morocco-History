import { TimelineEvent } from '../components/Timeline';

// This would be replaced with actual API calls in a real application
export class EventService {
  private static events: TimelineEvent[] = [
    {
      event_name: "الفتح الإسلامي للمغرب",
      article_title: "The Islamic Conquest of the Maghreb",
      date: {
        milady: {
          start: 683,
          end: 710
        },
        hijry: {
          start: 62,
          end: 90,
          approx: true
        }
      },
      sections: [
        {
          subtitle: "Background and Initial Incursions",
          paragraphs: [
            {
              paragraph_id: "s0_p0",
              text: "The Islamic conquest of the Maghreb (North Africa) began in the mid-1st century AH / 7th century AD and lasted nearly seventy years. This expansion was not a random event but based on a well-structured military plan initiated by the Caliphs and governors. The conquest began with initial reconnaissance campaigns. Egypt served as a base to oversee the conquest of the Maghreb. In 22 AH/643 AD, Amr ibn al-Aas seized Cyrenaica with little resistance from the Luwata and Hawwara Berbers. He also captured Tripoli after a rapid siege. In 27 AH/647 AD, Abd Allah ibn Sa'd launched an attack against Byzacena and defeated the exarch Gregorius near Suffetula (Sbeitla).",
              source_URLs: [
                "https://bokundoli.org/wp-content/uploads/2021/12/T3-12.pdf",
                "https://jfhsc.journals.ekb.eg/article_284688_be5b14e2be71f654220beefa78acc1d4.pdf"
              ]
            }
          ]
        },
        {
          subtitle: "Early Governors and Consolidation Efforts",
          paragraphs: [
            {
              paragraph_id: "s1_p0",
              text: "Muawiyah ibn Hudayj was appointed as the first governor of Africa, separating the Maghreb from Egypt. Uqba ibn Nafi al-Fihri was appointed as governor of Africa by Caliph Muawiyah ibn Abi Sufyan around 50 AH/670 AD to continue the Islamic conquest. Uqba followed the coastal route and captured Jarmath. He also founded the city of Kairouan around 50 AH, which became a military center for Muslims. Uqba built a military camp near a high point called al-Qarn in the region of Qamunya, which later became the city of Kairouan.",
              source_URLs: [
                "https://jfhsc.journals.ekb.eg/article_284688_be5b14e2be71f654220beefa78acc1d4.pdf"
              ]
            }
          ]
        }
      ]
    },
    {
      event_name: "تأسيس الدولة الإدريسية",
      article_title: "The Establishment of the Idrisid Dynasty",
      date: {
        milady: {
          start: 789,
          end: 974
        },
        hijry: {
          start: 172,
          end: 363,
          approx: true
        }
      },
      sections: [
        {
          subtitle: "Background and Origins",
          paragraphs: [
            {
              paragraph_id: "s0_p0",
              text: "The Idrisid dynasty, considered the first Shia dynasty to reach power in the Islamic world, was founded in Morocco in 172 AH (788 AD) by Idris ibn Abdullah. Idris ibn Abdullah, a descendant of Imam Hassan, fled Medina after the Battle of Fakhkh in 169 AH. The Idrisids are believed by many researchers to have followed the Zaydi Shia branch. The dynasty exerted control over the West African region for three centuries.",
              source_URLs: [
                "http://mail.jart.utq.edu.iq/index.php/main/article/view/565",
                "https://arj.urd.ac.ir/article_206983_764a118a32dbd1dc083c2708cb2a7631.pdf"
              ]
            }
          ]
        }
      ]
    },
    {
      event_name: "ثورات الأمازيغ (المغرب)",
      article_title: "Berber Revolts in Morocco: A Historical Overview",
      date: {
        milady: {
          start: 740,
          end: 743
        },
        hijry: {
          start: 122,
          end: 125,
          approx: true
        }
      },
      sections: [
        {
          subtitle: "Early Resistance to Arab Rule",
          paragraphs: [
            {
              paragraph_id: "s0_p0",
              text: "The history of Morocco is marked by numerous Berber revolts, stemming from resistance to various forms of external rule and cultural assimilation. The Arab conquest of North Africa in the 7th and 8th centuries brought Islam to the region, but also sparked resistance from the Berber populations. The Arab expansion westward along the southern Mediterranean shore, beginning twenty years after the Hijra, posed a threat to Europe and involved interactions and conflicts with the Berber populations.",
              source_URLs: [
                "https://kigiran.elpub.ru/jour/issue/viewFile/63/2#page=4",
                "https://www.cambridge.org/core/journals/bulletin-of-the-school-of-oriental-and-african-studies/article/kahena-queen-of-the-berbers/1AFF5114BB1699538E0E19C0B0E83879"
              ]
            }
          ]
        }
      ]
    }
  ];

  static getAllEvents(): TimelineEvent[] {
    return this.events;
  }

  static getEventById(id: string): TimelineEvent | null {
    // Parse the ID to find the event
    const eventIndex = parseInt(id.split('-').pop() || '0');
    return this.events[eventIndex] || null;
  }

  static getEventBySlug(slug: string): TimelineEvent | null {
    // Find event by slug (event name converted to URL-friendly format)
    return this.events.find(event => 
      event.event_name.replace(/\s+/g, '-').toLowerCase() === slug
    ) || null;
  }

  static getEventsByDateRange(startYear: number, endYear: number): TimelineEvent[] {
    return this.events.filter(event => 
      event.date.milady.start >= startYear && event.date.milady.end <= endYear
    );
  }

  static getEventsByPeriod(period: string): TimelineEvent[] {
    // Filter events by historical period
    switch (period.toLowerCase()) {
      case 'islamic-conquest':
        return this.events.filter(event => 
          event.date.milady.start >= 600 && event.date.milady.end <= 800
        );
      case 'early-dynasties':
        return this.events.filter(event => 
          event.date.milady.start >= 800 && event.date.milady.end <= 1200
        );
      default:
        return this.events;
    }
  }
} 