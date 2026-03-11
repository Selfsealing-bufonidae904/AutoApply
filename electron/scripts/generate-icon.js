/**
 * generate-icon.js — Generate placeholder app icons for all platforms.
 * Creates a 1024x1024 PNG with "AA" text, then converts to ICO and ICNS.
 *
 * Prerequisites: npm install --save-dev canvas png2icons
 * Usage: node electron/scripts/generate-icon.js
 */

const fs = require('fs');
const path = require('path');

const iconsDir = path.join(__dirname, '..', 'icons');

async function generatePng() {
  let createCanvas;
  try {
    ({ createCanvas } = require('canvas'));
  } catch {
    console.error('Missing dependency: npm install --save-dev canvas');
    process.exit(1);
  }

  const size = 1024;
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // Background — dark blue rounded rectangle
  const radius = 180;
  ctx.fillStyle = '#1a1a2e';
  ctx.beginPath();
  ctx.moveTo(radius, 0);
  ctx.lineTo(size - radius, 0);
  ctx.quadraticCurveTo(size, 0, size, radius);
  ctx.lineTo(size, size - radius);
  ctx.quadraticCurveTo(size, size, size - radius, size);
  ctx.lineTo(radius, size);
  ctx.quadraticCurveTo(0, size, 0, size - radius);
  ctx.lineTo(0, radius);
  ctx.quadraticCurveTo(0, 0, radius, 0);
  ctx.closePath();
  ctx.fill();

  // Border
  ctx.strokeStyle = '#16213e';
  ctx.lineWidth = 8;
  ctx.stroke();

  // "AA" text
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 420px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('AA', size / 2, size / 2 + 20);

  // Subtle accent line at bottom
  ctx.fillStyle = '#4f46e5';
  ctx.fillRect(size * 0.15, size * 0.85, size * 0.7, 12);

  const buffer = canvas.toBuffer('image/png');
  const pngPath = path.join(iconsDir, 'icon.png');
  fs.writeFileSync(pngPath, buffer);
  console.log(`Created: ${pngPath} (${buffer.length} bytes)`);
  return buffer;
}

async function convertToIcoIcns(pngBuffer) {
  let png2icons;
  try {
    png2icons = require('png2icons');
  } catch {
    console.error('Missing dependency: npm install --save-dev png2icons');
    process.exit(1);
  }

  // ICO (Windows)
  const icoBuffer = png2icons.createICO(pngBuffer, png2icons.BILINEAR, 0, true, true);
  if (icoBuffer) {
    const icoPath = path.join(iconsDir, 'icon.ico');
    fs.writeFileSync(icoPath, icoBuffer);
    console.log(`Created: ${icoPath} (${icoBuffer.length} bytes)`);
  } else {
    console.error('Failed to create ICO');
    process.exit(1);
  }

  // ICNS (macOS)
  const icnsBuffer = png2icons.createICNS(pngBuffer, png2icons.BILINEAR, 0);
  if (icnsBuffer) {
    const icnsPath = path.join(iconsDir, 'icon.icns');
    fs.writeFileSync(icnsPath, icnsBuffer);
    console.log(`Created: ${icnsPath} (${icnsBuffer.length} bytes)`);
  } else {
    console.error('Failed to create ICNS');
    process.exit(1);
  }
}

async function main() {
  if (!fs.existsSync(iconsDir)) {
    fs.mkdirSync(iconsDir, { recursive: true });
  }

  const pngBuffer = await generatePng();
  await convertToIcoIcns(pngBuffer);
  console.log('All icons generated successfully.');
}

main().catch((err) => {
  console.error('Icon generation failed:', err.message);
  process.exit(1);
});
