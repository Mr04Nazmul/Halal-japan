# ChatGPT-adjacent free LLM batch runner

Source directory: https://github.com/open-free-llm-api/awesome-freellm-apis

This tool is a command-line integration, NOT a ChatGPT model replacement or an installed ChatGPT plugin.

## Usage

1. Create a free-tier API key with a provider (Groq or OpenRouter).
2. Store it privately as GROQ_API_KEY or OPENROUTER_API_KEY, preferably in GitHub Actions secrets.
3. Prepare a JSON array of 20 or more prompt strings.
4. Run: `python tools/free_llm_batch.py --provider groq --input tools/llm_prompts_example.json --output llm-results.json --workers 3`
5. Review the generated JSON file. Concurrency is capped to 5 and provider quotas still apply.

Never put API keys in GitHub source, prompt files, or chat messages.
