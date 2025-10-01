import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, Zap, Crown, Check } from 'lucide-react';
import PricingTable from '../components/PricingTable';
import axios from 'axios';

const Pricing = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

  const handleUpgrade = async (tier, billingPeriod) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');

      if (!token) {
        // Redirect to signup
        navigate('/signup', { state: { selectedTier: tier } });
        return;
      }

      // Call checkout API
      const response = await axios.post(
        `${API_BASE}/api/billing/checkout`,
        { tier, billing_period: billingPeriod },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Redirect to Stripe checkout (stub for now)
      alert(`Redirecting to checkout for ${tier} (${billingPeriod})...\nCheckout URL: ${response.data.checkout_url}`);

      // In production, redirect to Stripe:
      // window.location.href = response.data.checkout_url;
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Failed to start checkout. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">Back</span>
          </button>

          <button
            onClick={() => navigate('/login')}
            className="text-sm text-gray-600 hover:text-blue-600 font-medium"
          >
            Sign In
          </button>
        </div>
      </div>

      {/* Hero Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 text-center">
        <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
          Choose Your Financial Freedom Plan
        </h1>
        <p className="text-lg text-gray-600 mb-4">
          From basic budgeting to AI-powered autopilot, find the perfect plan for your journey
        </p>
        <p className="text-sm text-gray-500">
          Start with a <span className="font-semibold text-blue-600">free 30-day trial</span> on Pro. No credit card required.
        </p>
      </div>

      {/* Pricing Table */}
      <PricingTable onUpgrade={handleUpgrade} currentTier="free" />

      {/* Feature Comparison */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Feature Comparison</h2>

        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
              <tr>
                <th className="py-4 px-6 text-left text-sm font-semibold">Feature</th>
                <th className="py-4 px-4 text-center text-sm font-semibold">Free</th>
                <th className="py-4 px-4 text-center text-sm font-semibold">Pro</th>
                <th className="py-4 px-4 text-center text-sm font-semibold">Premium</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {[
                { feature: 'Manual transaction entry', free: true, pro: true, premium: true },
                { feature: 'AI budget generation', free: 'Basic', pro: 'Advanced', premium: 'Premium' },
                { feature: 'CSV upload', free: '1/week', pro: 'Unlimited', premium: 'Unlimited' },
                { feature: 'Active goals', free: '1', pro: 'Unlimited', premium: 'Unlimited' },
                { feature: 'Weekly health reports', free: false, pro: true, premium: true },
                { feature: 'Smart Alerts', free: false, pro: true, premium: true },
                { feature: 'PDF reports', free: 'Basic', pro: 'Basic', premium: 'Advanced' },
                { feature: 'Excel/CSV export', free: false, pro: false, premium: true },
                { feature: 'Direct bank sync (Plaid)', free: false, pro: false, premium: true },
                { feature: 'Investment tracking', free: false, pro: false, premium: true },
                { feature: 'Autopilot AI Twin', free: false, pro: false, premium: true },
                { feature: 'Tax planning summaries', free: false, pro: false, premium: true },
                { feature: 'Support', free: 'Community', pro: 'Priority Email', premium: '24/7 Chat' },
              ].map((row, idx) => (
                <tr key={idx} className={idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                  <td className="py-3 px-6 text-sm text-gray-900 font-medium">{row.feature}</td>
                  <td className="py-3 px-4 text-center text-sm">
                    {typeof row.free === 'boolean' ? (
                      row.free ? (
                        <Check className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <span className="text-gray-300">—</span>
                      )
                    ) : (
                      <span className="text-gray-700">{row.free}</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-center text-sm">
                    {typeof row.pro === 'boolean' ? (
                      row.pro ? (
                        <Check className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <span className="text-gray-300">—</span>
                      )
                    ) : (
                      <span className="text-gray-700">{row.pro}</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-center text-sm">
                    {typeof row.premium === 'boolean' ? (
                      row.premium ? (
                        <Check className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <span className="text-gray-300">—</span>
                      )
                    ) : (
                      <span className="text-gray-700">{row.premium}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Frequently Asked Questions</h2>

        <div className="space-y-6">
          {[
            {
              q: 'Can I try before I buy?',
              a: 'Yes! Pro comes with a 30-day free trial. No credit card required. Premium includes a 7-day trial.',
            },
            {
              q: 'Can I cancel anytime?',
              a: 'Absolutely. Cancel anytime from your subscription settings. No penalties, no questions asked.',
            },
            {
              q: 'Is my data secure?',
              a: 'Yes. We use bank-level AES-256 encryption for all sensitive data. Bank connections via Plaid use OAuth, and we never store your bank credentials.',
            },
            {
              q: 'What is Autopilot: Your Financial Twin?',
              a: 'Autopilot is an AI-powered simulation engine that runs 1,000+ Monte Carlo simulations on your finances to predict job loss, market dips, and windfalls. It then recommends (and can execute) protective actions automatically with your approval.',
            },
            {
              q: 'Do you offer refunds?',
              a: 'Yes, we offer a 100% money-back guarantee within 30 days of purchase if you\'re not satisfied.',
            },
            {
              q: 'Can I upgrade or downgrade later?',
              a: 'Yes! You can upgrade or downgrade at any time. We\'ll prorate the difference fairly.',
            },
          ].map((faq, idx) => (
            <div key={idx} className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{faq.q}</h3>
              <p className="text-sm text-gray-600">{faq.a}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Final CTA */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Take Control of Your Finances?</h2>
          <p className="text-lg text-white/90 mb-8">
            Join thousands of users who've already achieved their financial goals with our AI-powered platform
          </p>
          <button
            onClick={() => handleUpgrade('pro', 'monthly')}
            className="bg-white text-blue-600 px-8 py-4 rounded-lg font-bold text-lg shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-200"
          >
            Start Your Free 30-Day Trial
          </button>
          <p className="text-xs text-white/80 mt-4">No credit card required • Cancel anytime</p>
        </div>
      </div>
    </div>
  );
};

export default Pricing;
