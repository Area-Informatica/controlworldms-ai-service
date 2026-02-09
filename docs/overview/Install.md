> ## Documentation Index
> Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Install LangChain

To install the LangChain package:

<CodeGroup>
  ```bash pip theme={null}
  pip install -U langchain
  # Requires Python 3.10+
  ```

  ```bash uv theme={null}
  uv add langchain
  # Requires Python 3.10+
  ```
</CodeGroup>

LangChain provides integrations to hundreds of LLMs and thousands of other integrations. These live in independent provider packages.

<CodeGroup>
  ```bash pip theme={null}
  # Installing the OpenAI integration
  pip install -U langchain-openai

  # Installing the Anthropic integration
  pip install -U langchain-anthropic
  ```

  ```bash uv theme={null}
  # Installing the OpenAI integration
  uv add langchain-openai

  # Installing the Anthropic integration
  uv add langchain-anthropic
  ```
</CodeGroup>

<Tip>
  See the [Integrations tab](/oss/python/integrations/providers/overview) for a full list of available integrations.
</Tip>

Now that you have LangChain installed, you can get started by following the [Quickstart guide](/oss/python/langchain/quickstart).

***

<Callout icon="pen-to-square" iconType="regular">
  [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/install.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
</Callout>

<Tip icon="terminal" iconType="regular">
  [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
</Tip>
