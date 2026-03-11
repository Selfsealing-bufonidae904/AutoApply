/**
 * sync-version.js — Read version from pyproject.toml and update package.json.
 * Ensures the Electron app version matches the Python backend version.
 *
 * Usage: node electron/scripts/sync-version.js
 */

const fs = require('fs');
const path = require('path');

const pyprojectPath = path.join(__dirname, '..', '..', 'pyproject.toml');
const packagePath = path.join(__dirname, '..', 'package.json');

// Read pyproject.toml and extract version
let pyproject;
try {
  pyproject = fs.readFileSync(pyprojectPath, 'utf-8');
} catch (err) {
  console.error(`Failed to read ${pyprojectPath}: ${err.message}`);
  process.exit(1);
}

const match = pyproject.match(/^version\s*=\s*"([^"]+)"/m);
if (!match) {
  console.error('Could not find version field in pyproject.toml');
  process.exit(1);
}

const version = match[1];

// Read and update package.json
let pkg;
try {
  pkg = JSON.parse(fs.readFileSync(packagePath, 'utf-8'));
} catch (err) {
  console.error(`Failed to read ${packagePath}: ${err.message}`);
  process.exit(1);
}

if (pkg.version === version) {
  console.log(`Version already synced: ${version}`);
  process.exit(0);
}

const oldVersion = pkg.version;
pkg.version = version;
fs.writeFileSync(packagePath, JSON.stringify(pkg, null, 2) + '\n', 'utf-8');
console.log(`Synced version: ${oldVersion} → ${version}`);
