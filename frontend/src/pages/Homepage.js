import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, TrendingUp, PiggyBank, Target, Brain, FileText, Shield, Sparkles, Bot } from 'lucide-react';

const Homepage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header Navigation */}
      <nav className="px-6 py-4 max-w-7xl mx-auto flex justify-between items-center">
        <div className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
          BudgetAI
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => navigate('/pricing')}
            className="px-6 py-2 text-gray-700 hover:text-blue-600 font-medium transition-colors"
          >
            Pricing
          </button>
          <button
            onClick={() => navigate('/login')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Sign In
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="px-6 py-16 md:py-24 max-w-7xl mx-auto">
        <div className="text-center">
          {/* Autopilot Badge */}
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-100 to-pink-100 border border-purple-200 px-4 py-2 rounded-full mb-6">
            <Bot className="w-5 h-5 text-purple-600" />
            <span className="text-sm font-semibold text-purple-900">
              Introducing Autopilot: Your AI Financial Twin
            </span>
            <Sparkles className="w-4 h-4 text-purple-600" />
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6">
            Your AI Financial Twin
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
              That Actually Takes Action
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-4 max-w-3xl mx-auto">
            Not just insights—<strong>Autopilot</strong> runs 1,000+ simulations on your real finances
            and executes protective actions automatically.
          </p>
          <p className="text-lg text-gray-500 mb-12 max-w-2xl mx-auto">
            Save more, stress less. Your AI twin simulates job loss, market dips, and windfalls to protect your future.
          </p>

          {/* 3 Key Benefits */}
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-12">
            <div className="bg-white/80 backdrop-blur-sm p-6 rounded-xl shadow-lg border border-gray-100">
              <Bot className="w-10 h-10 text-blue-600 mx-auto mb-3" />
              <h3 className="font-bold text-gray-900 mb-2">Your Financial Twin</h3>
              <p className="text-sm text-gray-600">
                AI simulates job loss, market dips, windfalls to protect your future
              </p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm p-6 rounded-xl shadow-lg border border-gray-100">
              <Sparkles className="w-10 h-10 text-purple-600 mx-auto mb-3" />
              <h3 className="font-bold text-gray-900 mb-2">Auto-Execution</h3>
              <p className="text-sm text-gray-600">
                Sweep to savings, round-up investments, pause overspending—automatically
              </p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm p-6 rounded-xl shadow-lg border border-gray-100">
              <Shield className="w-10 h-10 text-green-600 mx-auto mb-3" />
              <h3 className="font-bold text-gray-900 mb-2">Risk-Free</h3>
              <p className="text-sm text-gray-600">
                24-hour rollback, full audit logs, you're always in control
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate('/signup')}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold text-lg hover:shadow-2xl transform hover:scale-105 transition-all flex items-center justify-center gap-2"
            >
              Start Free 30-Day Trial
              <ArrowRight className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigate('/pricing')}
              className="px-8 py-4 bg-white text-gray-900 rounded-lg font-semibold text-lg border-2 border-gray-200 hover:border-purple-600 hover:shadow-lg transform hover:scale-105 transition-all"
            >
              View Pricing
            </button>
          </div>

          <p className="text-sm text-gray-500 mt-4">
            No credit card required • Cancel anytime • 100% money-back guarantee
          </p>
        </div>

        {/* Feature Image */}
        <div className="mt-20 rounded-2xl overflow-hidden shadow-2xl">
          <img
            src="https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1200&h=600&fit=crop"
            alt="Financial dashboard"
            className="w-full h-auto"
          />
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-20 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Smart Features for Young Professionals
            </h2>
            <p className="text-xl text-gray-600">
              Everything you need to build better financial habits
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8 rounded-xl border-2 border-gray-100 hover:border-blue-500 hover:shadow-xl transition-all">
              <div className="w-14 h-14 bg-blue-100 rounded-lg flex items-center justify-center mb-6">
                <Brain className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">AI Budget Analysis</h3>
              <p className="text-gray-600 text-lg">
                Get personalized monthly budget recommendations powered by advanced AI.
                Understand your spending patterns and optimize your finances.
              </p>
            </div>

            <div className="p-8 rounded-xl border-2 border-gray-100 hover:border-green-500 hover:shadow-xl transition-all">
              <div className="w-14 h-14 bg-green-100 rounded-lg flex items-center justify-center mb-6">
                <PiggyBank className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Smart Savings</h3>
              <p className="text-gray-600 text-lg">
                Discover actionable savings opportunities. Identify recurring subscriptions,
                overspending categories, and easy ways to save more.
              </p>
            </div>

            <div className="p-8 rounded-xl border-2 border-gray-100 hover:border-purple-500 hover:shadow-xl transition-all">
              <div className="w-14 h-14 bg-purple-100 rounded-lg flex items-center justify-center mb-6">
                <TrendingUp className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Track Everything</h3>
              <p className="text-gray-600 text-lg">
                Manually enter transactions or upload CSV files from your bank.
                Keep all your financial data organized in one secure place.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="px-6 py-20 bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600">
              Get started in three simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-white">1</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Create Account</h3>
              <p className="text-gray-600 text-lg">
                Sign up in seconds with just your email. No credit card required.
              </p>
            </div>

            <div className="text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-white">2</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Add Transactions</h3>
              <p className="text-gray-600 text-lg">
                Enter transactions manually or upload your bank statement CSV file.
              </p>
            </div>

            <div className="text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl font-bold text-white">3</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Get AI Insights</h3>
              <p className="text-gray-600 text-lg">
                Generate your personalized budget and receive actionable savings tips.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="px-6 py-20 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <img
                src="https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800&h=600&fit=crop"
                alt="Financial planning"
                className="rounded-2xl shadow-2xl"
              />
            </div>
            <div>
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Built for Young Professionals
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Whether you're just starting your career or looking to level up your finances,
                our AI coach adapts to your unique situation.
              </p>

              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Target className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Personalized Advice</h3>
                    <p className="text-gray-600">Get guidance tailored to your income, expenses, and financial goals.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FileText className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Easy to Use</h3>
                    <p className="text-gray-600">No complicated spreadsheets. Just simple, beautiful interfaces.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Shield className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Private & Secure</h3>
                    <p className="text-gray-600">Your financial data is encrypted and never shared with third parties.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 bg-gradient-to-r from-blue-600 to-green-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Take Control of Your Finances?
          </h2>
          <p className="text-xl text-blue-100 mb-12">
            Join thousands of young professionals building better financial habits with AI guidance.
          </p>
          <button
            onClick={() => navigate('/signup')}
            className="px-12 py-5 bg-white text-blue-600 rounded-lg font-bold text-xl hover:shadow-2xl transform hover:scale-105 transition-all"
          >
            Start Free Today
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-gray-400">
            © 2025 AI Finance Assistant. Built with ❤️ for young professionals.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Homepage;
