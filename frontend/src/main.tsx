import { FormEvent, StrictMode, useEffect, useState } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { createRoot } from "react-dom/client";
import "./styles/index.css";

const api = "http://localhost:8000/api/v1";
const token = () => localStorage.getItem("accessToken");

function AuthPage({ register = false }: { register?: boolean }) {
  const navigate = useNavigate(); const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget));
    const response = await fetch(`${api}/auth/${register ? "register" : "login"}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    const body = await response.json(); if (!response.ok) return setError(body.detail ?? "Unable to continue");
    if (register) return navigate("/login"); localStorage.setItem("accessToken", body.access_token); navigate("/dashboard");
  }
  return <main><h1>{register ? "Create account" : "Welcome back"}</h1><form onSubmit={submit}>
    {register && <input name="username" placeholder="Username" minLength={3} required />}
    <input name="email" type="email" placeholder="Email" required /><input name="password" type="password" placeholder="Password" minLength={8} required />
    <button>{register ? "Register" : "Sign in"}</button>{error && <p role="alert">{error}</p>}
  </form><p><Link to={register ? "/login" : "/register"}>{register ? "Already have an account? Sign in" : "Need an account? Register"}</Link></p></main>;
}

function Dashboard() { const navigate = useNavigate(); const [name, setName] = useState("");
  if (!token()) return <Navigate to="/login" replace />;
  useEffect(() => { fetch(`${api}/auth/me`, { headers: { Authorization: `Bearer ${token()}` } }).then(r => r.ok ? r.json() : null).then(user => user && setName(user.username)); }, []);
  return <main><h1>Dashboard</h1><p>{name ? `Signed in as ${name}.` : "Loading your profile..."}</p><button onClick={() => { localStorage.removeItem("accessToken"); navigate("/login"); }}>Sign out</button></main>;
}

function App() { return <Routes><Route path="/" element={<main><h1>Blog Platform</h1><Link to="/login">Sign in</Link></main>} /><Route path="/login" element={<AuthPage />} /><Route path="/register" element={<AuthPage register />} /><Route path="/dashboard" element={<Dashboard />} /></Routes>; }
createRoot(document.getElementById("root")!).render(<StrictMode><BrowserRouter><App /></BrowserRouter></StrictMode>);
