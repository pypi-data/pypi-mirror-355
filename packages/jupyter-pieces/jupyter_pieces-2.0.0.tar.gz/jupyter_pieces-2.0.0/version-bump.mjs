import { readFileSync, writeFileSync } from 'fs';

const targetVersion = process.env.npm_package_version;

// read plugin version from constants and replace it with the target version
let constants = readFileSync('src/const.ts', 'utf8')
constants = constants.replace(/(public static PLUGIN_VERSION = ')(.*)(')/, `$1${targetVersion}$3`);
writeFileSync('src/const.ts', constants);