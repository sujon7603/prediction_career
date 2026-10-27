const $ = (id) => document.getElementById(id);

let mode = location.pathname === "/signup" ? "signup" : "login";

function setMode(next) {
  mode = next;
  const signup = mode === "signup";

  $("authTitle").textContent = signup ? "Create your account" : "Welcome back";
  $("authSub").textContent = signup
    ? "Sign up free to predict your career and see your skill gap."
    : "Log in to predict your career and see your skill gap.";
  document.title = (signup ? "Sign up" : "Log in") + " – Pathwise";

  $("tabLogin").setAttribute("aria-selected", String(!signup));
  $("tabSignup").setAttribute("aria-selected", String(signup));

  $("nameRow").hidden = !signup;
  $("pwHint").hidden = !signup;
  $("password").autocomplete = signup ? "new-password" : "current-password";
  $("password").placeholder = signup ? "Create a password" : "Your password";
  $("submitBtn").textContent = signup ? "Create account" : "Log in";

  $("switchText").firstChild.textContent = signup ? "Already have an account? " : "New here? ";
  $("switchBtn").textContent = signup ? "Log in" : "Create an account";

  setMessage("");
  history.replaceState(null, "", signup ? "/signup" : "/login");
}

function setMessage(text, ok) {
  const m = $("authMsg");
  m.textContent = text;
  m.className = "auth-msg" + (ok ? " ok" : "");
}

async function submit(event) {
  event.preventDefault();
  const name = $("name").value.trim();
  const email = $("email").value.trim();
  const password = $("password").value;

  // quick checks before asking the server
  if (mode === "signup" && name.length < 2) return setMessage("Please enter your name.");
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return setMessage("Please enter a valid email address.");
  if (!password) return setMessage("Please enter your password.");
  if (mode === "signup" && password.length < 8) return setMessage("Password must be at least 8 characters.");

  const button = $("submitBtn");
  button.disabled = true;
  setMessage("Please wait...", true);

  try {
    const body = mode === "signup" ? { name, email, password } : { email, password };
    const res = await fetch("/api/auth/" + mode, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let data = {};
    try { data = await res.json(); } catch (e) {}

    if (!res.ok) {
      const detail = typeof data.detail === "string" ? data.detail : "Please check the form and try again.";
      setMessage(detail);
      button.disabled = false;
      return;
    }
    setMessage(mode === "signup" ? "Account created! Opening Pathwise..." : "Welcome back! Opening Pathwise...", true);
    location.replace("/");
  } catch (err) {
    setMessage("Cannot reach the Pathwise server. Make sure run.bat is still running.");
    button.disabled = false;
  }
}

$("tabLogin").onclick = () => setMode("login");
$("tabSignup").onclick = () => setMode("signup");
$("switchBtn").onclick = () => setMode(mode === "signup" ? "login" : "signup");
$("authForm").addEventListener("submit", submit);
$("togglePw").onclick = () => {
  const field = $("password");
  const show = field.type === "password";
  field.type = show ? "text" : "password";
  $("togglePw").textContent = show ? "Hide" : "Show";
};

setMode(mode);
