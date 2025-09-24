import stylistic from '@stylistic/eslint-plugin';
import tseslint from 'typescript-eslint';

export default [
  {
    ignores: [
      "*.yaml",
      "*.yml",
      "**/coverage",
      "**/*.config.js",
      "**/*.config.ts",
    ],
  },
  {
    plugins: {
      '@stylistic': stylistic,
    },
    files: ['./frontend/**/*.{js,ts,jsx,tsx}'],
    rules: {
      '@stylistic/quotes': ['error', 'single', { avoidEscape: true }],
      '@stylistic/max-len': ['error', 100],
      '@stylistic/semi': ['error', 'always'],
    },
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
];
