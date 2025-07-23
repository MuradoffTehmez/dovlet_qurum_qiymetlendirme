/**
 * Frontend Internationalization Support
 * Handles client-side translations and formatting
 */

class I18nManager {
    constructor() {
        this.currentLanguage = document.documentElement.lang || 'az';
        this.isRTL = document.documentElement.dir === 'rtl';
        this.translations = {};
        this.numberFormats = {};
        this.dateFormats = {};
        
        this.init();
    }
    
    async init() {
        await this.loadTranslations();
        this.setupNumberFormats();
        this.setupDateFormats();
        this.setupEventListeners();
    }
    
    async loadTranslations() {
        try {
            // Load translations from backend
            const response = await fetch(`/api/translations/${this.currentLanguage}/`);
            if (response.ok) {
                this.translations = await response.json();
            }
        } catch (error) {
            console.warn('Failed to load translations:', error);
        }
    }
    
    setupNumberFormats() {
        this.numberFormats = {
            'az': {
                decimal: ',',
                thousands: ' ',
                currency: '₼',
                currencyPosition: 'after'
            },
            'en': {
                decimal: '.',
                thousands: ',',
                currency: '$',
                currencyPosition: 'before'
            },
            'tr': {
                decimal: ',',
                thousands: '.',
                currency: '₺',
                currencyPosition: 'after'
            },
            'ru': {
                decimal: ',',
                thousands: ' ',
                currency: '₽',
                currencyPosition: 'after'
            }
        };
    }
    
    setupDateFormats() {
        this.dateFormats = {
            'az': {
                short: 'dd.MM.yyyy',
                long: 'dd MMMM yyyy',
                time: 'HH:mm',
                datetime: 'dd.MM.yyyy HH:mm'
            },
            'en': {
                short: 'MM/dd/yyyy',
                long: 'MMMM dd, yyyy',
                time: 'h:mm a',
                datetime: 'MM/dd/yyyy h:mm a'
            },
            'tr': {
                short: 'dd.MM.yyyy',
                long: 'dd MMMM yyyy',
                time: 'HH:mm',
                datetime: 'dd.MM.yyyy HH:mm'
            },
            'ru': {
                short: 'dd.MM.yyyy',
                long: 'dd MMMM yyyy',
                time: 'HH:mm',
                datetime: 'dd.MM.yyyy HH:mm'
            }
        };
    }
    
    setupEventListeners() {
        // Listen for language changes
        document.addEventListener('languageChanged', (event) => {
            this.currentLanguage = event.detail.language;
            this.isRTL = event.detail.isRTL;
            this.loadTranslations();
            this.updatePageDirection();
        });
    }
    
    updatePageDirection() {
        document.documentElement.dir = this.isRTL ? 'rtl' : 'ltr';
        document.documentElement.lang = this.currentLanguage;
        
        // Trigger custom event for components that need to adjust
        document.dispatchEvent(new CustomEvent('directionChanged', {
            detail: { isRTL: this.isRTL, language: this.currentLanguage }
        }));
    }
    
    // Translation methods
    translate(key, params = {}) {
        let translation = this.translations[key] || key;
        
        // Simple parameter substitution
        Object.keys(params).forEach(param => {
            translation = translation.replace(`{${param}}`, params[param]);
        });
        
        return translation;
    }
    
    // Alias for shorter syntax
    t(key, params = {}) {
        return this.translate(key, params);
    }
    
    // Number formatting
    formatNumber(number, options = {}) {
        const format = this.numberFormats[this.currentLanguage] || this.numberFormats['az'];
        const {
            decimals = 0,
            useGrouping = true
        } = options;
        
        try {
            const formatter = new Intl.NumberFormat(this.currentLanguage, {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals,
                useGrouping: useGrouping
            });
            
            return formatter.format(number);
        } catch (error) {
            // Fallback formatting
            return this.fallbackNumberFormat(number, format, decimals, useGrouping);
        }
    }
    
    fallbackNumberFormat(number, format, decimals, useGrouping) {
        let result = parseFloat(number).toFixed(decimals);
        
        // Replace decimal separator
        result = result.replace('.', format.decimal);
        
        // Add thousands separator
        if (useGrouping) {
            const parts = result.split(format.decimal);
            parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, format.thousands);
            result = parts.join(format.decimal);
        }
        
        return result;
    }
    
    formatCurrency(amount, currency = null) {
        const format = this.numberFormats[this.currentLanguage] || this.numberFormats['az'];
        const currencySymbol = currency || format.currency;
        const formattedAmount = this.formatNumber(amount, { decimals: 2 });
        
        if (format.currencyPosition === 'before') {
            return `${currencySymbol} ${formattedAmount}`;
        } else {
            return `${formattedAmount} ${currencySymbol}`;
        }
    }
    
    formatPercentage(number, decimals = 1) {
        const formatted = this.formatNumber(number, { decimals });
        return `${formatted}%`;
    }
    
    // Date formatting
    formatDate(date, format = 'short') {
        if (!date) return '';
        
        const dateObj = date instanceof Date ? date : new Date(date);
        const formatPattern = this.dateFormats[this.currentLanguage]?.[format] || 
                             this.dateFormats['az'][format];
        
        try {
            const formatter = new Intl.DateTimeFormat(this.currentLanguage, 
                this.getIntlDateOptions(format));
            return formatter.format(dateObj);
        } catch (error) {
            // Fallback to basic formatting
            return dateObj.toLocaleDateString(this.currentLanguage);
        }
    }
    
    getIntlDateOptions(format) {
        const options = {
            'short': {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            },
            'long': {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            },
            'time': {
                hour: '2-digit',
                minute: '2-digit'
            },
            'datetime': {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            }
        };
        
        return options[format] || options['short'];
    }
    
    formatRelativeTime(date) {
        if (!date) return '';
        
        const dateObj = date instanceof Date ? date : new Date(date);
        const now = new Date();
        const diffInSeconds = Math.floor((now - dateObj) / 1000);
        
        const intervals = {
            year: 31536000,
            month: 2592000,
            week: 604800,
            day: 86400,
            hour: 3600,
            minute: 60
        };
        
        for (const [unit, seconds] of Object.entries(intervals)) {
            const interval = Math.floor(diffInSeconds / seconds);
            if (interval >= 1) {
                return this.translate(`time.${unit}s_ago`, { count: interval });
            }
        }
        
        return this.translate('time.just_now');
    }
    
    // Pluralization
    pluralize(count, key) {
        // Simple pluralization rules
        const rules = {
            'az': (n) => n === 1 ? 'one' : 'other',
            'en': (n) => n === 1 ? 'one' : 'other',
            'tr': (n) => n === 1 ? 'one' : 'other',
            'ru': (n) => {
                if (n % 10 === 1 && n % 100 !== 11) return 'one';
                if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) return 'few';
                return 'many';
            }
        };
        
        const rule = rules[this.currentLanguage] || rules['az'];
        const form = rule(count);
        const translationKey = `${key}.${form}`;
        
        return this.translate(translationKey, { count });
    }
    
    // Utility methods
    getCurrentLanguage() {
        return this.currentLanguage;
    }
    
    isRightToLeft() {
        return this.isRTL;
    }
    
    getTextDirection() {
        return this.isRTL ? 'rtl' : 'ltr';
    }
    
    // Language switching
    async switchLanguage(langCode) {
        if (langCode === this.currentLanguage) return;
        
        // Update URL
        const currentPath = window.location.pathname;
        const newPath = currentPath.replace(`/${this.currentLanguage}/`, `/${langCode}/`);
        
        // Dispatch event before changing
        document.dispatchEvent(new CustomEvent('languageChanging', {
            detail: { from: this.currentLanguage, to: langCode }
        }));
        
        // Navigate to new language URL
        window.location.href = newPath;
    }
}

// Global instance
window.i18n = new I18nManager();

// Convenience functions
window.t = (key, params) => window.i18n.translate(key, params);
window.formatNumber = (number, options) => window.i18n.formatNumber(number, options);
window.formatCurrency = (amount, currency) => window.i18n.formatCurrency(amount, currency);
window.formatDate = (date, format) => window.i18n.formatDate(date, format);

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = I18nManager;
}