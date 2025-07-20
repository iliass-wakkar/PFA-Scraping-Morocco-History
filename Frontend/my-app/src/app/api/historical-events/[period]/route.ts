import { NextRequest, NextResponse } from 'next/server';
import { databaseService } from '@/services/database';

interface RouteParams {
  params: {
    period: string;
  };
}

export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const { searchParams } = new URL(request.url);
    const language = searchParams.get('language') || 'ar';
    const periodName = decodeURIComponent(params.period);

    const events = await databaseService.getEventsByPeriod(periodName, language);
    
    return NextResponse.json({
      status: "success",
      data: events
    });
  } catch (error) {
    console.error('Error in GET /api/historical-events/[period]:', error);
    
    if (error instanceof Error && error.message.includes('Period not found')) {
      return NextResponse.json(
        {
          status: "error",
          message: error.message
        },
        { status: 404 }
      );
    }
    
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