import {createHash} from "node:crypto";
import {cp, mkdir, readFile, readdir, rm, writeFile} from "node:fs/promises";
import {dirname, resolve} from "node:path";
import {fileURLToPath} from "node:url";

const dashboardRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const dataDir = resolve(dashboardRoot, "src", "data");
const previewDir = resolve(dashboardRoot, "preview-data");
const backupDir = resolve(dashboardRoot, ".preview-data-backup");
const backupDataDir = resolve(backupDir, "data");
const metadataPath = resolve(backupDir, "metadata.json");
const expectedFiles = [
  "conditions.json",
  "forecast-history.json",
  "locations.json",
  "manifest.json",
  "pipeline-runs.json",
  "provenance.json",
  "source-health.json"
];

const sha256 = (buffer) => createHash("sha256").update(buffer).digest("hex");

async function previewMetadata() {
  const previewEntries = await directoryEntries(previewDir);
  const expected = [...expectedFiles].sort();
  if (JSON.stringify(previewEntries) !== JSON.stringify(expected)) {
    throw new Error(
      "Representative preview data must contain exactly the expected dashboard JSON files."
    );
  }

  const hashes = {};
  for (const name of expectedFiles) {
    const content = await readFile(resolve(previewDir, name));
    JSON.parse(content.toString("utf8"));
    hashes[name] = sha256(content);
  }
  return {files: expectedFiles, preview_sha256: hashes};
}

async function directoryEntries(path) {
  return (await readdir(path, {withFileTypes: true}))
    .map((entry) => entry.name)
    .sort();
}

async function applyPreview() {
  try {
    await readFile(metadataPath);
    throw new Error(
      "Representative preview data is already active. Restore it before applying again."
    );
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }

  const metadata = await previewMetadata();
  await mkdir(backupDir, {recursive: false});

  try {
    await cp(dataDir, backupDataDir, {recursive: true});
    await writeFile(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`, "utf8");
    await rm(dataDir, {recursive: true, force: true});
    await cp(previewDir, dataDir, {recursive: true});
  } catch (error) {
    try {
      await rm(dataDir, {recursive: true, force: true});
      await cp(backupDataDir, dataDir, {recursive: true});
    } finally {
      await rm(backupDir, {recursive: true, force: true});
    }
    throw error;
  }

  console.log("dashboard_preview_data=applied");
}

async function restorePreview() {
  let metadata;
  try {
    metadata = JSON.parse(await readFile(metadataPath, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") {
      throw new Error("Representative preview data is not active.");
    }
    throw error;
  }

  const currentFiles = await directoryEntries(dataDir);
  const expected = [...metadata.files].sort();
  if (JSON.stringify(currentFiles) !== JSON.stringify(expected)) {
    throw new Error(
      "Dashboard data changed while representative preview data was active. Refusing to restore over those changes."
    );
  }

  for (const name of metadata.files) {
    const current = await readFile(resolve(dataDir, name));
    if (sha256(current) !== metadata.preview_sha256[name]) {
      throw new Error(
        `Dashboard data changed while representative preview data was active: ${name}. Refusing to overwrite it.`
      );
    }
  }

  await rm(dataDir, {recursive: true, force: true});
  await cp(backupDataDir, dataDir, {recursive: true});
  await rm(backupDir, {recursive: true, force: true});
  console.log("dashboard_preview_data=restored");
}

const command = process.argv[2];
if (command === "apply") {
  await applyPreview();
} else if (command === "restore") {
  await restorePreview();
} else {
  throw new Error("Usage: node scripts/preview-data.mjs <apply|restore>");
}
