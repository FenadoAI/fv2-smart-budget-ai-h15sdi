import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  PlusCircle,
  Upload,
  Trash2,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  Sparkles,
  LogOut,
  AlertCircle,
  Loader,
  PieChart,
  Target,
  Award,
  Flame,
  Bell,
  Download,
  X
} from 'lucide-react';
import ChatWidget from '../components/ChatWidget';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const API = `${API_BASE}/api`;

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [budget, setBudget] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generatingBudget, setGeneratingBudget] = useState(false);
  const [error, setError] = useState('');
  const [showAddTransaction, setShowAddTransaction] = useState(false);
  const [newTransaction, setNewTransaction] = useState({
    date: new Date().toISOString().split('T')[0],
    description: '',
    amount: '',
    category: '',
    type: 'expense'
  });

  // New states for enhanced features
  const [goals, setGoals] = useState([]);
  const [showAddGoal, setShowAddGoal] = useState(false);
  const [newGoal, setNewGoal] = useState({
    title: '',
    target_amount: '',
    current_amount: '',
    deadline: '',
    category: ''
  });
  const [userStats, setUserStats] = useState(null);
  const [badges, setBadges] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [latestInsight, setLatestInsight] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [generatingInsight, setGeneratingInsight] = useState(false);

  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }

    const userData = JSON.parse(localStorage.getItem('user'));
    setUser(userData);
    fetchTransactions();
    fetchLatestBudget();
    fetchGoals();
    fetchUserStats();
    fetchBadges();
    fetchAchievements();
    fetchLatestInsight();
    fetchAlerts();
    checkStreak();
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/transactions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTransactions(response.data);
    } catch (err) {
      console.error('Error fetching transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLatestBudget = async () => {
    try {
      const response = await axios.get(`${API}/budget/latest`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBudget(response.data);
    } catch (err) {
      // No budget yet is okay
      if (err.response?.status !== 404) {
        console.error('Error fetching budget:', err);
      }
    }
  };

  const handleAddTransaction = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await axios.post(
        `${API}/transactions`,
        { ...newTransaction, amount: parseFloat(newTransaction.amount) },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setShowAddTransaction(false);
      setNewTransaction({
        date: new Date().toISOString().split('T')[0],
        description: '',
        amount: '',
        category: '',
        type: 'expense'
      });
      fetchTransactions();
    } catch (err) {
      setError('Failed to add transaction');
    }
  };

  const handleDeleteTransaction = async (id) => {
    try {
      await axios.delete(`${API}/transactions/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchTransactions();
    } catch (err) {
      setError('Failed to delete transaction');
    }
  };

  const handleUploadCSV = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API}/transactions/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      fetchTransactions();
    } catch (err) {
      setError('Failed to upload CSV');
    }
  };

  const handleGenerateBudget = async () => {
    setGeneratingBudget(true);
    setError('');

    try {
      const now = new Date();
      const response = await axios.post(
        `${API}/budget/generate`,
        { month: now.getMonth() + 1, year: now.getFullYear() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setBudget(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate budget');
    } finally {
      setGeneratingBudget(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/');
  };

  // ============= New Feature Functions =============

  // Goals
  const fetchGoals = async () => {
    try {
      const response = await axios.get(`${API}/goals`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGoals(response.data);
    } catch (err) {
      console.error('Error fetching goals:', err);
    }
  };

  const handleAddGoal = async (e) => {
    e.preventDefault();
    try {
      await axios.post(
        `${API}/goals`,
        {
          ...newGoal,
          target_amount: parseFloat(newGoal.target_amount),
          current_amount: parseFloat(newGoal.current_amount || 0)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setShowAddGoal(false);
      setNewGoal({ title: '', target_amount: '', current_amount: '', deadline: '', category: '' });
      fetchGoals();
    } catch (err) {
      setError('Failed to add goal');
    }
  };

  const handleDeleteGoal = async (id) => {
    try {
      await axios.delete(`${API}/goals/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchGoals();
    } catch (err) {
      setError('Failed to delete goal');
    }
  };

  // Gamification
  const fetchUserStats = async () => {
    try {
      const response = await axios.get(`${API}/gamification/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserStats(response.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const fetchBadges = async () => {
    try {
      const response = await axios.get(`${API}/gamification/badges`);
      setBadges(response.data);
    } catch (err) {
      console.error('Error fetching badges:', err);
    }
  };

  const fetchAchievements = async () => {
    try {
      const response = await axios.get(`${API}/gamification/achievements`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAchievements(response.data);
    } catch (err) {
      console.error('Error fetching achievements:', err);
    }
  };

  const checkStreak = async () => {
    try {
      await axios.post(
        `${API}/gamification/check-streak`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchUserStats();
    } catch (err) {
      console.error('Error checking streak:', err);
    }
  };

  // Insights
  const fetchLatestInsight = async () => {
    try {
      const response = await axios.get(`${API}/insights/latest`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLatestInsight(response.data);
    } catch (err) {
      // No insights yet is okay
      if (err.response?.status !== 404) {
        console.error('Error fetching insight:', err);
      }
    }
  };

  const handleGenerateInsight = async () => {
    setGeneratingInsight(true);
    try {
      const response = await axios.post(
        `${API}/insights/generate`,
        { period_type: 'monthly' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setLatestInsight(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate insight');
    } finally {
      setGeneratingInsight(false);
    }
  };

  // Alerts
  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API}/alerts/triggered`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlerts(response.data);
    } catch (err) {
      console.error('Error fetching alerts:', err);
    }
  };

  const handleAcknowledgeAlert = async (id) => {
    try {
      await axios.post(
        `${API}/alerts/acknowledge/${id}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchAlerts();
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  // Reports
  const handleGenerateReport = async (format) => {
    try {
      const now = new Date();
      const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
      const response = await axios.post(
        `${API}/reports/generate`,
        {
          format: format,
          period_start: lastMonth.toISOString().split('T')[0],
          period_end: now.toISOString().split('T')[0],
          include_sections: ['transactions', 'budget', 'insights']
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert(`Report generated: ${response.data.message}`);
    } catch (err) {
      setError('Failed to generate report');
    }
  };

  const totalIncome = transactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0);

  const totalExpenses = transactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0);

  const netBalance = totalIncome - totalExpenses;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - Mobile Optimized */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <h1 className="text-lg sm:text-2xl font-bold text-gray-900 truncate">
                Welcome, {user?.username}!
              </h1>
              <p className="text-xs sm:text-sm text-gray-600 hidden sm:block">Your Financial Dashboard</p>
            </div>
            <div className="flex items-center gap-2 sm:gap-4 flex-shrink-0">
              {/* Streak Counter - Compact on Mobile */}
              {userStats && userStats.current_streak > 0 && (
                <div className="flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-1 sm:py-2 bg-orange-50 border border-orange-200 rounded-lg">
                  <Flame className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
                  <span className="font-bold text-orange-700 text-xs sm:text-base">{userStats.current_streak}🔥</span>
                </div>
              )}
              {/* Alerts Badge */}
              {alerts.length > 0 && (
                <div className="relative">
                  <Bell className="w-5 h-5 sm:w-6 sm:h-6 text-gray-600" />
                  <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center text-[10px] sm:text-xs">
                    {alerts.length}
                  </span>
                </div>
              )}
              <button
                onClick={handleLogout}
                className="flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-1 sm:py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4 sm:w-5 sm:h-5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-8 pb-24 sm:pb-8">
        {error && (
          <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2 sm:gap-3">
            <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800 text-sm sm:text-base">{error}</p>
          </div>
        )}

        {/* Summary Cards - Mobile Optimized */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-6 mb-4 sm:mb-8">
          <div className="bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6 border-2 border-green-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 font-medium text-sm sm:text-base">Total Income</span>
              <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
            </div>
            <p className="text-2xl sm:text-3xl font-bold text-green-600">${totalIncome.toFixed(2)}</p>
          </div>

          <div className="bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6 border-2 border-red-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 font-medium text-sm sm:text-base">Total Expenses</span>
              <TrendingDown className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
            </div>
            <p className="text-2xl sm:text-3xl font-bold text-red-600">${totalExpenses.toFixed(2)}</p>
          </div>

          <div className={`bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6 border-2 ${netBalance >= 0 ? 'border-blue-100' : 'border-orange-100'}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 font-medium text-sm sm:text-base">Net Balance</span>
              <DollarSign className={`w-4 h-4 sm:w-5 sm:h-5 ${netBalance >= 0 ? 'text-blue-600' : 'text-orange-600'}`} />
            </div>
            <p className={`text-2xl sm:text-3xl font-bold ${netBalance >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
              ${Math.abs(netBalance).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Main Content Grid - Mobile Optimized */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-8">
          {/* Transactions Section */}
          <div className="bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Transactions</h2>
              <div className="flex gap-1 sm:gap-2">
                <label className="flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 bg-gray-100 text-gray-700 rounded-lg cursor-pointer hover:bg-gray-200 transition-colors">
                  <Upload className="w-4 h-4 sm:w-5 sm:h-5" />
                  <span className="font-medium text-xs sm:text-base hidden sm:inline">Upload CSV</span>
                  <span className="font-medium text-xs sm:hidden">CSV</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleUploadCSV}
                    className="hidden"
                  />
                </label>
                <button
                  onClick={() => setShowAddTransaction(!showAddTransaction)}
                  className="flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <PlusCircle className="w-4 h-4 sm:w-5 sm:h-5" />
                  <span className="text-xs sm:text-base">Add</span>
                </button>
              </div>
            </div>

            {showAddTransaction && (
              <form onSubmit={handleAddTransaction} className="mb-6 p-4 bg-gray-50 rounded-lg space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                    <input
                      type="date"
                      required
                      value={newTransaction.date}
                      onChange={(e) => setNewTransaction({ ...newTransaction, date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={newTransaction.amount}
                      onChange={(e) => setNewTransaction({ ...newTransaction, amount: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                      placeholder="0.00"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    required
                    value={newTransaction.description}
                    onChange={(e) => setNewTransaction({ ...newTransaction, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                    placeholder="Coffee at Starbucks"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                    <input
                      type="text"
                      value={newTransaction.category}
                      onChange={(e) => setNewTransaction({ ...newTransaction, category: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                      placeholder="Food"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                    <select
                      value={newTransaction.type}
                      onChange={(e) => setNewTransaction({ ...newTransaction, type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                    >
                      <option value="expense">Expense</option>
                      <option value="income">Income</option>
                    </select>
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Add Transaction
                </button>
              </form>
            )}

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {transactions.length === 0 ? (
                <p className="text-center text-gray-500 py-8">
                  No transactions yet. Add your first transaction to get started!
                </p>
              ) : (
                transactions.map((transaction) => (
                  <div
                    key={transaction.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <p className="font-semibold text-gray-900">{transaction.description}</p>
                        {transaction.category && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                            {transaction.category}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        {transaction.date}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <p className={`text-lg font-bold ${transaction.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                        {transaction.type === 'income' ? '+' : '-'}${transaction.amount.toFixed(2)}
                      </p>
                      <button
                        onClick={() => handleDeleteTransaction(transaction.id)}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Budget Section */}
          <div className="bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">AI Budget</h2>
              <button
                onClick={handleGenerateBudget}
                disabled={generatingBudget || transactions.length === 0}
                className="flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 bg-gradient-to-r from-blue-600 to-green-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-base"
              >
                {generatingBudget ? (
                  <>
                    <Loader className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
                    <span className="hidden sm:inline">Analyzing...</span>
                    <span className="sm:hidden">...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span className="hidden sm:inline">Generate Budget</span>
                    <span className="sm:hidden">Generate</span>
                  </>
                )}
              </button>
            </div>

            {!budget ? (
              <div className="text-center py-12">
                <PieChart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">
                  {transactions.length === 0
                    ? 'Add some transactions to generate your first budget!'
                    : 'Click "Generate Budget" to get AI-powered insights'}
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Budget Summary */}
                <div className="p-4 bg-gradient-to-br from-blue-50 to-green-50 rounded-lg">
                  <h3 className="font-bold text-gray-900 mb-3">
                    Budget for {budget.month}/{budget.year}
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Income</p>
                      <p className="text-lg font-bold text-green-600">${budget.total_income.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Expenses</p>
                      <p className="text-lg font-bold text-red-600">${budget.total_expenses.toFixed(2)}</p>
                    </div>
                  </div>
                </div>

                {/* Spending by Category */}
                <div>
                  <h3 className="font-bold text-gray-900 mb-3">Spending by Category</h3>
                  <div className="space-y-2">
                    {Object.entries(budget.spending_by_category).map(([category, amount]) => (
                      <div key={category} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span className="text-gray-700">{category}</span>
                        <span className="font-bold text-gray-900">${amount.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Savings Opportunities */}
                <div>
                  <h3 className="font-bold text-gray-900 mb-3">💡 Savings Opportunities</h3>
                  <ul className="space-y-2">
                    {budget.savings_opportunities.map((opportunity, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-green-600 font-bold">•</span>
                        {opportunity}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* AI Analysis */}
                <div>
                  <h3 className="font-bold text-gray-900 mb-3">AI Analysis</h3>
                  <div className="p-4 bg-gray-50 rounded-lg text-sm text-gray-700 whitespace-pre-line max-h-64 overflow-y-auto">
                    {budget.analysis}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Goals & Gamification Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-8 mt-4 sm:mt-8">
          {/* Goals */}
          <div className="bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Target className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
                <span className="hidden sm:inline">Goals</span>
              </h2>
              <button
                onClick={() => setShowAddGoal(!showAddGoal)}
                className="flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-xs sm:text-base"
              >
                <PlusCircle className="w-4 h-4 sm:w-5 sm:h-5" />
                <span>Add Goal</span>
              </button>
            </div>

            {showAddGoal && (
              <form onSubmit={handleAddGoal} className="mb-6 p-4 bg-gray-50 rounded-lg space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Goal Title</label>
                  <input
                    type="text"
                    required
                    value={newGoal.title}
                    onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                    placeholder="Emergency Fund"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Target Amount</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={newGoal.target_amount}
                      onChange={(e) => setNewGoal({ ...newGoal, target_amount: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                      placeholder="5000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Current Amount</label>
                    <input
                      type="number"
                      step="0.01"
                      value={newGoal.current_amount}
                      onChange={(e) => setNewGoal({ ...newGoal, current_amount: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                      placeholder="0"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Deadline (Optional)</label>
                  <input
                    type="date"
                    value={newGoal.deadline}
                    onChange={(e) => setNewGoal({ ...newGoal, deadline: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Add Goal
                </button>
              </form>
            )}

            <div className="space-y-4">
              {goals.length === 0 ? (
                <p className="text-center text-gray-500 py-8">
                  No goals yet. Set your first financial goal!
                </p>
              ) : (
                goals.map((goal) => {
                  const percentage = (goal.current_amount / goal.target_amount * 100).toFixed(1);
                  return (
                    <div key={goal.id} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-bold text-gray-900">{goal.title}</h3>
                        <button
                          onClick={() => handleDeleteGoal(goal.id)}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="mb-2">
                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                          <span>${goal.current_amount.toFixed(2)} / ${goal.target_amount.toFixed(2)}</span>
                          <span>{percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-blue-600 to-green-600 h-2 rounded-full transition-all"
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          />
                        </div>
                      </div>
                      {goal.deadline && (
                        <p className="text-xs text-gray-500">
                          Deadline: {new Date(goal.deadline).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Gamification - Badges */}
          <div className="bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6 flex items-center gap-2">
              <Award className="w-5 h-5 sm:w-6 sm:h-6 text-yellow-600" />
              Achievements
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-4">
              {badges.map((badge) => {
                const isUnlocked = achievements.some(a => a.badge_id === badge.id);
                return (
                  <div
                    key={badge.id}
                    className={`p-2 sm:p-4 rounded-lg text-center transition-all ${
                      isUnlocked
                        ? 'bg-gradient-to-br from-yellow-50 to-orange-50 border-2 border-yellow-300'
                        : 'bg-gray-100 opacity-50'
                    }`}
                  >
                    <div className="text-2xl sm:text-4xl mb-1 sm:mb-2">{badge.icon}</div>
                    <p className="font-bold text-[10px] sm:text-xs text-gray-900">{badge.name}</p>
                    <p className="text-[9px] sm:text-xs text-gray-600 mt-0.5 sm:mt-1 hidden sm:block">{badge.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Insights & Export Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-8 mt-4 sm:mt-8">
          {/* Insights */}
          <div className="bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Insights</h2>
              <button
                onClick={handleGenerateInsight}
                disabled={generatingInsight || transactions.length === 0}
                className="flex items-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 text-xs sm:text-base"
              >
                {generatingInsight ? (
                  <>
                    <Loader className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
                    <span className="hidden sm:inline">Generating...</span>
                    <span className="sm:hidden">...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span>Generate</span>
                  </>
                )}
              </button>
            </div>

            {!latestInsight ? (
              <div className="text-center py-8">
                <p className="text-gray-600">
                  {transactions.length === 0
                    ? 'Add transactions to generate insights'
                    : 'Click "Generate" to get AI-powered insights'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
                  <p className="text-sm text-gray-700 mb-3">{latestInsight.summary}</p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="text-center">
                      <p className="text-gray-600">Income</p>
                      <p className="font-bold text-green-600">${latestInsight.trends.total_income?.toFixed(2)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-600">Expenses</p>
                      <p className="font-bold text-red-600">${latestInsight.trends.total_expenses?.toFixed(2)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-600">Net</p>
                      <p className="font-bold text-blue-600">${latestInsight.trends.net?.toFixed(2)}</p>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 mb-2">Recommendations</h3>
                  <ul className="space-y-1">
                    {latestInsight.recommendations.map((rec, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                        <span className="text-purple-600">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Export & Reports */}
          <div className="bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6 flex items-center gap-2">
              <Download className="w-5 h-5 sm:w-6 sm:h-6 text-green-600" />
              Export Reports
            </h2>
            <div className="space-y-3 sm:space-y-4">
              <p className="text-gray-600 text-xs sm:text-sm">
                Generate comprehensive reports for taxes, audits, or monthly summaries.
              </p>
              <div className="grid grid-cols-2 gap-2 sm:gap-4">
                <button
                  onClick={() => handleGenerateReport('pdf')}
                  className="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 sm:py-3 bg-red-50 text-red-700 border-2 border-red-200 rounded-lg hover:bg-red-100 transition-colors font-medium text-xs sm:text-base"
                >
                  <Download className="w-4 h-4 sm:w-5 sm:h-5" />
                  <span>PDF</span>
                </button>
                <button
                  onClick={() => handleGenerateReport('excel')}
                  className="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 px-2 sm:px-4 py-2 sm:py-3 bg-green-50 text-green-700 border-2 border-green-200 rounded-lg hover:bg-green-100 transition-colors font-medium text-xs sm:text-base"
                >
                  <Download className="w-4 h-4 sm:w-5 sm:h-5" />
                  <span>Excel</span>
                </button>
              </div>
              <div className="p-3 sm:p-4 bg-blue-50 rounded-lg">
                <p className="text-xs sm:text-sm text-blue-800">
                  <strong>Tip:</strong> Reports include transactions, budget, and insights.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Alerts Section */}
        {alerts.length > 0 && (
          <div className="mt-4 sm:mt-8 bg-white rounded-lg sm:rounded-xl shadow-sm p-4 sm:p-6">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6 flex items-center gap-2">
              <Bell className="w-5 h-5 sm:w-6 sm:h-6 text-orange-600" />
              Smart Alerts ({alerts.length})
            </h2>
            <div className="space-y-2 sm:space-y-3">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-3 sm:p-4 bg-orange-50 border border-orange-200 rounded-lg">
                  <p className="text-gray-800 text-sm sm:text-base pr-2">{alert.message}</p>
                  <button
                    onClick={() => handleAcknowledgeAlert(alert.id)}
                    className="text-gray-400 hover:text-gray-600 flex-shrink-0"
                  >
                    <X className="w-4 h-4 sm:w-5 sm:h-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Chat Widget */}
      <ChatWidget />
    </div>
  );
};

export default Dashboard;
