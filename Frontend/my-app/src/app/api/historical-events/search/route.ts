import { NextRequest, NextResponse } from 'next/server';
import { databaseService } from '@/services/database';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q') || '';
    const language = searchParams.get('language') || 'ar';

    if (!query.trim()) {
      return NextResponse.json(
        {
          status: "error",
          message: "Query parameter 'q' is required"
        },
        { status: 400 }
      );
    }

    const events = await databaseService.searchEvents(query, language);
    
    return NextResponse.json({
      status: "success",
      data: events
    });
  } catch (error) {
    console.error('Error in GET /api/historical-events/search:', error);
    return NextResponse.json(
      {
        status: "error",
        message: error instanceof Error ? error.message : "Internal server error"
      },
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
} 