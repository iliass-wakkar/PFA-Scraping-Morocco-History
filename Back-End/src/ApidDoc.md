
Thought for a couple of seconds

**GET /periods/{periodId}**

> **Retrieve one “big section” (period) with its events (id, title, summary, sources).**

* **Path**
  ```
  GET /periods/ar
  ```
* **Response 200**
  ```json
  {
    "id": "1",
    "title": "فترة ما قبل الإسلام والعصور القديمة (500 ق.م - 700 م)",
    "startYear": -500,
    "endYear": 700,
    "events": [
      {
        "id": "roman-invasion-mauretania",
        "title": "الغزو الروماني لموريتانيا (40-44 م)",
        "summary": "شرعت القوات الرومانية بقيادة قيصر كلوديوس في غزو مقاطعة موريتانيا، مستثمرين انقسامات القبائل المحلية لتحقيق السيطرة على طرق التجارة وشواطئ شمال إفريقيا.",
        "sources": [
          {
            "authors": "عمرو عبد العزيز منير",
            "journal": "tabayyun.dohainstitute.org",
            "year": 2017,
            "url": "https://tabayyun.dohainstitute.org/ar/issue19/pages/art04.aspx"
          }
        ]
      },
      {
        "id": "phoenician-berber-confrontations",
        "title": "مواجهات فينيقية-أمازيغية",
        "summary": "شهد الساحل المتوسطي صدامات متكررة بين التجار الفينيقيين والقبائل الأمازيغية حول نقاط الاستيطان وحماية المرافئ.",
        "sources": [
          {
            "authors": "ليلى بن عياد",
            "journal": "مجلة الأبحاث التاريخية",
            "year": 2015,
            "url": "https://example.org/fenician-berber"
          }
        ]
      }
    ]
  }
  ```

---

**GET /periods/{periodId}/events/{eventId}**

> **Retrieve full content for one specific event.**

* **Path**
  ```
  GET /periods/1/events/roman-invasion-mauretania
  ```
* **Response 200**
  ```json
  {
    "id": "roman-invasion-mauretania",
    "title": "الغزو الروماني لموريتانيا (40-44 م)",
    "sources": [
      {
        "authors": "عمرو عبد العزيز منير",
        "journal": "tabayyun.dohainstitute.org",
        "year": 2017,
        "url": "https://tabayyun.dohainstitute.org/ar/issue19/pages/art04.aspx"
      }
    ],
    "sections": [
      {
        "subtitle": "خلفية",
        "paragraph": "كانت موريتانيا تحت سيطرة مملكة نوميديا إلى أن استغل الرومان صراعات السلالات لفرض هيمنتهم عبر سلسلة من الحملات البرية والبحرية."
      },
      {
        "subtitle": "سير الحدث",
        "paragraph": "انطلقت الحملة عام 40 م من طرطوس، واجتازت جيوش الرومان الحدود عبر وادي ملوية، واحتلت العاصمة الملكية عام 44 م بعد حصار دام ثلاثة أشهر."
      }
    ]
  }
  ```
