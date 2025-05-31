from typing import List, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class HistoricalEventsService:
    def __init__(self):
        try:
            # MongoDB connection details
            username = "wip"
            password = "admin1234"
            host = "localhost"
            port = "27017"
            db_name = "PFA_DB"
            
            # Create connection string
            connection_string = f"mongodb://{username}:{password}@{host}:{port}/{db_name}?authSource=admin"
            print(f"Attempting to connect to MongoDB with connection string: {connection_string}")
            
            # Connect to MongoDB
            self.client = MongoClient(connection_string)
            # Test the connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
            
            self.db = self.client[db_name]
            print(f"Connected to database: {db_name}")
            
            # Initialize collections
            self.collections = {
                'ar': self.db.articles_ar,
                'en': self.db.articles_en,
                'fr': self.db.articles_fr,
                'es': self.db.articles_es
            }
            
            # Verify collections exist
            for lang, collection in self.collections.items():
                count = collection.count_documents({})
                print(f"Collection {lang} exists with {count} documents")
                
        except ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error during initialization: {e}")
            raise

    def get_all_events(self, language: str = 'ar') -> List[Dict[str, Any]]:
        """Get all historical events for a specific language"""
        try:
            if language not in self.collections:
                raise ValueError(f"Invalid language: {language}")
            
            collection = self.collections[language]
            print(f"Fetching all events from collection: {language}")
            cursor = collection.find({}, {'_id': 0})
            results = list(cursor)
            print(f"Found {len(results)} events")
            return results
        except Exception as e:
            print(f"Error in get_all_events: {e}")
            raise

    def get_events_by_period(self, period_name: str, language: str = 'ar') -> Dict[str, Any]:
        """Get events for a specific period and language"""
        try:
            if language not in self.collections:
                raise ValueError(f"Invalid language: {language}")
            
            collection = self.collections[language]
            print(f"Searching for period '{period_name}' in collection: {language}")
            period = collection.find_one({"big_event_name": period_name}, {'_id': 0})
            if period is None:
                raise ValueError(f"Period not found: {period_name}")
            
            print(f"Found period: {period_name}")
            return period
        except Exception as e:
            print(f"Error in get_events_by_period: {e}")
            raise

    def search_events(self, query: str, language: str = 'ar') -> List[Dict[str, Any]]:
        """Search events by query in a specific language"""
        try:
            if language not in self.collections:
                raise ValueError(f"Invalid language: {language}")
            
            collection = self.collections[language]
            print(f"Searching for '{query}' in collection: {language}")
            
            # Create text index if it doesn't exist
            collection.create_index([
                ("big_event_name", "text"),
                ("events.event_name", "text"),
                ("events.article_title", "text"),
                ("events.sections.subtitle", "text"),
                ("events.sections.paragraphs.text", "text")
            ])
            
            # Search in all relevant fields
            cursor = collection.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})])
            
            results = list(cursor)
            print(f"Found {len(results)} results for query: {query}")
            return results
        except Exception as e:
            print(f"Error in search_events: {e}")
            raise 