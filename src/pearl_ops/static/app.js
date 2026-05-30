const $ = (id) => document.getElementById(id);

function fmt(value, fallback = "-") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function row(label, value) {
  return `<dt>${label}</dt><dd>${fmt(value)}</dd>`;
}

function step(state, title, detail) {
  return `
    <div class="step ${state}">
      <span class="dot"></span>
      <strong>${title}</strong>
      <span>${detail}</span>
    </div>
  `;
}

async function post(path) {
  const res = await fetch(path, { method: "POST" });
  const data = await res.json();
  console.log(path, data);
  await loadStatus();
}

function render(status) {
  const activePool = status.miner.active_pool || status.config.default_pool;
  const activeLog = status.miner.logs[activePool] || status.miner.logs.pearlhash;
  const gpu = status.miner.gpu?.[0] || {};
  const wallet = status.wallet.ok ? status.wallet.data : {};
  const phAccount = status.economics?.pearlhash_account?.ok ? status.economics.pearlhash_account.data : {};
  const phPending = phAccount.pending_rewards?.total_pending;
  const phWorkerHashrate = phAccount.connected_workers?.flatMap((worker) => worker.gpu_info || [])
    ?.reduce((sum, gpu) => sum + Number(gpu.hashrate || 0), 0) / 1e12;
  const safeDiag = status.safetrade.ok ? status.safetrade.data : {};
  const safetradeOk = Boolean(safeDiag.member_me?.ok || safeDiag.spot_balances?.ok);
  const networkOk = status.network.ok && status.network.data === status.config.trusted_ip;

  $("minerState").textContent = status.miner.running ? "Running" : "Stopped";
  $("poolState").textContent = fmt(activePool);
  $("hashrateState").textContent = activeLog?.last_hashrate_th_s
    ? `${activeLog.last_hashrate_th_s} TH/s`
    : "-";
  $("gpuState").textContent = gpu.error
    ? "Error"
    : `${fmt(gpu.utilization_pct)}% / ${fmt(gpu.temperature_c)}C`;
  $("safeState").textContent = safetradeOk ? "Auth OK" : "Check";
  $("updatedAt").textContent = new Date(status.timestamp).toLocaleString();

  $("pipeline").innerHTML = [
    step(status.miner.running ? "ok" : "bad", "Miner process", status.miner.process || "No local miner process"),
    step(activePool === "pearlhash" ? "ok" : "warn", "Pool target", `default=${status.config.default_pool}, active=${fmt(status.miner.active_pool)}`),
    step(
      activeLog?.connected_hint && (activeLog.log_age_seconds === null || activeLog.log_age_seconds < 90) ? "ok" : "warn",
      "Pool connection",
      `${activePool}: ${fmt(activeLog?.last_hashrate_th_s)} TH/s, log age ${fmt(activeLog?.log_age_seconds)}s`
    ),
    step(
      status.economics?.pearlhash_account?.ok ? "ok" : "warn",
      "PearlHash account",
      status.economics?.pearlhash_account?.ok
        ? `pending ${Number(phPending || 0).toFixed(4)} PRL, worker ${Number(phWorkerHashrate || 0).toFixed(2)} TH/s`
        : status.economics?.pearlhash_account?.error
    ),
    step(status.wallet.ok ? "ok" : "bad", "Pearl address", status.wallet.ok ? status.config.pearl_address : status.wallet.error),
    step(networkOk ? "ok" : "warn", "Trusted IP", `current=${status.network.data || status.network.error}, trusted=${status.config.trusted_ip}`),
    step(
      safetradeOk ? "ok" : "warn",
      "SafeTrade API",
      safetradeOk ? "Authenticated" : (safeDiag.member_me?.error || status.safetrade.error)
    ),
    step(status.config.live_trading_enabled ? "warn" : "ok", "Trading guard", status.config.live_trading_enabled ? "Live trading enabled" : "Dry-run / protected"),
    step(status.config.withdrawals_enabled ? "warn" : "ok", "Withdrawal guard", status.config.withdrawals_enabled ? "Withdrawals enabled" : "Withdrawals disabled"),
  ].join("");

  $("logTail").textContent = activeLog?.tail?.join("\n") || "No log yet.";
  $("poolLink").href = activePool === "alphapool"
    ? status.miner.links.alphapool
    : status.miner.links.pearlhash;

  $("walletBox").innerHTML = status.wallet.ok
    ? [
        row("address", wallet.address),
        row("balance", wallet.balance_prl),
        row("received", wallet.total_received_prl),
        row("mined", wallet.total_mined_prl),
        row("tx count", wallet.tx_count),
      ].join("")
    : row("error", status.wallet.error);

  $("gpuBox").innerHTML = gpu.error
    ? row("error", gpu.error)
    : [
        row("name", gpu.name),
        row("util", `${fmt(gpu.utilization_pct)}%`),
        row("power", `${fmt(gpu.power_w)} W`),
        row("temp", `${fmt(gpu.temperature_c)} C`),
        row("memory", `${fmt(gpu.memory_used_mib)} / ${fmt(gpu.memory_total_mib)} MiB`),
      ].join("");

  $("safeBox").innerHTML = [
    row("member", safeDiag.member_me?.ok ? "ok" : safeDiag.member_me?.error || status.safetrade.error),
    row("balances", safeDiag.spot_balances?.ok ? "ok" : safeDiag.spot_balances?.error || "-"),
    row("market", status.config.safetrade_market),
    row("key", status.config.safetrade_api_key),
    row("deposit", status.config.safetrade_deposit),
  ].join("");

  $("configBox").innerHTML = [
    row("pool", status.config.default_pool),
    row("pearlhash", status.config.pearlhash_host),
    row("run hours", status.miner.runtime_hours),
    row("pending", phPending === undefined ? "-" : `${Number(phPending).toFixed(4)} PRL`),
    row("pool TH/s", phWorkerHashrate ? phWorkerHashrate.toFixed(2) : "-"),
    row("est PRL", status.economics?.estimated_net_prl_this_run),
    row("PRL/hour", status.economics?.estimate?.data?.net_prl_per_hour_after_pool_fee),
    row("dry run", status.config.dry_run),
    row("live trade", status.config.live_trading_enabled),
    row("withdraw", status.config.withdrawals_enabled),
  ].join("");
}

async function loadStatus() {
  try {
    const res = await fetch("/api/status", { cache: "no-store" });
    render(await res.json());
  } catch (error) {
    $("minerState").textContent = "Panel error";
    $("logTail").textContent = error.message;
  }
}

$("refreshBtn").addEventListener("click", loadStatus);
$("startBtn").addEventListener("click", () => post("/api/miner/start"));
$("stopBtn").addEventListener("click", () => post("/api/miner/stop"));

loadStatus();
setInterval(loadStatus, 10000);
