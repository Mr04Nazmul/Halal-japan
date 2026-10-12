import React,{useState} from 'react';
import {Camera,FileText,AlertCircle} from 'lucide-react';
import {Button} from './Button';
import styles from './IngredientOcr.module.css';
export default function IngredientOcr({onDetected}:{onDetected?:(text:string)=>void}){
 const [busy,setBusy]=useState(false),[text,setText]=useState(''),[error,setError]=useState(''),[progress,setProgress]=useState('');
 const analyze=async(e:React.ChangeEvent<HTMLInputElement>)=>{
 const file=e.target.files?.[0];if(!file)return;setBusy(true);setError('');setText('');
 let worker:any;try{
 setProgress('Loading Japanese OCR…');const t=await import('tesseract.js');
 worker=await t.createWorker('jpn+eng',1,{logger:(m:any)=>{if(m.status)setProgress(m.status)}});
 const found=await worker.recognize(file);const raw=found.data.text?.trim()||'';
 if(!raw)throw Error('No Japanese text recognized. Retake photo under bright light.');
 setText(raw);onDetected?.(raw);
 }catch(err:any){setError(err.message||'OCR failed. Try another photo.')}finally{if(worker)await worker.terminate().catch(()=>{});setBusy(false);e.target.value='';}
 };
 const redFlags=[/豚肉|豚脂|ラード|ポーク|pork|lard/i,/ゼラチン|gelatin|乳化剤|香料|酒精|みりん|アルコール|enzyme|emulsifier/i];
 const strong=redFlags[0].test(text),review=redFlags[1].test(text);
 return <section className={styles.card}><h3><FileText size={20}/> Japanese Ingredient Label OCR</h3><p>Photograph the <b>原材料名</b> and <b>添加物</b> sections on the actual package. Text is recognized on your device; review it before relying on results.</p>
 <label className={styles.pick}><Camera size={18}/>{busy?'Reading label…':'Take / choose ingredient photo'}<input type="file" accept="image/*" capture="environment" disabled={busy} onChange={analyze}/></label>
 {busy&&<p className={styles.muted}>{progress}</p>}{error&&<div className={styles.warn}><AlertCircle size={17}/>{error}</div>}
 {text&&<div className={styles.result}><b>Recognized label (please proofread):</b><textarea aria-label="Correct detected ingredient text" value={text} onChange={e=>setText(e.target.value)} rows={6}/><div className={styles.warn}><AlertCircle size={17}/>{strong?'Possible prohibited pork-derived ingredient detected.':review?'Potentially doubtful additives: manufacturer confirmation needed.':'No obvious prohibited ingredient in recognized text. Halal status is NOT verified.'}</div><small>OCR can misread Japanese labels. A label photo alone does not establish certification or the source of additives.</small></div>}
 </section>;
}
