import { copyFile } from 'node:fs/promises';
await copyFile('src/tokens.css', 'public/theme.css');
