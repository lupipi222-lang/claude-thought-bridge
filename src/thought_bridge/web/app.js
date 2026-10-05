const list=document.querySelector("#messageList");
const pushButton=document.querySelector("#pushButton");
const toastBox=document.querySelector("#toast");
const TOKEN_KEY="thought_bridge_user_token";
let token=localStorage.getItem(TOKEN_KEY)||"";
let events=[];
let stream=null;
const trailThoughtMap=new Map();

function esc(value){return String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[ch]);}
function formatText(value){return esc(value).replace(/\n/g,"<br>");}
function splitSelfState(text){
  const raw=String(text||"");
  const match=raw.match(/^\s*\[\[自我状态[：:]?\]\]([\s\S]*?)\[\[\/自我状态\]\]/);
  if(!match)return {state:"",body:raw.trim()};
  const state=match[1].trim();
  const body=raw.slice(match[0].length).replace(/^[—-]{2,}\s*/,"").trim();
  return {state,body};
}
function showToast(text){toastBox.textContent=text;toastBox.classList.add("show");clearTimeout(showToast.timer);showToast.timer=setTimeout(()=>toastBox.classList.remove("show"),1600);}
async function copyText(text){
  try{await navigator.clipboard.writeText(text);}catch{
    const area=document.createElement("textarea");area.value=text;area.style.position="fixed";area.style.opacity="0";document.body.append(area);area.select();document.execCommand("copy");area.remove();
  }
  showToast("原始过程已复制");
}
function auth(){
  if(token)return true;
  token=prompt("输入 RELAY_USER_TOKEN")?.trim()||"";
  if(token)localStorage.setItem(TOKEN_KEY,token);
  return !!token;
}
async function api(path,options={}){
  if(!auth())throw new Error("missing token");
  const response=await fetch(path,{...options,headers:{Authorization:`Bearer ${token}`,"Content-Type":"application/json",...(options.headers||{})}});
  if(response.status===401){localStorage.removeItem(TOKEN_KEY);token="";throw new Error("unauthorized");}
  if(!response.ok)throw new Error(`HTTP ${response.status}`);
  return response.json();
}
function groupEvents(source){
  const out=[];let trail=[];let lastAt=0;
  const flushTrail=()=>{if(trail.length){out.push({type:"trail",trail:[...trail],id:`trail-${trail[0].event_id}`});trail=[];}};
  for(const event of source){
    const at=Date.parse(event.ts)||0;
    if(trail.length&&lastAt&&at-lastAt>5*60*1000)flushTrail();
    if(event.kind==="thinking"||event.kind==="action"){
      trail.push(event);lastAt=at;continue;
    }
    if(event.kind==="reply"){
      out.push({type:"reply",event,trail:[...trail]});trail=[];lastAt=at;
    }
  }
  flushTrail();
  return out;
}
function trailHtml(trail,state,id,open=false){
  if(!trail.length&&!state)return "";
  trailThoughtMap.set(String(id),trail.filter(item=>item.kind==="thinking").map(item=>item.text));
  const native=trail.map(item=>item.kind==="thinking"
    ? `<div class="trail-think">${formatText(item.text)}</div>`
    : `<div class="trail-act">${esc(item.text)}</div>`).join("");
  const hasState=!!state;
  return `<details class="trail" data-trail-id="${esc(id)}" data-mode="${hasState?"heart":"native"}" ${hasState?'data-has-heart="1"':""} ${open?"open":""}>
    <summary><span data-trail-label>${hasState?"心里话":"Process"}</span></summary>
    <div class="trail-body">
      ${hasState?`<div class="trail-heart">${formatText(state)}</div>`:""}
      <div class="trail-native ${hasState?"hidden":""}">${native}<div class="trail-done">Done</div></div>
      ${hasState&&trail.some(item=>item.kind==="thinking")?'<small class="trail-switch-hint">双击查看原始过程</small>':""}
    </div>
  </details>`;
}
function render(){
  trailThoughtMap.clear();
  const grouped=groupEvents(events);
  if(!grouped.length){list.innerHTML='<p class="empty">还没有消息</p>';return;}
  list.innerHTML=grouped.map(item=>{
    if(item.type==="trail")return trailHtml(item.trail,"",item.id,true);
    const {state,body}=splitSelfState(item.event.text);
    return `<article class="message-row ai" data-event-id="${esc(item.event.event_id)}"><div class="message-stack">
      ${trailHtml(item.trail,state,item.event.event_id,false)}
      ${body?`<div class="bubble">${formatText(body)}</div>`:""}
      <time class="message-time">${new Date(item.event.ts).toLocaleString([], {month:"numeric",day:"numeric",hour:"2-digit",minute:"2-digit"})}</time>
    </div></article>`;
  }).join("");
  bindTrails();
  list.lastElementChild?.scrollIntoView({block:"end"});
}
function bindTrails(){
  list.querySelectorAll(".trail").forEach(details=>{
    const label=details.querySelector("[data-trail-label]");
    const heart=details.querySelector(".trail-heart");
    const native=details.querySelector(".trail-native");
    const hint=details.querySelector(".trail-switch-hint");
    const body=details.querySelector(".trail-body");
    const thought=trailThoughtMap.get(details.dataset.trailId)||[];
    const setMode=mode=>{details.dataset.mode=mode;label.textContent=mode==="heart"?"心里话":"Process";heart?.classList.toggle("hidden",mode!=="heart");native?.classList.toggle("hidden",mode!=="native");hint?.classList.toggle("hidden",mode!=="heart");};
    details.addEventListener("toggle",()=>{if(!details.open&&heart)setMode("heart");});
    hint?.addEventListener("click",event=>{event.preventDefault();event.stopPropagation();details.open=false;});
    body?.addEventListener("dblclick",event=>{if(details.open&&heart&&details.dataset.mode==="heart"&&thought.length){event.preventDefault();event.stopPropagation();setMode("native");details.dataset.ignoreClickUntil=String(performance.now()+480);}});
    let lastTap=0,lastX=0,lastY=0;
    body?.addEventListener("touchend",event=>{
      if(!details.open||!heart||details.dataset.mode!=="heart")return;
      const touch=event.changedTouches?.[0];if(!touch)return;
      const now=performance.now();const double=now-lastTap<420&&Math.hypot(touch.clientX-lastX,touch.clientY-lastY)<42;
      if(double&&thought.length){event.preventDefault();event.stopPropagation();setMode("native");details.dataset.ignoreClickUntil=String(now+520);lastTap=0;}else{lastTap=now;lastX=touch.clientX;lastY=touch.clientY;}
    },{passive:false});
    body?.addEventListener("click",async()=>{
      if(!details.open||details.dataset.mode!=="native")return;
      if(performance.now()<Number(details.dataset.ignoreClickUntil||0))return;
      if(thought.length)await copyText(thought.join("\n\n"));
      details.open=false;
    });
  });
}
async function load(){
  try{const data=await api("/api/history?conversation_id=main&limit=300");await api("/api/session",{method:"POST",body:"{}"});events=data.events||[];render();connect();reportPresence();}
  catch(error){list.innerHTML=`<p class="empty">连接失败：${esc(error.message)}</p>`;}
}
function connect(){
  stream?.close();stream=new EventSource("/api/stream");
  stream.onmessage=event=>{try{const item=JSON.parse(event.data);if(item.conversation_id!=="main")return;if(events.some(old=>old.event_id===item.event_id))return;events.push(item);render();}catch{}};
}
async function reportPresence(){try{await api("/api/presence",{method:"POST",body:JSON.stringify({visible:!document.hidden})});}catch{}}
function b64ToBytes(value){const padded=value+"=".repeat((4-value.length%4)%4);const raw=atob(padded.replace(/-/g,"+").replace(/_/g,"/"));return Uint8Array.from(raw,ch=>ch.charCodeAt(0));}
pushButton.onclick=async()=>{
  try{
    if(!("serviceWorker" in navigator)||!("PushManager" in window))throw new Error("此浏览器不支持 Web Push");
    const permission=await Notification.requestPermission();if(permission!=="granted")throw new Error("没有获得通知权限");
    const registration=await navigator.serviceWorker.register("/sw.js");
    const {public_key}=await api("/api/push/public-key");if(!public_key)throw new Error("服务器还没配置 VAPID");
    const subscription=await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:b64ToBytes(public_key)});
    await api("/api/push/subscribe",{method:"POST",body:JSON.stringify(subscription)});pushButton.textContent="通知已开启";showToast("通知已开启");
  }catch(error){showToast(error.message);}
};
document.addEventListener("visibilitychange",reportPresence);
setInterval(()=>{if(!document.hidden)reportPresence();},30000);
load();
