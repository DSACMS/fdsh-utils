#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "..");
const disclaimerPath = path.join(repositoryRoot, "DISCLAIMER.md");
const expectedText =
  "Disclaimer: This project is not official FDSH documentation or part of the official FDSH product; see";

if (!existsSync(disclaimerPath)) {
  console.error("Missing root DISCLAIMER.md file.");
  process.exit(1);
}

const toPosixPath = (filePath) => filePath.split(path.sep).join("/");

const getGitFiles = () => {
  try {
    const output = execFileSync(
      "git",
      [
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "--",
        "README.md",
        "**/README.md",
      ],
      {
        cwd: repositoryRoot,
        encoding: "utf8",
        stdio: ["ignore", "pipe", "ignore"],
      },
    );

    return output
      .split("\n")
      .map((filePath) => filePath.trim())
      .filter(Boolean);
  } catch {
    return null;
  }
};

const getReadmeFilesFromDirectory = (directory) => {
  const ignoredDirectories = new Set([".git", "node_modules"]);
  const files = [];

  for (const entry of readdirSync(directory)) {
    const entryPath = path.join(directory, entry);
    const relativeEntryPath = path.relative(repositoryRoot, entryPath);
    const stats = statSync(entryPath);

    if (stats.isDirectory()) {
      if (!ignoredDirectories.has(entry)) {
        files.push(...getReadmeFilesFromDirectory(entryPath));
      }
      continue;
    }

    if (entry === "README.md") {
      files.push(toPosixPath(relativeEntryPath));
    }
  }

  return files;
};

const readmeFiles = [
  ...new Set(getGitFiles() ?? getReadmeFilesFromDirectory(repositoryRoot)),
].sort();

const failures = [];

for (const readmeFile of readmeFiles) {
  const readmePath = path.join(repositoryRoot, readmeFile);
  const readmeDirectory = path.dirname(readmePath);
  const disclaimerLink = toPosixPath(
    path.relative(readmeDirectory, disclaimerPath) || "DISCLAIMER.md",
  );
  const expectedDisclaimer = `**${expectedText} [DISCLAIMER.md](${disclaimerLink}).**`;
  const contents = readFileSync(readmePath, "utf8").replaceAll("\r\n", "\n");
  const topNonEmptyLines = contents
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 3);

  if (!topNonEmptyLines.includes(expectedDisclaimer)) {
    failures.push({ expectedDisclaimer, readmeFile });
  }
}

if (failures.length > 0) {
  console.error(
    "README disclaimer check failed. Each README.md must include the expected disclaimer in its first three non-empty lines.\n",
  );

  for (const failure of failures) {
    console.error(`- ${failure.readmeFile}`);
    console.error(`  Expected: ${failure.expectedDisclaimer}`);
  }

  process.exit(1);
}

console.log(
  `README disclaimer check passed for ${readmeFiles.length} file(s).`,
);
