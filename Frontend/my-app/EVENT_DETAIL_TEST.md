# Event Detail Page Test Guide

## ✅ **Issue Fixed**

**Problem**: Event detail pages were showing "Event Not Found" when clicking on events from the timeline, especially for Arabic event names.

**Root Cause**: The event ID parsing logic couldn't handle URL-encoded Arabic characters properly.

**Solution**:

1. Added URL decoding for event IDs
2. Simplified event finding logic to work directly with API data
3. Added fallback search by event name
4. Added comprehensive debugging information

## **Test Cases**

### **Basic Navigation Tests**

#### **From Timeline Page**

- ✅ **Click on any event**: Should navigate to event detail page
- ✅ **Arabic event names**: Should work with URL-encoded characters
- ✅ **English event names**: Should work normally
- ✅ **French event names**: Should work normally
- ✅ **Spanish event names**: Should work normally

#### **From Search Results**

- ✅ **Click on search result**: Should navigate to event detail page
- ✅ **Different languages**: Should work in all languages
- ✅ **Long event names**: Should handle complex names

### **Event Detail Page Tests**

#### **Content Display**

- ✅ **Event title**: Should display correctly
- ✅ **Event date**: Should show both Gregorian and Hijri dates
- ✅ **Article content**: Should display all sections and paragraphs
- ✅ **Sources**: Should show source URLs when available

#### **Navigation**

- ✅ **Back to Timeline**: Should return to timeline page
- ✅ **Language change**: Should reload content in new language
- ✅ **Browser back**: Should work normally

### **Language-Specific Tests**

#### **Arabic Events**

- ✅ **Arabic event names**: Should work with complex Arabic text
- ✅ **Arabic content**: Should display Arabic text correctly
- ✅ **RTL layout**: Should use right-to-left layout

#### **English Events**

- ✅ **English event names**: Should work normally
- ✅ **English content**: Should display correctly
- ✅ **LTR layout**: Should use left-to-right layout

## **How to Test**

1. **Start the development server**:

   ```bash
   npm run dev
   ```

2. **Test Timeline Navigation**:

   - Open `http://localhost:3000/timeline`
   - Click on any event card
   - Verify the event detail page loads correctly
   - Check that all content is displayed properly

3. **Test Search Navigation**:

   - Use the search bar in the navbar
   - Click on a search result
   - Verify the event detail page loads correctly

4. **Test Language Changes**:

   - Change language using the dropdown
   - Navigate to timeline and click on an event
   - Verify the event loads in the correct language

5. **Test Arabic Events**:
   - Set language to Arabic
   - Navigate to timeline
   - Click on Arabic-named events
   - Verify they load correctly

## **Expected Behavior**

### **Event Detail Page**

- ✅ **Loading state**: Shows loading spinner while fetching data
- ✅ **Content display**: Shows event title, dates, and full article
- ✅ **Navigation**: Back button works correctly
- ✅ **Responsive**: Works on mobile and desktop

### **Error Handling**

- ✅ **Event not found**: Shows helpful error message with debug info
- ✅ **Network errors**: Shows retry button
- ✅ **Invalid URLs**: Shows appropriate error message

### **Debug Information**

- ✅ **Console logs**: Shows detailed debugging information
- ✅ **Error page**: Shows event ID, language, and API data status
- ✅ **Network tab**: Shows API calls and responses

## **Debugging**

If you encounter issues:

1. **Check browser console** for detailed logs:

   - Decoded Event ID
   - Parsed indices
   - API Data structure
   - Found event information

2. **Check the error page** for debug information:

   - Event ID (encoded and decoded)
   - Language setting
   - API data availability
   - Available events list

3. **Check network tab** for API calls:
   - Verify API calls are made with correct language
   - Check response structure
   - Look for any error responses

## **Technical Details**

### **Event ID Format**

```
${event.event_name.replace(/\s+/g, '-').toLowerCase()}-${bigEventIndex}-${eventIndex}
```

### **URL Encoding**

- Arabic characters get URL-encoded (e.g., `غزوات` becomes `%D8%BA%D8%B2%D9%88%D8%A7%D8%AA`)
- The page now properly decodes these before parsing

### **Event Finding Logic**

1. **Primary**: Parse indices from event ID and find by position
2. **Fallback**: Generate expected event ID and find by exact match
3. **Error**: Show detailed debug information if not found

### **Data Transformation**

- Works directly with API data structure
- Transforms API events to TimelineEvent format
- Handles missing or malformed data gracefully

The event detail pages should now work reliably for all event types and languages!
