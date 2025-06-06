import React, { useState, useEffect, useCallback } from 'react';
import { Plus, BookOpen, Brain, Shuffle, User, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Custom hooks for API calls
const useFlashcards = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const createFlashcard = useCallback(async (flashcardData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/flashcard`, flashcardData);
      
      const result = response.data;
      setLoading(false);
      return result;
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to create flashcard');
      setLoading(false);
      throw err;
    }
  }, []);

  const getFlashcards = useCallback(async (studentId, limit = 5) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/get-subject`, {
        params: {
          student_id: studentId,
          limit: limit
        }
      });
      
      const result = response.data;
      setLoading(false);
      return result;
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch flashcards');
      setLoading(false);
      throw err;
    }
  }, []);

  return { createFlashcard, getFlashcards, loading, error };
};

// Subject color mapping
const subjectColors = {
  Physics: 'from-blue-500 to-blue-600',
  Chemistry: 'from-green-500 to-green-600',
  Mathematics: 'from-purple-500 to-purple-600',
  Biology: 'from-pink-500 to-pink-600',
  Other: 'from-gray-500 to-gray-600'
};

const subjectIcons = {
  Physics: '⚡',
  Chemistry: '🧪',
  Mathematics: '📐',
  Biology: '🧬',
  Other: '📚'
};

// Animated Background Component
const AnimatedBackground = () => (
  <div className="fixed inset-0 -z-10 overflow-hidden">
    <div className="absolute -top-40 -right-32 w-96 h-96 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-3xl animate-pulse"></div>
    <div className="absolute -bottom-40 -left-32 w-96 h-96 bg-gradient-to-tr from-pink-400/20 to-orange-400/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-gradient-to-r from-green-400/10 to-blue-400/10 rounded-full blur-3xl animate-bounce" style={{animationDuration: '6s'}}></div>
  </div>
);

// Notification Component
const Notification = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
  const Icon = type === 'success' ? CheckCircle : AlertCircle;

  return (
    <div className={`fixed top-4 right-4 ${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 z-50 animate-slide-in`}>
      <Icon className="w-5 h-5" />
      <span className="font-medium">{message}</span>
      <button onClick={onClose} className="ml-2 text-white/80 hover:text-white">×</button>
    </div>
  );
};

// Create Flashcard Form
const CreateFlashcardForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    student_id: '',
    question: '',
    answer: ''
  });
  const [isExpanded, setIsExpanded] = useState(false);
  const { createFlashcard, loading, error } = useFlashcards();

  const handleSubmit = async () => {
    if (!formData.student_id.trim() || !formData.question.trim() || !formData.answer.trim()) {
      return;
    }

    try {
      const result = await createFlashcard(formData);
      setFormData({ student_id: '', question: '', answer: '' });
      setIsExpanded(false);
      onSuccess(`Flashcard created successfully! Subject: ${result.subject}`, 'success');
    } catch (err) {
      onSuccess(err.message, 'error');
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value.toLowerCase()
    }));
  };

  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 overflow-hidden transition-all duration-500 hover:shadow-2xl">
      <div 
        className="bg-gradient-to-r from-indigo-500 to-purple-600 p-6 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between text-white">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <Plus className={`w-6 h-6 transition-transform duration-300 ${isExpanded ? 'rotate-45' : ''}`} />
            </div>
            <div>
              <h2 className="text-xl font-bold">Create New Flashcard</h2>
              <p className="text-indigo-100 text-sm">Add a question and answer to build your deck</p>
            </div>
          </div>
          <div className="text-2xl animate-bounce">🎯</div>
        </div>
      </div>

      <div className={`transition-all duration-500 ease-in-out ${isExpanded ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0'} overflow-y-auto`}>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <User className="inline w-4 h-4 mr-2" />
              Student ID
            </label>
            <input
              type="text"
              name="student_id"
              value={formData.student_id}
              onChange={handleChange}
              placeholder="Enter your student ID"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 text-gray-900"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <Brain className="inline w-4 h-4 mr-2" />
              Question
            </label>
            <textarea
              name="question"
              value={formData.question}
              onChange={handleChange}
              placeholder="What would you like to remember?"
              rows="3"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 resize-none text-gray-900"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <CheckCircle className="inline w-4 h-4 mr-2" />
              Answer
            </label>
            <textarea
              name="answer"
              value={formData.answer}
              onChange={handleChange}
              placeholder="The answer or explanation"
              rows="3"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 resize-none text-gray-900"
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold py-3 px-6 rounded-xl hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Plus className="w-5 h-5" />
              )}
              {loading ? 'Creating...' : 'Create Flashcard'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Flashcard Component
const FlashcardItem = ({ flashcard, index }) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), index * 100);
    return () => clearTimeout(timer);
  }, [index]);

  const gradientClass = subjectColors[flashcard.subject] || subjectColors.Other;
  const icon = subjectIcons[flashcard.subject] || subjectIcons.Other;

  return (
    <div className={`transform transition-all duration-500 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`}>
      <div 
        className="relative h-64 w-full cursor-pointer group"
        onClick={() => setIsFlipped(!isFlipped)}
        style={{ perspective: '1000px' }}
      >
        <div className={`absolute inset-0 w-full h-full transition-transform duration-700 preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
          {/* Front */}
          <div className={`absolute inset-0 w-full h-full backface-hidden rounded-2xl bg-gradient-to-br ${gradientClass} p-6 flex flex-col justify-between shadow-xl hover:shadow-2xl transition-shadow duration-300`}>
            <div className="flex justify-between items-start">
              <div className="bg-white/20 backdrop-blur-sm rounded-lg px-3 py-1 text-white text-sm font-medium">
                {flashcard.subject}
              </div>
              <div className="text-2xl">{icon}</div>
            </div>
            
            <div className="text-white">
              <h3 className="font-bold text-lg mb-2">Question</h3>
              <p className="text-white/90 leading-relaxed">{flashcard.question}</p>
            </div>
            
            <div className="flex justify-between items-center text-white/80 text-sm">
              <span>Click to reveal answer</span>
              <div className="w-8 h-8 rounded-full border-2 border-white/40 flex items-center justify-center">
                <span className="text-xs">?</span>
              </div>
            </div>
          </div>

          {/* Back */}
          <div className={`absolute inset-0 w-full h-full backface-hidden rotate-y-180 rounded-2xl bg-gradient-to-br from-gray-700 to-gray-800 p-6 flex flex-col justify-between shadow-xl`}>
            <div className="flex justify-between items-start">
              <div className="bg-white/20 backdrop-blur-sm rounded-lg px-3 py-1 text-white text-sm font-medium">
                Answer
              </div>
              <div className="text-2xl">💡</div>
            </div>
            
            <div className="text-white">
              <h3 className="font-bold text-lg mb-2">Solution</h3>
              <p className="text-white/90 leading-relaxed">{flashcard.answer}</p>
            </div>
            
            <div className="flex justify-between items-center text-white/80 text-sm">
              <span>Click to see question</span>
              <div className="w-8 h-8 rounded-full border-2 border-white/40 flex items-center justify-center">
                <CheckCircle className="w-4 h-4" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Study Session Component
const StudySession = ({ onSuccess }) => {
  const [flashcards, setFlashcards] = useState([]);
  const [studentId, setStudentId] = useState('');
  const [limit, setLimit] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const { getFlashcards, error } = useFlashcards();

  const handleGetFlashcards = async () => {
    if (!studentId.trim()) {
      onSuccess('Please enter a student ID', 'error');
      return;
    }

    setIsLoading(true);
    console.log(`Attempting to fetch flashcards for student ID: ${studentId.toLowerCase()} with limit: ${limit}`);
    try {
      const cards = await getFlashcards(studentId.toLowerCase(), limit);
      setFlashcards(cards);
      console.log('Flashcards fetched successfully:', cards);
      if (cards.length === 0) {
        onSuccess('No flashcards found for this student', 'error');
      } else {
        onSuccess(`Loaded ${cards.length} flashcard${cards.length !== 1 ? 's' : ''}!`, 'success');
      }
    } catch (err) {
      onSuccess(err.message, 'error');
      console.error('Error fetching flashcards:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Study Controls */}
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-lg">
            <BookOpen className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-800">Study Session</h2>
            <p className="text-gray-600 text-sm">Review your flashcards with intelligent mixing</p>
          </div>
          <div className="ml-auto text-2xl animate-pulse">🚀</div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <User className="inline w-4 h-4 mr-2" />
              Student ID
            </label>
            <input
              type="text"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="Enter student ID"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 text-gray-900"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <Clock className="inline w-4 h-4 mr-2" />
              Number of Cards
            </label>
            <select
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all duration-200 bg-gray-50/50 text-gray-900"
            >
              <option value={5}>5 cards</option>
              <option value={10}>10 cards</option>
              <option value={15}>15 cards</option>
              <option value={20}>20 cards</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleGetFlashcards}
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold py-3 px-6 rounded-xl hover:from-emerald-600 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Shuffle className="w-5 h-5" />
              )}
              {isLoading ? 'Loading...' : 'Get Cards'}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Flashcards Grid */}
      {flashcards.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-gray-800">
              Your Study Cards ({flashcards.length})
            </h3>
            <div className="text-sm text-gray-600 bg-white/50 rounded-full px-3 py-1">
              Click cards to flip them!
            </div>
          </div>
          
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {flashcards.map((flashcard, index) => (
              <FlashcardItem key={flashcard.id} flashcard={flashcard} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
const SmartFlashcardApp = () => {
  const [notification, setNotification] = useState(null);

  const showNotification = (message, type) => {
    setNotification({ message, type });
  };

  const closeNotification = () => {
    setNotification(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 relative">
      <AnimatedBackground />
      
      {/* Header */}
      <div className="bg-white/70 backdrop-blur-md border-b border-white/20 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Smart Flashcards
                </h1>
                <p className="text-sm text-gray-600">AI-powered learning made simple</p>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-sm text-gray-600 bg-white/50 rounded-full px-4 py-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>System Ready</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          <CreateFlashcardForm onSuccess={showNotification} />
          <StudySession onSuccess={showNotification} />
        </div>
      </div>

      {/* Footer */}
      <div className="bg-white/70 backdrop-blur-md border-t border-white/20 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-600">
            <p className="text-sm">
              Built with ❤️ using React & FastAPI • Intelligent subject classification powered by AI
            </p>
          </div>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          onClose={closeNotification}
        />
      )}

      <style jsx>{`
        .preserve-3d {
          transform-style: preserve-3d;
        }
        .backface-hidden {
          backface-visibility: hidden;
        }
        .rotate-y-180 {
          transform: rotateY(180deg);
        }
        @keyframes slide-in {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default SmartFlashcardApp;