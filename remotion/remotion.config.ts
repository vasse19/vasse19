// See all configuration options: https://remotion.dev/docs/config
// Each option also is available as a CLI flag: https://remotion.dev/docs/cli

// Note: When using the Node.JS APIs, the config file doesn't apply. Instead, pass options directly to the APIs

import { Config } from "@remotion/cli/config";
import fs from "node:fs";

Config.setRspack(true);
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// Cloud sandbox: remotion.media (Remotion's browser download) is blocked, so reuse the
// Chrome Headless Shell preinstalled in the image when it exists. Elsewhere Remotion downloads its own.
const preinstalledShell =
  "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
if (fs.existsSync(preinstalledShell)) {
  Config.setBrowserExecutable(preinstalledShell);
}
