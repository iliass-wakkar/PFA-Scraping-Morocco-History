import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Input,
  VStack,
  Text,
  Link,
  InputGroup,
  InputLeftElement,
  Heading,
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import api, { SearchResult } from '../services/api';

interface SearchProps {
  language: string;
}

function Search({ language }: SearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = async (searchQuery: string) => {
    setQuery(searchQuery);
    
    if (searchQuery.trim().length === 0) {
      setResults([]);
      return;
    }

    try {
      setSearching(true);
      const data = await api.searchEvents(searchQuery, language);
      setResults(data);
    } catch (error) {
      console.error('Error searching events:', error);
    } finally {
      setSearching(false);
    }
  };

  return (
    <Box>
      <Heading mb={8}>Search Historical Events</Heading>
      <VStack spacing={8} align="stretch">
        <InputGroup>
          <InputLeftElement pointerEvents="none">
            <SearchIcon color="gray.300" />
          </InputLeftElement>
          <Input
            placeholder="Search for historical events..."
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </InputGroup>

        {searching && <Text>Searching...</Text>}

        {results.length > 0 && (
          <VStack spacing={4} align="stretch">
            {results.map((result) => (
              <Link
                as={RouterLink}
                to={`/period/${encodeURIComponent(result.big_event_name)}`}
                key={result.big_event_name}
                _hover={{ textDecoration: 'none' }}
              >
                <Box
                  p={6}
                  bg="white"
                  borderRadius="lg"
                  boxShadow="md"
                  transition="transform 0.2s"
                  _hover={{ transform: 'translateY(-2px)' }}
                >
                  <Heading size="md" mb={2}>
                    {result.big_event_name}
                  </Heading>
                  <Text color="gray.600" mb={2}>
                    {result.events.length} events found
                  </Text>
                  <Text color="gray.500" fontSize="sm">
                    Relevance score: {result.score.toFixed(2)}
                  </Text>
                </Box>
              </Link>
            ))}
          </VStack>
        )}

        {query && !searching && results.length === 0 && (
          <Text>No results found</Text>
        )}
      </VStack>
    </Box>
  );
}

export default Search; 