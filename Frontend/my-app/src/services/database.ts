import { MongoClient, Db, Collection } from 'mongodb';

export interface HistoricalEvent {
  big_event_name: string;
  events: Array<{
    event_name: string;
    article_title: string;
    sections: Array<{
      subtitle: string;
      paragraphs: Array<{
        text: string;
      }>;
    }>;
  }>;
}

export interface SearchResult {
  _id: string;
  big_event_name: string;
  events: Array<{
    event_name: string;
    article_title: string;
    sections: Array<{
      subtitle: string;
      paragraphs: Array<{
        text: string;
      }>;
    }>;
  }>;
  score?: number;
}

class DatabaseService {
  private client: MongoClient | null = null;
  private db: Db | null = null;
  private collections: Record<string, Collection> = {};

  async connect(): Promise<void> {
    if (this.client) {
      return; // Already connected
    }

    try {
      const connectionString = process.env.MONGODB_URI || "mongodb+srv://admin:w3jT8ekhQuwpBQhs@cluster0.azhlz3v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0";
      const dbName = process.env.DB_NAME || "PFA_DB";

      console.log("Attempting to connect to MongoDB...");
      
      this.client = new MongoClient(connectionString);
      await this.client.connect();
      
      // Test the connection
      await this.client.db("admin").command({ ping: 1 });
      console.log("Successfully connected to MongoDB!");

      this.db = this.client.db(dbName);
      console.log(`Connected to database: ${dbName}`);

      // Initialize collections
      this.collections = {
        'ar': this.db.collection('articles_ar'),
        'en': this.db.collection('articles_en'),
        'fr': this.db.collection('articles_fr'),
        'es': this.db.collection('articles_es')
      };

      // Verify collections exist and create text indexes
      for (const [lang, collection] of Object.entries(this.collections)) {
        const count = await collection.countDocuments({});
        console.log(`Collection ${lang} exists with ${count} documents`);

        // Create text index for search functionality
        try {
          await collection.createIndex([
            { "big_event_name": "text" },
            { "events.event_name": "text" },
            { "events.article_title": "text" },
            { "events.sections.subtitle": "text" },
            { "events.sections.paragraphs.text": "text" }
          ]);
          console.log(`Text index created for collection: ${lang}`);
        } catch {
          console.log(`Text index already exists for collection: ${lang}`);
        }
      }

    } catch (error) {
      console.error("Could not connect to MongoDB:", error);
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (this.client) {
      await this.client.close();
      this.client = null;
      this.db = null;
      this.collections = {};
    }
  }

  async getAllEvents(language: string = 'ar'): Promise<HistoricalEvent[]> {
    await this.connect();
    
    if (!this.collections[language]) {
      throw new Error(`Invalid language: ${language}`);
    }

    try {
      console.log(`Fetching all events from collection: ${language}`);
      const cursor = this.collections[language].find({}, { projection: { _id: 0 } });
      const results = await cursor.toArray();
      console.log(`Found ${results.length} events`);
      return results as unknown as HistoricalEvent[];
    } catch (error) {
      console.error("Error in getAllEvents:", error);
      throw error;
    }
  }

  async getEventsByPeriod(periodName: string, language: string = 'ar'): Promise<HistoricalEvent> {
    await this.connect();
    
    if (!this.collections[language]) {
      throw new Error(`Invalid language: ${language}`);
    }

    try {
      console.log(`Searching for period '${periodName}' in collection: ${language}`);
      const period = await this.collections[language].findOne(
        { "big_event_name": periodName },
        { projection: { _id: 0 } }
      );
      
      if (!period) {
        throw new Error(`Period not found: ${periodName}`);
      }

      console.log(`Found period: ${periodName}`);
      return period as unknown as HistoricalEvent;
    } catch (error) {
      console.error("Error in getEventsByPeriod:", error);
      throw error;
    }
  }

  async searchEvents(query: string, language: string = 'ar'): Promise<SearchResult[]> {
    await this.connect();
    
    if (!this.collections[language]) {
      throw new Error(`Invalid language: ${language}`);
    }

    try {
      console.log(`Searching for '${query}' in collection: ${language}`);
      
      // Clean and prepare the query
      const cleanQuery = query.trim().toLowerCase();
      const queryWords = cleanQuery.split(/\s+/).filter(word => word.length > 0);
      
      let searchQuery = {};
      
      // For short queries (1-2 words), try text search first
      if (queryWords.length <= 2 && cleanQuery.length > 2) {
        try {
          // Try text search first
          const textResults = await this.collections[language].find(
            { $text: { $search: cleanQuery } },
            { 
              projection: { 
                score: { $meta: "textScore" },
                _id: 1,
                big_event_name: 1,
                events: 1
              }
            }
          ).sort({ score: { $meta: "textScore" } }).toArray();
          
          if (textResults.length > 0) {
            console.log(`Text search found ${textResults.length} results`);
            return textResults as unknown as SearchResult[];
          }
        } catch {
          console.log('Text search failed, falling back to regex search');
        }
      }
      
      // Fallback to regex search for all cases
      const searchConditions = [];
      
      // 1. Exact phrase search
      if (cleanQuery.length > 2) {
        searchConditions.push({
          $or: [
            { big_event_name: { $regex: cleanQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), $options: 'i' } },
            { "events.event_name": { $regex: cleanQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), $options: 'i' } },
            { "events.article_title": { $regex: cleanQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), $options: 'i' } },
            { "events.sections.subtitle": { $regex: cleanQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), $options: 'i' } },
            { "events.sections.paragraphs.text": { $regex: cleanQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), $options: 'i' } }
          ]
        });
      }
      
      // 2. Word-by-word search for longer queries
      if (queryWords.length > 1) {
        const wordConditions = queryWords.map(word => ({
          $or: [
            { big_event_name: { $regex: word, $options: 'i' } },
            { "events.event_name": { $regex: word, $options: 'i' } },
            { "events.article_title": { $regex: word, $options: 'i' } },
            { "events.sections.subtitle": { $regex: word, $options: 'i' } },
            { "events.sections.paragraphs.text": { $regex: word, $options: 'i' } }
          ]
        }));
        searchConditions.push({ $and: wordConditions });
      }
      
      // Combine search conditions
      if (searchConditions.length > 0) {
        searchQuery = { $or: searchConditions };
      }
      
      console.log('Search query:', JSON.stringify(searchQuery, null, 2));
      
      // Execute search
      const cursor = this.collections[language].find(
        searchQuery,
        { 
          projection: { 
            _id: 1,
            big_event_name: 1,
            events: 1
          }
        }
      );
      
      const results = await cursor.toArray();
      
      // Custom scoring and sorting
      const scoredResults = results.map(doc => {
        let score = 0;
        
        // Boost score for exact matches in big_event_name
        if (doc.big_event_name.toLowerCase().includes(cleanQuery)) {
          score += 10;
        }
        
        // Boost score for partial matches
        if (doc.big_event_name.toLowerCase().includes(queryWords[0] || '')) {
          score += 5;
        }
        
        // Boost score for matches in event names and titles
        doc.events.forEach((event: HistoricalEvent['events'][0]) => {
          if (event.event_name.toLowerCase().includes(cleanQuery)) {
            score += 3;
          }
          if (event.article_title.toLowerCase().includes(cleanQuery)) {
            score += 3;
          }
        });
        
        return { ...doc, score };
      });
      
      // Sort by score (highest first)
      scoredResults.sort((a, b) => (b.score || 0) - (a.score || 0));
      
      console.log(`Found ${scoredResults.length} results for query: ${query}`);
      return scoredResults as unknown as SearchResult[];
    } catch (error) {
      console.error("Error in searchEvents:", error);
      throw error;
    }
  }
}

// Export singleton instance
export const databaseService = new DatabaseService(); 