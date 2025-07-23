#!/usr/bin/env node
/**
 * Build script for internationalization assets
 * Processes translation files and creates optimized bundles
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');
const yaml = require('js-yaml');

const LOCALE_DIR = path.join(__dirname, '..', 'locale');
const OUTPUT_DIR = path.join(__dirname, '..', 'static', 'js', 'i18n');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Supported languages
const LANGUAGES = ['az', 'en', 'tr', 'ru'];

console.log('🌍 Building i18n assets...');

// Process each language
LANGUAGES.forEach(lang => {
    console.log(`📝 Processing ${lang}...`);
    
    const poFile = path.join(LOCALE_DIR, lang, 'LC_MESSAGES', 'django.po');
    const outputFile = path.join(OUTPUT_DIR, `${lang}.json`);
    
    if (fs.existsSync(poFile)) {
        const translations = parsePOFile(poFile);
        
        // Write JSON file
        fs.writeFileSync(outputFile, JSON.stringify(translations, null, 2));
        console.log(`✅ Created ${outputFile}`);
    } else {
        console.log(`⚠️  PO file not found for ${lang}`);
    }
});

// Create language metadata
const metadata = {
    languages: LANGUAGES.map(lang => ({
        code: lang,
        name: getLanguageName(lang),
        direction: isRTL(lang) ? 'rtl' : 'ltr',
        isRTL: isRTL(lang)
    })),
    defaultLanguage: 'az',
    fallbackLanguage: 'en'
};

fs.writeFileSync(
    path.join(OUTPUT_DIR, 'metadata.json'),
    JSON.stringify(metadata, null, 2)
);

console.log('🎉 i18n build completed!');

function parsePOFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf-8');
    const translations = {};
    
    const lines = content.split('\n');
    let currentMsgid = null;
    let currentMsgstr = null;
    let inMultiline = false;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        if (line.startsWith('msgid ')) {
            currentMsgid = extractQuotedString(line.substring(6));
            inMultiline = false;
        } else if (line.startsWith('msgstr ')) {
            currentMsgstr = extractQuotedString(line.substring(7));
            inMultiline = false;
            
            // Store translation if both msgid and msgstr exist
            if (currentMsgid && currentMsgstr) {
                translations[currentMsgid] = currentMsgstr;
            }
        } else if (line.startsWith('"') && inMultiline) {
            // Handle multiline strings
            const additionalText = extractQuotedString(line);
            if (currentMsgstr !== null) {
                currentMsgstr += additionalText;
            } else if (currentMsgid !== null) {
                currentMsgid += additionalText;
            }
        }
        
        // Check if we're starting a multiline string
        if ((line.startsWith('msgid ') || line.startsWith('msgstr ')) && 
            line.endsWith('""')) {
            inMultiline = true;
        }
    }
    
    return translations;
}

function extractQuotedString(str) {
    // Remove surrounding quotes and handle escaped characters
    if (str.startsWith('"') && str.endsWith('"')) {
        return str.slice(1, -1)
            .replace(/\\"/g, '"')
            .replace(/\\n/g, '\n')
            .replace(/\\t/g, '\t')
            .replace(/\\\\/g, '\\');
    }
    return str;
}

function getLanguageName(langCode) {
    const names = {
        'az': 'Azərbaycan',
        'en': 'English',
        'tr': 'Türkçe',
        'ru': 'Русский'
    };
    return names[langCode] || langCode;
}

function isRTL(langCode) {
    const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
    return rtlLanguages.includes(langCode);
}