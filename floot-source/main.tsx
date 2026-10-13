import React from 'react';
import {createRoot} from 'react-dom/client';
import './base.css';

class AppErrorBoundary extends React.Component<React.PropsWithChildren, {failed:boolean}> {
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true};}
 componentDidCatch(error:unknown){console.error('Japan Halal Checker startup error',error);}
 render(){
  if(this.state.failed)return <main style={{padding:24,fontFamily:'system-ui',background:'#10271d',color:'#fff',minHeight:'100vh'}}>
   <h1>Japan Halal Checker</h1><p>Something went wrong while loading this screen. Please reload the website.</p>
   <button style={{padding:'12px 20px',background:'#e4cb91',border:0,borderRadius:10}} onClick={()=>window.location.reload()}>Retry / 再読み込み</button>
  </main>;
  return this.props.children;
 }
}
const rootEl=document.getElementById('root');
if(rootEl){
 const root=createRoot(rootEl);
 const renderMessage=(message:string)=>root.render(<main style={{padding:24,fontFamily:'system-ui',background:'#10271d',color:'#fff',minHeight:'100vh'}}>
  <h1>Japan Halal Checker</h1><p>{message}</p>
  <button style={{padding:'12px 20px',background:'#e4cb91',border:0,borderRadius:10}} onClick={()=>window.location.reload()}>Retry / 再読み込み</button>
 </main>);
 renderMessage('Loading website…');
 import('./pages/_index').then(({default:Home})=>{
  root.render(<AppErrorBoundary><Home/></AppErrorBoundary>);
 }).catch(error=>{
  console.error('Failed to load website module',error);
  renderMessage('The website could not load its files. Please refresh or open this page in Safari.');
 });
}
