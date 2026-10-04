import { useEffect, useRef, useState } from "react";
import { getSession, login, logout } from "./api";
import "./styles.css";

function Login({message,onLoggedIn}){
  const [email,setEmail]=useState("employee@company.vn");
  const [password,setPassword]=useState("Employee123");
  const [error,setError]=useState("");
  async function submit(e){
    e.preventDefault();setError("");
    try{const r=await login(email,password);onLoggedIn(r.user)}
    catch(err){setError(err.data?.message||"Email hoặc mật khẩu không đúng.")}
  }
  return <main className="page"><section className="card">
    <div className="brand">CRM</div><p className="eyebrow">S1-02 · PHIÊN ĐĂNG NHẬP</p><h1>Đăng nhập</h1>
    {message&&<div className="notice">{message}</div>}
    <form className="form" onSubmit={submit}>
      <label>Email công ty<input type="email" value={email} onChange={e=>setEmail(e.target.value)}/></label>
      <label>Mật khẩu<input type="password" value={password} onChange={e=>setPassword(e.target.value)}/></label>
      {error&&<div className="alert">{error}</div>}<button>Đăng nhập</button>
    </form>
  </section></main>
}

function Home({user,onExpired,onLogout}){
  const last=useRef(0); const [status,setStatus]=useState("Phiên sẽ tự gia hạn khi còn hoạt động.");
  useEffect(()=>{
    async function touch(){
      const now=Date.now(); if(now-last.current<30000)return; last.current=now;
      try{await getSession();setStatus("Phiên vừa được gia hạn do có hoạt động.")}
      catch(e){if(e.status===401)onExpired(e.data?.message||"Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.")}
    }
    const names=["click","keydown","scroll"];
    names.forEach(n=>window.addEventListener(n,touch,{passive:true}));
    return()=>names.forEach(n=>window.removeEventListener(n,touch));
  },[onExpired]);

  async function signOut(){try{await logout()}finally{onLogout()}}
  return <main className="page"><section className="card center">
    <div className="brand">CRM</div><p className="eyebrow">PHIÊN ĐĂNG NHẬP HỢP LỆ</p>
    <h1>Trang làm việc</h1><p>Xin chào <strong>{user.full_name}</strong>.</p>
    <div className="box"><strong>Trạng thái phiên</strong><span>{status}</span></div>
    <p className="hint">Khi bạn click, gõ phím hoặc cuộn trang, server sẽ gia hạn phiên. Nếu phiên hết hạn, hệ thống tự đưa về đăng nhập.</p>
    <button className="danger" onClick={signOut}>Đăng xuất an toàn</button>
  </section></main>
}

export default function App(){
  const [user,setUser]=useState(null);const [message,setMessage]=useState("");const [checking,setChecking]=useState(true);
  useEffect(()=>{getSession().then(r=>setUser(r.user)).catch(e=>{
    if(e.status===401&&e.data?.code==="session_expired")setMessage(e.data.message);
    setUser(null)
  }).finally(()=>setChecking(false))},[]);
  if(checking)return <main className="page">Đang kiểm tra phiên đăng nhập...</main>;
  return user
    ? <Home user={user} onExpired={m=>{setMessage(m);setUser(null)}} onLogout={()=>{setMessage("Bạn đã đăng xuất an toàn.");setUser(null)}}/>
    : <Login message={message} onLoggedIn={u=>{setMessage("");setUser(u)}}/>;
}
