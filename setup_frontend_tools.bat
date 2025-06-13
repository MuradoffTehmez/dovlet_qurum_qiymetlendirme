@echo off
echo 🚀 Layihə üçün npm başlatılır...
call npm init -y

echo 📦 Lazımi dev paketlər quraşdırılır...
call npm install --save-dev prettier eslint stylelint stylelint-config-standard

echo 📝 Prettier konfiqurasiya faylı yaradılır...
echo module.exports = {> prettier.config.js
echo.  semi: true,>> prettier.config.js
echo.  singleQuote: true,>> prettier.config.js
echo.  printWidth: 100,>> prettier.config.js
echo.  tabWidth: 2,>> prettier.config.js
echo.  trailingComma: 'es5',>> prettier.config.js
echo.  bracketSpacing: true,>> prettier.config.js
echo.  htmlWhitespaceSensitivity: 'ignore',>> prettier.config.js
echo };>> prettier.config.js

echo 📝 Stylelint konfiqurasiya faylı yaradılır...
echo {> .stylelintrc.json
echo   "extends": "stylelint-config-standard",>> .stylelintrc.json
echo   "rules": {>> .stylelintrc.json
echo     "indentation": 2,>> .stylelintrc.json
echo     "string-quotes": "single">> .stylelintrc.json
echo   }>> .stylelintrc.json
echo }>> .stylelintrc.json

echo 📝 ESLint konfiqurasiya faylı yaradılır...
echo {> .eslintrc.json
echo   "env": {>> .eslintrc.json
echo     "browser": true,>> .eslintrc.json
echo     "es2021": true>> .eslintrc.json
echo   },>> .eslintrc.json
echo   "extends": "eslint:recommended",>> .eslintrc.json
echo   "parserOptions": {>> .eslintrc.json
echo     "ecmaVersion": "latest">> .eslintrc.json
echo   },>> .eslintrc.json
echo   "rules": {>> .eslintrc.json
echo     "semi": ["error", "always"],>> .eslintrc.json
echo     "quotes": ["error", "single"]>> .eslintrc.json
echo   }>> .eslintrc.json
echo }>> .eslintrc.json

echo 📄 .prettierignore faylı yaradılır...
echo node_modules> .prettierignore
echo static/vendor/>> .prettierignore

echo ⚙️ package.json daxilində scriptləri əl ilə əlavə etməyiniz lazımdır!
echo JSON CLI olmadığı üçün avtomatik əlavə edilə bilmir.
echo ---------------------------------------------
echo  "scripts": {
echo    "format": "prettier --write .",
echo    "lint:css": "stylelint \"**/*.css\"",
echo    "lint:js": "eslint . --ext .js",
echo    "check": "npm run lint:css && npm run lint:js"
echo  }
echo ---------------------------------------------
echo Bu scriptləri manual olaraq package.json-a əlavə edin.
echo ✅ Hazırdır! İndi istifadə edə bilərsiniz:

echo.
echo 🔹 Kodları formatlamaq üçün:
echo     npm run format
echo 🔹 CSS və JS kodlarını yoxlamaq üçün:
echo     npm run check
