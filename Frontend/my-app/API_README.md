# Morocco History API - Next.js Backend

This Next.js application includes a complete backend API that replicates the functionality of the original Flask backend. **The frontend has been updated to use this new local backend.**

## ✅ **Migration Complete**

The frontend has been successfully updated to use the new Next.js backend instead of the Flask backend:

- **Old API URL**: `http://localhost:5000`
- **New API URL**: `http://localhost:3000/api`
- **Status**: ✅ **Frontend updated and ready to use**

## API Endpoints

### Base URL

- `http://localhost:3000/api`

### Endpoints

#### 1. Welcome Message

- **GET** `/api/`
- **Response**: Welcome message

```json
{
  "message": "Welcome to Morocco History API"
}
```

#### 2. Get All Historical Events

- **GET** `/api/historical-events/`
- **Query Parameters**:
  - `language` (optional): Language code (`ar`, `en`, `fr`, `es`). Default: `ar`
- **Example**: `GET /api/historical-events/?language=en`
- **Response**:

```json
{
  "status": "success",
  "data": [
    {
      "big_event_name": "Period Name",
      "events": [...]
    }
  ]
}
```

#### 3. Get Events by Period

- **GET** `/api/historical-events/[period]`
- **Path Parameters**:
  - `period`: Period name (URL encoded)
- **Query Parameters**:
  - `language` (optional): Language code. Default: `ar`
- **Example**: `GET /api/historical-events/فترة%20ما%20قبل%20الإسلام?language=ar`
- **Response**:

```json
{
  "status": "success",
  "data": {
    "big_event_name": "Period Name",
    "events": [...]
  }
}
```

#### 4. Search Events

- **GET** `/api/historical-events/search`
- **Query Parameters**:
  - `q` (required): Search query
  - `language` (optional): Language code. Default: `ar`
- **Example**: `GET /api/historical-events/search?q=roman&language=en`
- **Response**:

```json
{
  "status": "success",
  "data": [
    {
      "_id": "...",
      "big_event_name": "Period Name",
      "events": [...],
      "score": 1.5
    }
  ]
}
```

## Database Configuration

The API connects to the same MongoDB Atlas cluster as the original Flask backend:

- **Database**: PFA_DB
- **Collections**:
  - `articles_ar` (Arabic)
  - `articles_en` (English)
  - `articles_fr` (French)
  - `articles_es` (Spanish)

## Environment Variables

Create a `.env.local` file in the project root (copy from `env.example`):

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://admin:w3jT8ekhQuwpBQhs@cluster0.azhlz3v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DB_NAME=PFA_DB

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api
```

## Features

- ✅ **Multi-language Support**: Arabic, English, French, Spanish
- ✅ **Period-based Filtering**: Get events by specific historical periods
- ✅ **Text Search**: Full-text search with MongoDB text indexing
- ✅ **CORS Support**: Configured for cross-origin requests
- ✅ **Error Handling**: Proper error responses with status codes
- ✅ **TypeScript**: Full type safety with interfaces
- ✅ **Connection Management**: Efficient MongoDB connection handling
- ✅ **Frontend Integration**: Updated to use local backend

## Running the Application

1. Install dependencies:

```bash
npm install
```

2. Create `.env.local` file with MongoDB configuration (copy from `env.example`)

3. Run the development server:

```bash
npm run dev
```

4. The application will be available at `http://localhost:3000`
   - **Frontend**: `http://localhost:3000`
   - **API**: `http://localhost:3000/api`

## Migration from Flask Backend

This Next.js API provides the exact same functionality as the original Flask backend:

| Flask Endpoint                        | Next.js Endpoint                      | Status |
| ------------------------------------- | ------------------------------------- | ------ |
| `GET /`                               | `GET /api/`                           | ✅     |
| `GET /api/historical-events/`         | `GET /api/historical-events/`         | ✅     |
| `GET /api/historical-events/<period>` | `GET /api/historical-events/[period]` | ✅     |
| `GET /api/historical-events/search`   | `GET /api/historical-events/search`   | ✅     |

All endpoints maintain the same request/response format and query parameters.

## Frontend Changes Made

The following files were updated to use the new backend:

1. **`src/services/apiService.ts`**:

   - Updated `API_BASE_URL` from `http://localhost:5000` to `http://localhost:3000/api`
   - Updated endpoint paths to match new API structure
   - Added handling for new response format with `status` and `data` fields
   - Added search functionality

2. **Environment Configuration**:
   - Added `NEXT_PUBLIC_API_BASE_URL` environment variable
   - Created `env.example` for easy setup

The frontend now uses the integrated Next.js backend instead of the separate Flask server!
