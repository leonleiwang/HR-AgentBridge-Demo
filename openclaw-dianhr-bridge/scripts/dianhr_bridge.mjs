#!/usr/bin/env node

const DEFAULT_ENDPOINT = "http://127.0.0.1:8000/agent/run";
const FALLBACK =
  "DianHR 本地服务暂时不可用，请确认 http://127.0.0.1:8000/health 是否正常。";

function getArgValue(name) {
  const index = process.argv.indexOf(name);
  if (index === -1) return "";
  return process.argv[index + 1] || "";
}

async function readStdin() {
  if (process.stdin.isTTY) return "";
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8").trim();
}

async function main() {
  const endpoint = process.env.DIANHR_AGENT_ENDPOINT || DEFAULT_ENDPOINT;
  const message = (getArgValue("--message") || (await readStdin())).trim();

  if (!message) {
    console.log("请提供需要转发给 DianHR 的消息。");
    return;
  }

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify({
        message,
        channel: "dingtalk",
        source: "openclaw-dianhr-bridge",
      }),
    });

    if (!response.ok) {
      console.log(FALLBACK);
      return;
    }

    const data = await response.json();
    const reply = typeof data.reply === "string" ? data.reply.trim() : "";
    console.log(reply || FALLBACK);
  } catch {
    console.log(FALLBACK);
  }
}

main();
