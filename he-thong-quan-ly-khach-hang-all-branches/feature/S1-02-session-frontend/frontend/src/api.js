const API_BASE_URL=import.meta.env.VITE_API_BASE_URL||"http://127.0.0.1:5001";
async function request(path,options={}){
  const response=await fetch(`${API_BASE_URL}${path}`,{
    credentials:"include",...options,
    headers:{"Content-Type":"application/json",...(options.headers||{})},
  });
  const data=await response.json().catch(()=>({}));
  if(!response.ok){const e=new Error(data.message||"Yêu cầu không thành công.");e.status=response.status;e.data=data;throw e}
  return data;
}
export const login=(email,password)=>request("/api/session/login",{method:"POST",body:JSON.stringify({email,password})});
export const getSession=()=>request("/api/session/me",{method:"GET"});
export const logout=()=>request("/api/session/logout",{method:"POST",body:"{}"});
