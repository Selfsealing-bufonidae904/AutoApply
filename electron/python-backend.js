const { app } = require('electron');
const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');
const net = require('net');

let backendProcess = null;
let backendPort = 5000;
let logStream = null;

/**
 * Find the Python executable. Checks for a local venv first, then system Python.
 * @returns {string|null} Path to Python or null if not found.
 */
function findPython() {
  const isPackaged = app && typeof app.isPackaged !== 'undefined' ? app.isPackaged : false;

  // Priority 1: Bundled Python runtime (packaged mode)
  if (isPackaged) {
    const bundledCandidates = process.platform === 'win32'
      ? [path.join(process.resourcesPath, 'python-runtime', 'python.exe')]
      : [
          path.join(process.resourcesPath, 'python-runtime', 'bin', 'python3'),
          path.join(process.resourcesPath, 'python-runtime', 'bin', 'python'),
        ];
    for (const p of bundledCandidates) {
      if (fs.existsSync(p)) return p;
    }
    console.warn('Bundled Python runtime not found, falling back to venv/system Python');
  }

  // Priority 2: Local virtual environment (dev mode)
  const projectRoot = isPackaged
    ? path.join(process.resourcesPath, 'python-backend')
    : path.join(__dirname, '..');

  const venvCandidates = process.platform === 'win32'
    ? [
        path.join(projectRoot, 'venv', 'Scripts', 'python.exe'),
        path.join(projectRoot, '.venv', 'Scripts', 'python.exe'),
      ]
    : [
        path.join(projectRoot, 'venv', 'bin', 'python3'),
        path.join(projectRoot, 'venv', 'bin', 'python'),
        path.join(projectRoot, '.venv', 'bin', 'python3'),
        path.join(projectRoot, '.venv', 'bin', 'python'),
      ];

  for (const venvPath of venvCandidates) {
    if (fs.existsSync(venvPath)) {
      return venvPath;
    }
  }

  // Fall back to system Python
  const systemCandidates = process.platform === 'win32'
    ? ['python', 'python3', 'py']
    : ['python3', 'python'];

  for (const cmd of systemCandidates) {
    try {
      const version = execSync(`${cmd} --version`, { encoding: 'utf-8', timeout: 5000 });
      if (version.includes('3.')) {
        return cmd;
      }
    } catch {
      // Not found, try next
    }
  }
  return null;
}

/**
 * Get the path to the run.py script.
 * In dev mode: ../run.py relative to electron/
 * In packaged mode: inside app resources
 */
function getScriptPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'python-backend', 'run.py');
  }
  return path.join(__dirname, '..', 'run.py');
}

/**
 * Get the Electron Chromium executable path for Playwright to reuse.
 * @returns {string|null} Path to Chromium binary or null.
 */
function getElectronChromiumPath() {
  // In dev mode, Electron's Chromium is at node_modules/electron/dist/
  const electronPath = process.platform === 'win32'
    ? path.join(__dirname, 'node_modules', 'electron', 'dist', 'electron.exe')
    : process.platform === 'darwin'
      ? path.join(__dirname, 'node_modules', 'electron', 'dist', 'Electron.app', 'Contents', 'MacOS', 'Electron')
      : path.join(__dirname, 'node_modules', 'electron', 'dist', 'electron');

  if (fs.existsSync(electronPath)) {
    return electronPath;
  }

  // In packaged mode, the Electron binary is the app itself — not usable for Playwright.
  // Fall back to Playwright's own Chromium.
  return null;
}

/**
 * Get the data directory path for log files.
 * @returns {string}
 */
function getDataDir() {
  return path.join(app.getPath('home'), '.autoapply');
}

/**
 * Set up log file for backend output.
 * Rotates if existing log exceeds 10MB.
 */
function setupLogFile() {
  const dataDir = getDataDir();
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  const logPath = path.join(dataDir, 'backend.log');
  const rotatedPath = path.join(dataDir, 'backend.log.1');

  try {
    if (fs.existsSync(logPath)) {
      const stats = fs.statSync(logPath);
      if (stats.size > 10 * 1024 * 1024) {
        if (fs.existsSync(rotatedPath)) {
          fs.unlinkSync(rotatedPath);
        }
        fs.renameSync(logPath, rotatedPath);
      }
    }
  } catch {
    // Ignore rotation errors
  }

  logStream = fs.createWriteStream(logPath, { flags: 'a' });
  return logStream;
}

/**
 * Check if a port is available.
 * @param {number} port
 * @returns {Promise<boolean>}
 */
function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.once('listening', () => {
      server.close();
      resolve(true);
    });
    server.listen(port, '127.0.0.1');
  });
}

/**
 * Find an available port starting from the given port.
 * @param {number} startPort
 * @returns {Promise<number>}
 */
async function findAvailablePort(startPort = 5000) {
  for (let port = startPort; port <= startPort + 10; port++) {
    if (await isPortAvailable(port)) {
      return port;
    }
  }
  throw new Error(`No available port found in range ${startPort}-${startPort + 10}`);
}

/**
 * Poll the health endpoint until it responds 200.
 * @param {number} port
 * @param {number} intervalMs
 * @param {number} timeoutMs
 * @returns {Promise<void>}
 */
function waitForHealth(port, intervalMs = 500, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    const check = () => {
      if (Date.now() - startTime > timeoutMs) {
        reject(new Error(`Backend did not start within ${timeoutMs / 1000}s`));
        return;
      }

      const req = http.get(`http://127.0.0.1:${port}/api/health`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          setTimeout(check, intervalMs);
        }
      });

      req.on('error', () => {
        setTimeout(check, intervalMs);
      });

      req.setTimeout(2000, () => {
        req.destroy();
        setTimeout(check, intervalMs);
      });
    };

    check();
  });
}

/**
 * Start the Python backend.
 * @param {object} options
 * @param {string} [options.pythonPath] - Override Python executable path
 * @param {number} [options.port] - Override starting port
 * @returns {Promise<{port: number, process: object}>}
 */
async function startBackend(options = {}) {
  const pythonCmd = options.pythonPath || findPython();
  if (!pythonCmd) {
    throw new Error('Python 3.11+ is required but was not found. Please install Python from python.org.');
  }

  const scriptPath = getScriptPath();
  if (!fs.existsSync(scriptPath)) {
    throw new Error(`Backend script not found at: ${scriptPath}`);
  }

  backendPort = await findAvailablePort(options.port || 5000);
  setupLogFile();

  const env = { ...process.env };
  env.AUTOAPPLY_PORT = String(backendPort);

  const isPackaged = app && typeof app.isPackaged !== 'undefined' ? app.isPackaged : false;

  if (isPackaged) {
    // Set paths for bundled Python runtime
    env.PLAYWRIGHT_BROWSERS_PATH = path.join(
      process.resourcesPath, 'python-runtime', 'playwright-browsers'
    );
    env.PYTHONPATH = path.join(process.resourcesPath, 'python-backend');
  } else {
    // Dev mode: share Electron's Chromium with Playwright
    const chromiumPath = getElectronChromiumPath();
    if (chromiumPath) {
      env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH = chromiumPath;
    }
  }

  const cwd = app.isPackaged
    ? path.join(process.resourcesPath, 'python-backend')
    : path.join(__dirname, '..');

  backendProcess = spawn(pythonCmd, [scriptPath], {
    cwd,
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });

  if (logStream) {
    backendProcess.stdout.pipe(logStream);
    backendProcess.stderr.pipe(logStream);
  }

  backendProcess.on('error', (err) => {
    console.error('Failed to start Python backend:', err.message);
  });

  backendProcess.on('exit', (code, sig) => {
    console.log(`Python backend exited (code=${code}, signal=${sig})`);
    backendProcess = null;
  });

  await waitForHealth(backendPort);
  return { port: backendPort, process: backendProcess };
}

/**
 * Stop the Python backend gracefully, with force-kill fallback.
 * @returns {Promise<void>}
 */
async function stopBackend() {
  if (!backendProcess) return;

  // Try graceful shutdown via API
  try {
    await new Promise((resolve, reject) => {
      const postData = '';
      const req = http.request(
        {
          hostname: '127.0.0.1',
          port: backendPort,
          path: '/api/shutdown',
          method: 'POST',
          headers: { 'Content-Length': 0 },
          timeout: 3000,
        },
        (res) => resolve(res.statusCode)
      );
      req.on('error', () => resolve(null));
      req.on('timeout', () => { req.destroy(); resolve(null); });
      req.end(postData);
    });
  } catch {
    // Ignore — will force kill below
  }

  // Wait up to 5 seconds for graceful exit
  const exited = await new Promise((resolve) => {
    if (!backendProcess) { resolve(true); return; }

    const timeout = setTimeout(() => resolve(false), 5000);
    backendProcess.once('exit', () => {
      clearTimeout(timeout);
      resolve(true);
    });
  });

  // Force kill if still running
  if (!exited && backendProcess) {
    try {
      if (process.platform === 'win32') {
        execSync(`taskkill /PID ${backendProcess.pid} /T /F`, { timeout: 5000 });
      } else {
        backendProcess.kill('SIGKILL');
      }
    } catch {
      // Process may have already exited
    }
  }

  backendProcess = null;

  if (logStream) {
    logStream.end();
    logStream = null;
  }
}

/**
 * Get the port the backend is running on.
 * @returns {number}
 */
function getPort() {
  return backendPort;
}

module.exports = { startBackend, stopBackend, getPort, findPython };
