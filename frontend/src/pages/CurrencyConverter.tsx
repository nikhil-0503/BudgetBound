import React, { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { DollarSign, ArrowRightLeft, TrendingUp, Info, MapPin, CreditCard } from 'lucide-react';
import api from '../services/api';

interface ExchangeRates {
  [key: string]: number;
}

interface RatesResponse {
  rates: ExchangeRates;
  last_updated: string | null;
  source: string;
}

export const CurrencyConverter: React.FC = () => {
  usePageTitle('Currency Converter | BudgetBound');
  const [amount, setAmount] = useState<number>(10000);
  const [fromCurrency, setFromCurrency] = useState<string>('INR');
  const [toCurrency, setToCurrency] = useState<string>('USD');
  const [convertedAmount, setConvertedAmount] = useState<number | null>(null);
  const [exchangeRate, setExchangeRate] = useState<number | null>(null);
  const [allRates, setAllRates] = useState<ExchangeRates>({});
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currencies = [
    { code: 'INR', name: 'Indian Rupee', symbol: '₹', flag: '🇮🇳' },
    { code: 'USD', name: 'US Dollar', symbol: '$', flag: '🇺🇸' },
    { code: 'EUR', name: 'Euro', symbol: '€', flag: '🇪🇺' },
    { code: 'GBP', name: 'British Pound', symbol: '£', flag: '🇬🇧' },
    { code: 'AED', name: 'UAE Dirham', symbol: 'د.إ', flag: '🇦🇪' },
    { code: 'THB', name: 'Thai Baht', symbol: '฿', flag: '🇹🇭' },
    { code: 'SGD', name: 'Singapore Dollar', symbol: 'S$', flag: '🇸🇬' },
    { code: 'MYR', name: 'Malaysian Ringgit', symbol: 'RM', flag: '🇲🇾' },
    { code: 'IDR', name: 'Indonesian Rupiah', symbol: 'Rp', flag: '🇮🇩' },
    { code: 'VND', name: 'Vietnamese Dong', symbol: '₫', flag: '🇻🇳' },
    { code: 'NPR', name: 'Nepalese Rupee', symbol: 'रू', flag: '🇳🇵' },
    { code: 'LKR', name: 'Sri Lankan Rupee', symbol: 'Rs', flag: '🇱🇰' },
    { code: 'TRY', name: 'Turkish Lira', symbol: '₺', flag: '🇹🇷' },
    { code: 'QAR', name: 'Qatari Riyal', symbol: 'ر.ق', flag: '🇶🇦' },
    { code: 'OMR', name: 'Omani Rial', symbol: 'ر.ع.', flag: '🇴🇲' },
    { code: 'JPY', name: 'Japanese Yen', symbol: '¥', flag: '🇯🇵' },
    { code: 'AUD', name: 'Australian Dollar', symbol: 'A$', flag: '🇦🇺' },
    { code: 'CAD', name: 'Canadian Dollar', symbol: 'C$', flag: '🇨🇦' }
  ];

  useEffect(() => {
    fetchAllRates();
  }, []);

  useEffect(() => {
    if (amount > 0) {
      convertCurrency();
    }
  }, [amount, fromCurrency, toCurrency]);

  const fetchAllRates = async () => {
    try {
      const response = await api.get('/api/currency/rates', {
        params: { base: 'INR' }
      });
      setAllRates(response.data.rates);
      setLastUpdated(response.data.last_updated);
    } catch (err) {
      console.error('Failed to fetch exchange rates:', err);
    }
  };

  const convertCurrency = async () => {
    if (amount <= 0) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/api/currency/convert', {
        params: {
          amount,
          from_currency: fromCurrency,
          to_currency: toCurrency
        }
      });

      setConvertedAmount(response.data.converted_amount);
      setExchangeRate(response.data.exchange_rate);
      if (response.data.last_updated) {
        setLastUpdated(response.data.last_updated);
      }
    } catch (err: any) {
      console.error(err);
      setError('Failed to convert currency. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const swapCurrencies = () => {
    setFromCurrency(toCurrency);
    setToCurrency(fromCurrency);
  };

  const getCurrencyInfo = (code: string) => {
    return currencies.find(c => c.code === code);
  };

  const popularConversions = [
    { from: 'INR', to: 'USD', label: '₹ to $' },
    { from: 'INR', to: 'EUR', label: '₹ to €' },
    { from: 'INR', to: 'AED', label: '₹ to Dirham' },
    { from: 'INR', to: 'THB', label: '₹ to Baht' },
    { from: 'USD', to: 'INR', label: '$ to ₹' },
    { from: 'EUR', to: 'INR', label: '€ to ₹' }
  ];

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <p className="eyebrow-rule text-marigold-700 dark:text-marigold-400 text-xs font-semibold">Travel Tools</p>
        <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-paper-50 mt-1">
          Currency Converter
        </h1>
        <p className="text-sm text-paper-600 dark:text-paper-400 mt-2">
          Convert currencies with live exchange rates
          {lastUpdated && (
            <span className="ml-2 text-xs text-marigold-600 dark:text-marigold-400">
              • Updated {new Date(lastUpdated).toLocaleString()}
            </span>
          )}
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Converter */}
        <div className="lg:col-span-2 space-y-6">
          <div className="ticket p-8">
            {/* Amount Input */}
            <div className="mb-6">
              <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">
                Amount
              </label>
              <input
                type="number"
                min="1"
                step="100"
                value={amount}
                onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl px-6 py-4 text-2xl font-bold text-paper-900 dark:text-white focus:outline-none focus:border-marigold-500"
              />
            </div>

            {/* Currency Selection */}
            <div className="grid grid-cols-[1fr,auto,1fr] gap-4 items-end mb-6">
              {/* From Currency */}
              <div>
                <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">
                  From
                </label>
                <select
                  value={fromCurrency}
                  onChange={(e) => setFromCurrency(e.target.value)}
                  className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl px-4 py-3 text-sm text-paper-900 dark:text-white focus:outline-none focus:border-marigold-500"
                >
                  {currencies.map(currency => (
                    <option key={currency.code} value={currency.code}>
                      {currency.flag} {currency.code} - {currency.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Swap Button */}
              <button
                onClick={swapCurrencies}
                className="mb-3 p-3 rounded-lg bg-marigold-100 dark:bg-marigold-900 text-marigold-600 dark:text-marigold-300 hover:bg-marigold-200 dark:hover:bg-marigold-800 transition-colors"
              >
                <ArrowRightLeft size={20} />
              </button>

              {/* To Currency */}
              <div>
                <label className="block text-xs font-semibold text-paper-600 dark:text-paper-400 mb-2">
                  To
                </label>
                <select
                  value={toCurrency}
                  onChange={(e) => setToCurrency(e.target.value)}
                  className="w-full bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl px-4 py-3 text-sm text-paper-900 dark:text-white focus:outline-none focus:border-marigold-500"
                >
                  {currencies.map(currency => (
                    <option key={currency.code} value={currency.code}>
                      {currency.flag} {currency.code} - {currency.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Result */}
            {convertedAmount !== null && (
              <div className="bg-gradient-to-r from-marigold-50 to-amber-50 dark:from-marigold-950/30 dark:to-amber-950/30 rounded-xl p-6 border border-marigold-200 dark:border-marigold-900">
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-sm text-paper-600 dark:text-paper-400">Converted Amount</span>
                  {exchangeRate && (
                    <span className="text-xs text-paper-500 dark:text-paper-500">
                      Rate: 1 {fromCurrency} = {exchangeRate.toFixed(4)} {toCurrency}
                    </span>
                  )}
                </div>
                <div className="text-3xl font-bold text-marigold-700 dark:text-marigold-300">
                  {getCurrencyInfo(toCurrency)?.symbol} {convertedAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="text-sm text-paper-600 dark:text-paper-400 mt-1">
                  {getCurrencyInfo(toCurrency)?.name}
                </div>
              </div>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg text-sm text-red-700 dark:text-red-300">
                {error}
              </div>
            )}
          </div>

          {/* Popular Conversions */}
          <div className="ticket p-6">
            <h2 className="font-display text-lg font-semibold text-ink-900 dark:text-paper-50 mb-4">
              Popular Conversions
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {popularConversions.map((conv, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setFromCurrency(conv.from);
                    setToCurrency(conv.to);
                  }}
                  className="p-3 bg-paper-50 dark:bg-paper-900 hover:bg-marigold-50 dark:hover:bg-marigold-950/30 border border-paper-200 dark:border-paper-700 hover:border-marigold-300 dark:hover:border-marigold-800 rounded-lg text-sm font-medium text-paper-700 dark:text-paper-300 transition-colors"
                >
                  {conv.label}
                </button>
              ))}
            </div>
          </div>

          {/* Exchange Rate Table */}
          {Object.keys(allRates).length > 0 && (
            <div className="ticket p-6">
              <h2 className="font-display text-lg font-semibold text-ink-900 dark:text-paper-50 mb-4 flex items-center gap-2">
                <TrendingUp size={20} className="text-marigold-600" />
                Exchange Rates (INR Base)
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {Object.entries(allRates).slice(0, 12).map(([currency, rate]) => {
                  const info = getCurrencyInfo(currency);
                  return (
                    <div key={currency} className="bg-paper-50 dark:bg-paper-900 rounded-lg p-3">
                      <div className="text-lg mb-1">{info?.flag}</div>
                      <div className="text-xs text-paper-600 dark:text-paper-400 mb-1">{currency}</div>
                      <div className="text-sm font-semibold text-paper-900 dark:text-white">
                        {rate.toFixed(4)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar - Tips & Info */}
        <div className="space-y-6">
          {/* Currency Tips */}
          <div className="ticket p-6">
            <h3 className="font-display text-lg font-semibold text-ink-900 dark:text-paper-50 mb-4 flex items-center gap-2">
              <Info size={18} className="text-marigold-600" />
              Travel Tips
            </h3>
            <div className="space-y-4 text-sm text-paper-700 dark:text-paper-300">
              <div className="flex items-start gap-3">
                <MapPin size={16} className="text-marigold-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium mb-1">Know Before You Go</p>
                  <p className="text-xs text-paper-600 dark:text-paper-400">
                    Research local payment customs and preferred currency for your destination
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <DollarSign size={16} className="text-marigold-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium mb-1">Best Exchange Rates</p>
                  <p className="text-xs text-paper-600 dark:text-paper-400">
                    ATMs typically offer better rates than airport currency exchanges
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CreditCard size={16} className="text-marigold-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium mb-1">Card vs Cash</p>
                  <p className="text-xs text-paper-600 dark:text-paper-400">
                    Use cards for major purchases, carry local cash for small vendors
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Note */}
          <div className="ticket bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900 p-4">
            <div className="flex items-start gap-3">
              <TrendingUp size={16} className="text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-emerald-800 dark:text-emerald-200">
                <p className="font-semibold mb-1">Live Exchange Rates</p>
                <p>
                  Rates are fetched from exchangerate-api.com and updated hourly. 
                  Actual rates may vary based on your bank or exchange service fees.
                </p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="ticket p-6">
            <h3 className="font-display text-sm font-semibold text-ink-900 dark:text-paper-50 mb-3">
              Quick Actions
            </h3>
            <div className="space-y-2">
              <button
                onClick={() => setAmount(10000)}
                className="w-full text-left px-3 py-2 rounded-lg bg-paper-50 dark:bg-paper-900 hover:bg-marigold-50 dark:hover:bg-marigold-950/30 text-sm text-paper-700 dark:text-paper-300 transition-colors"
              >
                Set ₹10,000
              </button>
              <button
                onClick={() => setAmount(50000)}
                className="w-full text-left px-3 py-2 rounded-lg bg-paper-50 dark:bg-paper-900 hover:bg-marigold-50 dark:hover:bg-marigold-950/30 text-sm text-paper-700 dark:text-paper-300 transition-colors"
              >
                Set ₹50,000
              </button>
              <button
                onClick={() => setAmount(100000)}
                className="w-full text-left px-3 py-2 rounded-lg bg-paper-50 dark:bg-paper-900 hover:bg-marigold-50 dark:hover:bg-marigold-950/30 text-sm text-paper-700 dark:text-paper-300 transition-colors"
              >
                Set ₹1,00,000
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
