import markdownIt from "markdown-it";
import { init } from "@github/markdownlint-github";

const markdownItFactory = () => markdownIt({ html: true });

const options = {
  gitignore: true,
  globs: ["**/*.{md,mdx}"],
  ignores: [".agents/**", ".github/**", "COMMUNITY.md"],
  config: init({
    "line-length": false,
  }),
  customRules: ["@github/markdownlint-github"],
  markdownItFactory,
  outputFormatters: [
    ["markdownlint-cli2-formatter-pretty", { appendLink: true }],
  ],
};

export default options;
