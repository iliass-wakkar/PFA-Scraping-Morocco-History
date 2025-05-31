# Morocco History API Documentation

## Base URL

```
http://localhost:5000
```

## Authentication

Currently, no authentication is required to access the API endpoints.

## Endpoints

### 1. Welcome Message

Returns a welcome message for the API.

- **URL**: `/`
- **Method**: `GET`
- **Response**:

```json
{
  "message": "Welcome to Morocco History API"
}
```

### 2. Get All Historical Events

Retrieves all historical events for a specific language.

- **URL**: `/api/historical-events/`
- **Method**: `GET`
- **Query Parameters**:
  - `language` (optional): Language code for the events
    - Default: `ar`
    - Available options: `ar` (Arabic), `en` (English), `fr` (French), `es` (Spanish)
- **Response**:

```json
[
  {
    "big_event_name": "فترة ما قبل الإسلام والعصور القديمة",
    "events": [
      {
        "event_name": "غزوات الوندال",
        "article_title": "غزوات الوندال (شمال أفريقيا)",
        "date": "429-534 م",
        "sections": [
          {
            "subtitle": "الخلفية التاريخية",
            "paragraphs": [
              {
                "text": "..."
              }
            ]
          }
        ]
      }
    ]
  }
]
```

### 3. Get Events by Period

Retrieves events for a specific historical period.

- **URL**: `/api/historical-events/<period_name>`
- **Method**: `GET`
- **URL Parameters**:
  - `period_name`: Name of the historical period (URL encoded)
- **Query Parameters**:
  - `language` (optional): Language code for the events
    - Default: `ar`
    - Available options: `ar`, `en`, `fr`, `es`
- **Response**:

```json
{
  "big_event_name": "فترة ما قبل الإسلام والعصور القديمة",
  "events": [
    {
      "event_name": "غزوات الوندال",
      "article_title": "غزوات الوندال (شمال أفريقيا)",
      "date": "429-534 م",
      "sections": [
        {
          "subtitle": "الخلفية التاريخية",
          "paragraphs": [
            {
              "text": "..."
            }
          ]
        }
      ]
    }
  ]
}
```

### 4. Search Events

Searches for events based on a query string.

- **URL**: `/api/historical-events/search`
- **Method**: `GET`
- **Query Parameters**:
  - `q`: Search query string
  - `language` (optional): Language code for the events
    - Default: `ar`
    - Available options: `ar`, `en`, `fr`, `es`
- **Response**:

```json
[
  {
    "big_event_name": "فترة ما قبل الإسلام والعصور القديمة",
    "events": [
      {
        "event_name": "غزوات الوندال",
        "article_title": "غزوات الوندال (شمال أفريقيا)",
        "date": "429-534 م",
        "sections": [
          {
            "subtitle": "الخلفية التاريخية",
            "paragraphs": [
              {
                "text": "..."
              }
            ]
          }
        ]
      }
    ],
    "score": 1.5
  }
]
```

## Error Responses

### 400 Bad Request

```json
{
  "status": "error",
  "message": "Invalid language code"
}
```

### 404 Not Found

```json
{
  "status": "error",
  "message": "Period not found: [period_name]"
}
```

### 500 Internal Server Error

```json
{
  "status": "error",
  "message": "Internal server error"
}
```

## Example Usage

### Get all events in Arabic

```bash
curl http://localhost:5000/api/historical-events/?language=ar
```

### Get events for a specific period in English

```bash
curl http://localhost:5000/api/historical-events/Pre-Islamic%20Period?language=en
```

### Search for events containing "وندال" in Arabic

```bash
curl http://localhost:5000/api/historical-events/search?q=وندال&language=ar
```

## Notes

- All dates are in the format specified in the data
- Text search is case-insensitive
- Results are sorted by relevance when using the search endpoint
- The API supports CORS for web client access
