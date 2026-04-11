import { LavalinkManager } from "lavalink-client";

function normalizeNode(node, index) {
  if (!node?.host || !node?.port || !node?.password) return null;
  return {
    id: node.identifier || `node-${index + 1}`,
    host: node.host,
    port: Number(node.port),
    authorization: node.password,
    secure: Boolean(node.https ?? node.secure),
    requestTimeout: 30000,
    retryAmount: 5,
    retryDelay: 5000,
  };
}

function resolveNodes(config) {
  const fromList = (config.lavalink_nodes || [])
    .map((node, index) => normalizeNode(node, index))
    .filter(Boolean);

  if (fromList.length) return fromList;

  // Backward compatibility for single-node configs.
  if (config.lavalink?.host && config.lavalink?.port && config.lavalink?.password) {
    const single = normalizeNode(
      {
        identifier: "main",
        host: config.lavalink.host,
        port: config.lavalink.port,
        password: config.lavalink.password,
        https: config.lavalink.https,
      },
      0
    );
    if (single) return [single];
  }

  // Environment fallback for deployments that keep Lavalink in env vars.
  if (process.env.LAVALINK_HOST && process.env.LAVALINK_PORT && process.env.LAVALINK_PASSWORD) {
    const envNode = normalizeNode(
      {
        identifier: process.env.LAVALINK_IDENTIFIER || "env-node",
        host: process.env.LAVALINK_HOST,
        port: process.env.LAVALINK_PORT,
        password: process.env.LAVALINK_PASSWORD,
        https: String(process.env.LAVALINK_HTTPS || "false").toLowerCase() === "true",
      },
      0
    );
    if (envNode) return [envNode];
  }

  return [];
}

async function probeV4Info(node) {
  const url = `http${node.secure ? "s" : ""}://${node.host}:${node.port}/v4/info`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), node.requestTimeout || 10000);
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: { Authorization: node.authorization },
      signal: controller.signal,
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

export async function setupLavalink(client, config) {
  const configuredNodes = resolveNodes(config);
  if (!configuredNodes.length) {
    console.warn("⚠️ Lavalink: no valid nodes found in config/env.");
    return null;
  }

  const healthyNodes = [];
  for (const node of configuredNodes) {
    const ok = await probeV4Info(node);
    if (ok) healthyNodes.push(node);
    else console.warn(`⚠️ Lavalink node skipped (no /v4/info): ${node.host}:${node.port}`);
  }

  if (!healthyNodes.length) {
    console.warn("⚠️ Lavalink: no reachable v4 nodes after probe.");
    return null;
  }

  const manager = new LavalinkManager({
    nodes: healthyNodes,
    sendToShard: (guildId, payload) =>
      client.guilds.cache.get(guildId)?.shard?.send(payload),
    client: {
      id: client.user?.id ?? "0",
      username: client.user?.username ?? "ZeroDay Tools",
    },
    autoSkip: true,
    playerOptions: {
      defaultSearchPlatform: "spsearch",
      applyVolumeAsFilter: false,
      volumeDecrementer: 0.75,
    },
  });

  client.lavalink = manager;
  manager.discordClient = client;

  // Prevent process crash when any public node emits runtime errors (429/timeout/etc.).
  manager.nodeManager.on("error", (node, error) => {
    const nodeId = node?.options?.id || node?.id || "unknown-node";
    const host = node?.options?.host || "unknown-host";
    const port = node?.options?.port || "unknown-port";
    console.warn(`⚠️ Lavalink node error [${nodeId}] ${host}:${port} -> ${error?.message || error}`);
  });

  manager.nodeManager.on("connect", (node) => {
    const nodeId = node?.options?.id || node?.id || "unknown-node";
    const host = node?.options?.host || "unknown-host";
    console.log(`✅ Lavalink node connected: ${nodeId} (${host})`);
  });

  manager.nodeManager.on("disconnect", (node, payload) => {
    const nodeId = node?.options?.id || node?.id || "unknown-node";
    const host = node?.options?.host || "unknown-host";
    const reason = payload?.reason || "unknown";
    const code = payload?.code ?? "n/a";
    console.warn(`⚠️ Lavalink node disconnected: ${nodeId} (${host}) code=${code} reason=${reason}`);
  });

  manager.nodeManager.on("reconnecting", (node) => {
    const nodeId = node?.options?.id || node?.id || "unknown-node";
    const host = node?.options?.host || "unknown-host";
    console.warn(`⚠️ Lavalink node reconnecting: ${nodeId} (${host})`);
  });

  client.on("raw", (data) => manager.sendRawData(data));

  const init = async () => {
    const initialized = await manager.init({
      id: client.user.id,
      username: client.user.username,
    });
    if (!initialized?.useable) {
      console.warn("⚠️ Lavalink initialized but no nodes are currently useable.");
    } else {
      console.log(`✅ Lavalink initialized with ${healthyNodes.length} healthy node(s).`);
    }
  };

  if (client.user) {
    init().catch((err) => console.error("❌ Lavalink init failed:", err));
  } else {
    client.once("ready", () => {
      init().catch((err) => console.error("❌ Lavalink init failed:", err));
    });
  }

  return manager;
}
