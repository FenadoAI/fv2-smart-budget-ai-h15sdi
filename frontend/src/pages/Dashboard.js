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
  PieChart
} from 'lucide-react';

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
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, {user?.username}!
            </h1>
            <p className="text-gray-600">Your Financial Dashboard</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6 border-2 border-green-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 font-medium">Total Income</span>
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-3xl font-bold text-green-600">${totalIncome.toFixed(2)}</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border-2 border-red-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 font-medium">Total Expenses</span>
              <TrendingDown className="w-5 h-5 text-red-600" />
            </div>
            <p className="text-3xl font-bold text-red-600">${totalExpenses.toFixed(2)}</p>
          </div>

          <div className={`bg-white rounded-xl shadow-sm p-6 border-2 ${netBalance >= 0 ? 'border-blue-100' : 'border-orange-100'}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600 font-medium">Net Balance</span>
              <DollarSign className={`w-5 h-5 ${netBalance >= 0 ? 'text-blue-600' : 'text-orange-600'}`} />
            </div>
            <p className={`text-3xl font-bold ${netBalance >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
              ${Math.abs(netBalance).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Transactions Section */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Transactions</h2>
              <div className="flex gap-2">
                <label className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg cursor-pointer hover:bg-gray-200 transition-colors">
                  <Upload className="w-5 h-5" />
                  <span className="font-medium">Upload CSV</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleUploadCSV}
                    className="hidden"
                  />
                </label>
                <button
                  onClick={() => setShowAddTransaction(!showAddTransaction)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <PlusCircle className="w-5 h-5" />
                  Add
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
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">AI Budget Analysis</h2>
              <button
                onClick={handleGenerateBudget}
                disabled={generatingBudget || transactions.length === 0}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-green-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generatingBudget ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Generate Budget
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
      </div>
    </div>
  );
};

export default Dashboard;
