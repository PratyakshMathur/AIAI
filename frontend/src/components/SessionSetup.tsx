import React, { useState, useEffect } from 'react';
import { SessionCreate, Problem, apiService } from '../services/api';

interface SessionSetupProps {
  onSessionCreate: (sessionData: SessionCreate) => void;
}

const SessionSetup: React.FC<SessionSetupProps> = ({ onSessionCreate }) => {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [selectedProblemId, setSelectedProblemId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  
  const [formData, setFormData] = useState({
    candidate_name: '',
    interviewer_name: '',
  });

  useEffect(() => {
    // Fetch available problems on mount
    const fetchProblems = async () => {
      try {
        const data = await apiService.getAllProblems();
        setProblems(data);
        if (data.length > 0) {
          setSelectedProblemId(data[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch problems:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchProblems();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.candidate_name && selectedProblemId) {
      onSessionCreate({
        candidate_name: formData.candidate_name,
        interviewer_name: formData.interviewer_name || undefined,
        problem_statement: '',  // Will be fetched from problems.db
        problem_id: selectedProblemId
      });
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const selectedProblem = problems.find(p => p.id === selectedProblemId);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="bg-primary-600 text-white p-6">
          <h1 className="text-3xl font-bold mb-2">AI Interview Platform</h1>
          <p className="text-primary-100">
            Welcome to your behavioral interview session for data roles
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Candidate Name *
              </label>
              <input
                type="text"
                value={formData.candidate_name}
                onChange={(e) => handleChange('candidate_name', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Enter your full name"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Interviewer Name (Optional)
              </label>
              <input
                type="text"
                value={formData.interviewer_name}
                onChange={(e) => handleChange('interviewer_name', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Interviewer's name"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Problem *
            </label>
            {loading ? (
              <div className="text-gray-500">Loading problems...</div>
            ) : problems.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 text-yellow-800">
                No problems available. Please run the problem manager CLI to add problems.
              </div>
            ) : (
              <>
                <select
                  value={selectedProblemId || ''}
                  onChange={(e) => setSelectedProblemId(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                >
                  {problems.map(problem => (
                    <option key={problem.id} value={problem.id}>
                      {problem.title} ({problem.difficulty})
                    </option>
                  ))}
                </select>
                
                {selectedProblem && (
                  <div className="mt-4 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
                    <p className="text-2xl font-bold text-gray-800 text-center">
                      🚀 Hello! Let's go!
                    </p>
                    <p className="text-sm text-gray-600 text-center mt-2">
                      Your challenge is ready. Click start to begin!
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
          
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  How This Interview Works
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <ul className="list-disc list-inside space-y-1">
                    <li>You'll work in a SQL sandbox with real datasets</li>
                    <li>We track your problem-solving process, not just final answers</li>
                    <li>Ask the AI for help, but use it strategically</li>
                    <li>Your analytical thinking and query approach is what matters most</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading || problems.length === 0 || !selectedProblemId}
              className="px-6 py-3 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Start Interview Session
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SessionSetup;