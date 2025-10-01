import React from 'react';
import { X, Sparkles, Check, Crown } from 'lucide-react';

const UpgradeModal = ({ isOpen, onClose, feature, currentTier, requiredTier, benefits, onUpgrade }) => {
  if (!isOpen) return null;

  const tierInfo = {
    pro: {
      name: 'Pro',
      icon: Sparkles,
      price: '₹399/mo',
      color: 'from-blue-600 to-purple-600',
      trial: '30-day free trial',
    },
    premium: {
      name: 'Premium',
      icon: Crown,
      price: '₹999/mo',
      color: 'from-purple-600 to-pink-600',
      trial: '7-day free trial',
    },
  };

  const info = tierInfo[requiredTier] || tierInfo.pro;
  const Icon = info.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-scale-in">
        {/* Gradient Header */}
        <div className={`bg-gradient-to-r ${info.color} p-6 text-white relative`}>
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white hover:bg-white/20 rounded-full p-1 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>

          <div className="flex items-center gap-4 mb-4">
            <div className="bg-white/20 p-3 rounded-full">
              <Icon className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">Unlock {feature}</h2>
              <p className="text-sm opacity-90">Upgrade to {info.name}</p>
            </div>
          </div>

          {/* Pricing Badge */}
          <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full">
            <span className="text-lg font-bold">{info.price}</span>
            <span className="text-xs opacity-80">• {info.trial}</span>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Current Limitation */}
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-800">
              <span className="font-semibold">Current plan ({currentTier}):</span> This feature is not available.
            </p>
          </div>

          {/* Benefits */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">What you'll get:</h3>
            <ul className="space-y-3">
              {benefits.map((benefit, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
                    <Check className="w-4 h-4 text-green-600" />
                  </div>
                  <span className="text-sm text-gray-700">{benefit}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Additional Value Props */}
          <div className="mb-6 p-4 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border border-blue-100">
            <p className="text-xs text-gray-700 mb-2 font-semibold">✨ Also included in {info.name}:</p>
            <ul className="text-xs text-gray-600 space-y-1">
              {requiredTier === 'pro' && (
                <>
                  <li>• Unlimited CSV imports</li>
                  <li>• Deeper AI insights & multi-month trends</li>
                  <li>• Weekly financial health reports</li>
                  <li>• Smart Alerts with custom rules</li>
                </>
              )}
              {requiredTier === 'premium' && (
                <>
                  <li>• Everything in Pro</li>
                  <li>• Direct bank API integrations (Plaid)</li>
                  <li>• Autopilot: Your Financial Twin (AI simulations)</li>
                  <li>• Investment portfolio tracking</li>
                  <li>• Advanced reporting (CSV/Excel/PDF)</li>
                </>
              )}
            </ul>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col gap-3">
            <button
              onClick={() => {
                onUpgrade(requiredTier);
                onClose();
              }}
              className={`w-full bg-gradient-to-r ${info.color} text-white py-3 px-6 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105`}
            >
              {info.trial ? `Start ${info.trial.split('-')[0]}-Day Trial` : `Upgrade to ${info.name}`}
            </button>

            <button
              onClick={onClose}
              className="w-full bg-gray-100 text-gray-700 py-2 px-6 rounded-lg font-medium hover:bg-gray-200 transition-colors"
            >
              Maybe Later
            </button>
          </div>

          {/* Trust Badge */}
          <p className="text-xs text-center text-gray-500 mt-4">
            🔒 Secure payment • Cancel anytime • No hidden fees
          </p>
        </div>
      </div>
    </div>
  );
};

export default UpgradeModal;
