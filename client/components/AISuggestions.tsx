import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface ProactiveSuggestion {
  id: string;
  text: string;
  icon: string;
}

interface AISuggestionsProps {
  navigation: any;
  driverId: string;
  maxSuggestions?: number;
}

const AISuggestionsComponent: React.FC<AISuggestionsProps> = ({ 
  navigation, 
  driverId, 
  maxSuggestions = 3 
}) => {
  const [suggestions, setSuggestions] = useState<ProactiveSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const serverUrl = 'http://localhost:8000/api/v1'; // Adjust based on your server config

  useEffect(() => {
    loadSuggestions();
  }, [driverId]);

  const loadSuggestions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${serverUrl}/ai/suggestions/${driverId}`);
      if (response.ok) {
        const data = await response.json();
        const formattedSuggestions = data.suggestions
          .slice(0, maxSuggestions)
          .map((suggestion: string, index: number) => ({
            id: `suggestion_${index}`,
            text: suggestion,
            icon: getSuggestionIcon(suggestion)
          }));
        setSuggestions(formattedSuggestions);
      }
    } catch (error) {
      console.warn('Failed to load AI suggestions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getSuggestionIcon = (suggestion: string): string => {
    if (suggestion.includes('🔥') || suggestion.includes('surge')) return 'flame';
    if (suggestion.includes('☔') || suggestion.includes('rain')) return 'rainy';
    if (suggestion.includes('❄️') || suggestion.includes('snow')) return 'snow';
    if (suggestion.includes('🌅') || suggestion.includes('morning')) return 'sunny';
    if (suggestion.includes('🌆') || suggestion.includes('evening')) return 'moon';
    if (suggestion.includes('🌙') || suggestion.includes('night')) return 'moon-outline';
    if (suggestion.includes('⭐') || suggestion.includes('break')) return 'star';
    if (suggestion.includes('🚗') || suggestion.includes('start')) return 'car';
    return 'information-circle';
  };

  const handleSuggestionPress = (suggestion: ProactiveSuggestion) => {
    const questionText = `Tell me more about: ${suggestion.text.replace(/[🔥☔❄️🌅🌆🌙⭐🚗]/g, '').trim()}`;
    
    navigation.navigate('AIChat', {
      initialMessage: questionText
    });
  };

  const handleViewAllPress = () => {
    navigation.navigate('AIChat');
  };

  if (suggestions.length === 0 && !isLoading) {
    return null;
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Ionicons name="bulb" size={20} color="#FF9500" />
          <Text style={styles.title}>AI Suggestions</Text>
        </View>
        <TouchableOpacity onPress={handleViewAllPress} style={styles.viewAllButton}>
          <Text style={styles.viewAllText}>Chat</Text>
          <Ionicons name="chevron-forward" size={16} color="#007AFF" />
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Getting suggestions...</Text>
        </View>
      ) : (
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.suggestionsContainer}
        >
          {suggestions.map((suggestion) => (
            <TouchableOpacity
              key={suggestion.id}
              style={styles.suggestionCard}
              onPress={() => handleSuggestionPress(suggestion)}
            >
              <Ionicons 
                name={suggestion.icon as any} 
                size={24} 
                color="#007AFF" 
                style={styles.suggestionIcon} 
              />
              <Text style={styles.suggestionText} numberOfLines={3}>
                {suggestion.text}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 8,
  },
  viewAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewAllText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
    marginRight: 4,
  },
  loadingContainer: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
  },
  suggestionsContainer: {
    paddingRight: 16,
  },
  suggestionCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    padding: 12,
    marginRight: 12,
    width: 200,
    minHeight: 80,
    borderLeftWidth: 3,
    borderLeftColor: '#007AFF',
  },
  suggestionIcon: {
    marginBottom: 8,
  },
  suggestionText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 18,
    flex: 1,
  },
});

export default AISuggestionsComponent;