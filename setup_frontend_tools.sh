#!/bin/bash

echo "🚀 NPM başlatılır..."
npm init -y

echo "📦 Lazımi paketlər quraşdırılır (prettier, eslint, stylelint)..."
npm install --save-dev prettier eslint stylelint stylelint-config-standard

echo "📝 Prettier konfiqurasiyası yaradılır..."
cat <<EOF > prettier.config.js
module.exports = {
  semi: true,
  singleQuote: true,
  printWidth: 100,
  tabWidth: 2,
  trailingComma: 'es5',
  bracketSpacing: true,
  htmlWhitespaceSensitivity: 'ignore',
};
EOF

echo "📝 Stylelint konfiqurasiyası yaradılır..."
cat <<EOF > .stylelintrc.json
{
  "extends": "stylelint-config-standard",
  "rules": {
    "indentation": 2,
    "string-quotes": "single"
  }
}
EOF

echo "📝 ESLint konfiqurasiyası yaradılır..."
cat <<EOF > .eslintrc.json
{
  "env": {
    "browser": true,
    "es2021": true
  },
  "extends": "eslint:recommended",
  "parserOptions": {
    "ecmaVersion": "latest"
  },
  "rules": {
    "semi": ["error", "always"],
    "quotes": ["error", "single"]
  }
}
EOF

echo "📄 Prettier ignore faylı yaradılır..."
cat <<EOF > .prettierignore
node_modules
static/vendor/
EOF

echo "📄 package.json scriptləri əlavə olunur..."
npx json -I -f package.json -e '
this.scripts = {
  "format": "prettier --write .",
  "lint:css": "stylelint \\"**/*.css\\"",
  "lint:js": "eslint . --ext .js",
  "check": "npm run lint:css && npm run lint:js"
}
'

echo "✅ Qurulum tamamlandı. İndi istifadə edə bilərsiniz:

🔹 Kodları formatlamaq üçün:
   npm run format

🔹 CSS və JS kodlarını yoxlamaq üçün:
   npm run check
"
