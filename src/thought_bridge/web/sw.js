self.addEventListener("push",event=>{
  let data={};
  try{data=event.data?.json()||{};}catch{}
  if(!data.body)return;
  event.waitUntil(self.registration.showNotification(data.title||"New reply",{
    body:data.body,
    // Unique per reply bubble. Never use one constant tag here.
    tag:data.tag||data.event_id||`reply-${Date.now()}`,
    data:{url:data.url||"/"},
  }));
});
self.addEventListener("notificationclick",event=>{
  event.notification.close();
  event.waitUntil(clients.matchAll({type:"window",includeUncontrolled:true}).then(list=>{
    const wanted=new URL(event.notification.data?.url||"/",self.location.origin).href;
    for(const client of list){if("focus" in client){client.navigate?.(wanted);return client.focus();}}
    return clients.openWindow(wanted);
  }));
});
