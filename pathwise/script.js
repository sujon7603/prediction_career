const $ = (id) => document.getElementById(id);

const have = new Set();   // skill keys the user selected
let META = null;
let gapRequestId = 0;

// ---------- helpers ----------
async function api(path, body) {
  const options = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : undefined;
  const res = await fetch(path, options);
  if (res.status === 401) {
    location.replace("/login");   // not logged in (or session ended)
    throw new Error("Please log in.");
  }
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail; } catch (e) {}
    throw new Error(detail || "Request failed (" + res.status + ")");
  }
  return res.json();
}

function showBanner(message) {
  const b = $("banner");
  b.textContent = message || "";
  b.hidden = !message;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// ---------- step 1: skill chips ----------
function renderSkills() {
  const box = $("skills");
  box.innerHTML = "";
  META.skills.forEach((s) => {
    const b = el("button", "chip", s.label);
    b.type = "button";
    b.setAttribute("aria-pressed", have.has(s.key));
    b.onclick = () => {
      have.has(s.key) ? have.delete(s.key) : have.add(s.key);
      renderSkills();
      refreshGap();
    };
    box.appendChild(b);
  });
}

// ---------- step 1: predict ----------
async function predict() {
  const msg = $("predictMsg");
  if (have.size === 0) {
    msg.textContent = "Please tap at least one skill first.";
    return;
  }
  msg.textContent = "Asking the AI...";
  try {
    const data = await api("/api/career/predict", { skills: Array.from(have) });
    msg.textContent = "";
    renderResults(data);
    $("role").value = data.predicted_career;
    refreshGap();
  } catch (err) {
    msg.textContent = "";
    showBanner("Could not get a prediction: " + err.message);
  }
}

function renderResults(data) {
  const box = $("results");
  box.innerHTML = "";
  data.careers.forEach((c, i) => {
    const card = el("div", "result" + (i === 0 ? " best" : ""));

    const head = el("div", "result-head");
    head.appendChild(el("h4", "", c.career));
    if (i === 0) head.appendChild(el("span", "badge", "Best fit"));
    card.appendChild(head);

    card.appendChild(metric("AI confidence", c.ai_confidence, "teal"));
    card.appendChild(metric("Skill match", c.skill_match, "indigo"));

    const btn = el("button", "link", "See skill gap →");
    btn.type = "button";
    btn.onclick = () => {
      $("role").value = c.career;
      refreshGap();
      $("analyzer").scrollIntoView({ behavior: "smooth" });
    };
    card.appendChild(btn);
    box.appendChild(card);
  });
  showBanner("");
}

function metric(label, value, color) {
  const wrap = el("div", "metric");
  const top = el("div", "metric-top");
  top.appendChild(el("span", "", label));
  top.appendChild(el("b", "", Math.round(value) + "%"));
  const bar = el("div", "bar");
  const fill = el("i", "fill " + color);
  fill.style.width = Math.max(0, Math.min(100, value)) + "%";
  bar.appendChild(fill);
  wrap.appendChild(top);
  wrap.appendChild(bar);
  return wrap;
}

// ---------- step 2: skill gap ----------
async function refreshGap() {
  const career = $("role").value;
  if (!career) return;
  const myId = ++gapRequestId;
  try {
    const gap = await api("/api/skill-gap", { career: career, skills: Array.from(have) });
    if (myId !== gapRequestId) return;   // a newer request replaced this one
    renderGap(gap);
    showBanner("");
  } catch (err) {
    showBanner("Could not load the skill gap: " + err.message);
  }
}

function renderGap(g) {
  $("roleDesc").textContent = g.description;

  const chips = $("gapChips");
  chips.innerHTML = "";
  g.matching.forEach((s) => chips.appendChild(el("span", "tagchip have", "✓ " + s.label)));
  g.missing.forEach((s) => chips.appendChild(el("span", "tagchip gap", s.label)));

  const p = Math.round(g.match_score);
  $("ring").style.setProperty("--p", p);
  $("pct").textContent = p + "%";

  $("verdict").textContent =
    have.size === 0 ? "Tap the skills you already have in step 1."
    : p >= 100 ? "You have every skill for this career. Start applying!"
    : p >= 70 ? "You are close. Learn the last few skills and start applying."
    : p >= 40 ? "Solid base. A focused plan will get you job-ready."
    : "A good start. Follow the plan below in order.";

  const plan = $("plan");
  plan.innerHTML = "";
  if (g.missing.length === 0) {
    plan.appendChild(el("li", "empty", "No gaps. You cover every skill for this career."));
  } else {
    g.missing.forEach((m) => {
      const li = el("li", "", m.label);
      li.appendChild(el("small", "", "about " + m.weeks + " weeks"));
      plan.appendChild(li);
    });
  }
  $("eta").textContent = g.missing.length
    ? "Estimated time to close the gap: " + g.total_weeks + " weeks at about 6 hours a week."
    : "";
}

// ---------- careers grid ----------
function renderRoles() {
  const sel = $("role");
  const grid = $("roleGrid");
  META.careers.forEach((c) => {
    sel.add(new Option(c.name, c.name));

    const d = el("div", "role");
    d.appendChild(el("h3", "", c.name));
    d.appendChild(el("p", "", c.description));
    d.appendChild(el("span", "tag", c.skills.length + " core skills"));
    d.appendChild(document.createElement("br"));
    const b = el("button", "", "Analyze this career");
    b.type = "button";
    b.onclick = () => {
      sel.value = c.name;
      refreshGap();
      $("analyzer").scrollIntoView({ behavior: "smooth" });
    };
    d.appendChild(b);
    grid.appendChild(d);
  });
}

// ---------- logged-in user ----------
function showUser(user) {
  const chip = $("userChip");
  chip.textContent = "Hi, " + user.name.split(" ")[0];
  chip.hidden = false;
  $("logoutBtn").onclick = async () => {
    try { await fetch("/api/auth/logout", { method: "POST" }); } catch (e) {}
    location.replace("/login");
  };
}

// ---------- start ----------
async function init() {
  if (location.protocol === "file:") {
    showBanner("Please start the Pathwise server and open http://localhost:8000 (see README).");
    return;
  }
  try {
    const me = await api("/api/auth/me");
    showUser(me.user);
    META = await api("/api/meta");
  } catch (err) {
    if (err.message === "Please log in.") return;
    showBanner("Cannot reach the Pathwise server. Make sure run.bat is still running, then refresh.");
    return;
  }
  renderSkills();
  renderRoles();
  $("role").onchange = refreshGap;
  $("predictBtn").onclick = predict;
  refreshGap();
}

init();
