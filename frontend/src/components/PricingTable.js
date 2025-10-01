import React, { useState } from 'react';
import { Check, Sparkles, Zap, Crown } from 'lucide-react';

const PricingTable = ({ currentTier = 'free', onUpgrade }) => {
  const [billingPeriod, setBillingPeriod] = useState('monthly');

  const tiers = [
    {
      name: 'Free',
      tier: 'free',
      icon: Sparkles,
      price: { monthly: 0, annual: 0 },
      tagline: 'Get Started with Smart Finance',
      description: 'Perfect for tracking basics and learning AI budgeting',
      features: [
        'Manual transaction entry',
        'Limited AI insights',
        'Basic budget generation',
        '1 CSV upload per week',
        'Access to community tips',
        '1 active goal',
      ],
      cta: 'Current Plan',
      highlight: false,
    },
    {
      name: 'Pro',
      tier: 'pro',
      icon: Zap,
      price: { monthly: 399, annual: 3999 },
      tagline: 'Unlock AI-Powered Insights & Goals',
      description: 'For serious savers who want automation and intelligence',
      badge: 'Most Popular',
      features: [
        'Unlimited CSV imports',
        'Deeper AI insights & trends',
        'Full Goal Tracking (unlimited)',
        'Weekly health reports',
        'Smart Alerts (custom rules)',
        'Basic Export & Reports (PDF)',
        '30-day free trial',
        'Priority email support',
      ],
      cta: 'Start Free Trial',
      highlight: true,
    },
    {
      name: 'Premium',
      tier: 'premium',
      icon: Crown,
      price: { monthly: 999, annual: 9999 },
      tagline: 'The Full Financial Command Center',
      description: 'Real-time bank sync + Autopilot = Hands-off wealth building',
      features: [
        'Everything in Pro, plus:',
        '💳 Direct Bank API integrations (Plaid)',
        '📈 Investment portfolio tracking',
        '🤖 Autopilot: Your Financial Twin',
        '💡 Monte Carlo simulations',
        '🎯 Auto-execution rules',
        '📊 Advanced reporting (CSV/Excel)',
        '🧾 Tax planning summaries',
        '24/7 priority chat support',
      ],
      cta: 'Upgrade to Premium',
      highlight: false,
    },
  ];

  const calculateSavings = (tier) => {
    if (tier.price.annual === 0) return null;
    const monthlyCost = tier.price.monthly * 12;
    const annualCost = tier.price.annual;
    const savings = monthlyCost - annualCost;
    const percentage = Math.round((savings / monthlyCost) * 100);
    return { savings, percentage };
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {/* Billing Toggle */}
      <div className="flex justify-center items-center gap-4 mb-8">
        <span className={`text-sm font-medium ${billingPeriod === 'monthly' ? 'text-blue-600' : 'text-gray-500'}`}>
          Monthly
        </span>
        <button
          onClick={() => setBillingPeriod(billingPeriod === 'monthly' ? 'annual' : 'monthly')}
          className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          style={{ backgroundColor: billingPeriod === 'annual' ? '#3b82f6' : '#e5e7eb' }}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              billingPeriod === 'annual' ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
        <span className={`text-sm font-medium ${billingPeriod === 'annual' ? 'text-blue-600' : 'text-gray-500'}`}>
          Annual <span className="text-green-600 font-semibold">(Save 17%)</span>
        </span>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
        {tiers.map((tier) => {
          const Icon = tier.icon;
          const isCurrentTier = currentTier === tier.tier;
          const savings = calculateSavings(tier);
          const price = billingPeriod === 'monthly' ? tier.price.monthly : tier.price.annual;

          return (
            <div
              key={tier.name}
              className={`relative rounded-2xl p-6 sm:p-8 transition-all duration-300 ${
                tier.highlight
                  ? 'border-2 border-blue-500 shadow-2xl scale-105 bg-gradient-to-br from-blue-50 to-white'
                  : 'border border-gray-200 shadow-lg bg-white hover:shadow-xl'
              }`}
            >
              {/* Badge */}
              {tier.badge && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-1 rounded-full text-xs font-bold shadow-lg">
                    {tier.badge}
                  </span>
                </div>
              )}

              {/* Header */}
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 mb-4">
                  <Icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                <p className="text-sm font-semibold text-blue-600 mb-1">{tier.tagline}</p>
                <p className="text-xs text-gray-600">{tier.description}</p>
              </div>

              {/* Price */}
              <div className="text-center mb-6 border-y border-gray-200 py-6">
                <div className="flex items-baseline justify-center gap-2">
                  <span className="text-4xl font-bold text-gray-900">₹{price}</span>
                  {price > 0 && (
                    <span className="text-gray-500 text-sm">
                      /{billingPeriod === 'monthly' ? 'mo' : 'yr'}
                    </span>
                  )}
                </div>
                {billingPeriod === 'annual' && savings && (
                  <p className="text-sm text-green-600 font-semibold mt-2">
                    Save ₹{savings.savings} ({savings.percentage}% off)
                  </p>
                )}
                {tier.tier === 'pro' && billingPeriod === 'monthly' && (
                  <p className="text-xs text-blue-600 mt-2">30-day free trial included</p>
                )}
              </div>

              {/* Features */}
              <ul className="space-y-3 mb-8">
                {tier.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* CTA Button */}
              <button
                onClick={() => !isCurrentTier && onUpgrade(tier.tier, billingPeriod)}
                disabled={isCurrentTier}
                className={`w-full py-3 px-6 rounded-lg font-semibold transition-all duration-200 ${
                  isCurrentTier
                    ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                    : tier.highlight
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg hover:shadow-xl hover:scale-105'
                    : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg'
                }`}
              >
                {isCurrentTier ? tier.cta.replace(/Start|Upgrade to/, 'Current Plan') : tier.cta}
              </button>
            </div>
          );
        })}
      </div>

      {/* FAQ / Trust Indicators */}
      <div className="mt-12 text-center">
        <p className="text-sm text-gray-600">
          🔒 <span className="font-semibold">Bank-level security</span> • All plans include encrypted data storage
        </p>
        <p className="text-xs text-gray-500 mt-2">Cancel anytime • No hidden fees • 100% money-back guarantee</p>
      </div>
    </div>
  );
};

export default PricingTable;
