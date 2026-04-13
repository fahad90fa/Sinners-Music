import fs from "node:fs";

const DEFAULT_CONFIG = {
  prefix: "!",
  sales_channel: null,
  ticket_category: null,
  admin_roles: [],
  support_roles: [],
  log_channel: null,
  payment_methods: ["PayPal", "Bitcoin", "Ethereum", "Bank Transfer"],
  embed_color: "0x00ff9d",
  footer_text: "Sinners Music",
  thumbnail_url: "https://i.imgur.com/your_logo.png",
  rules_message_id: null,
  rules_channel: null,
  welcome_channel: null,
  welcome_style: "main",
  lavalink_nodes: [],
};

export function loadConfig() {
  try {
    const raw = fs.readFileSync("config.json", "utf8");
    const parsed = JSON.parse(raw);
    return { ...DEFAULT_CONFIG, ...parsed };
  } catch (err) {
    fs.writeFileSync("config.json", JSON.stringify(DEFAULT_CONFIG, null, 4));
    return { ...DEFAULT_CONFIG };
  }
}

export function saveConfig(config) {
  fs.writeFileSync("config.json", JSON.stringify(config, null, 4));
}
