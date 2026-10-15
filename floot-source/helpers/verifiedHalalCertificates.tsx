/**
 * Reviewed exact-product halal certificates ONLY.
 *
 * No certificate is implied by Open Food Facts, product labels, halal logos,
 * manufacturer statements, or the presence/absence of flagged ingredients.
 *
 * To add a record: verify the issuer's official registry or signed document,
 * certificate scope (exact product and GTIN), dates, and revocation status;
 * then have an editor review the evidence before publishing a record below.
 * Never put manufacturer bulk/private unlicensed records in this list.
 */
export type ReviewedHalalCertificate={
 barcode:string;
 productNames:string[]; // Official product name and individually checked aliases
 brand:string;
 issuer:string;
 certificateNumber:string;
 validFrom:string; // YYYY-MM-DD
 validUntil:string; // YYYY-MM-DD
 verifiedAt:string; // YYYY-MM-DD, last issuer-side check
 officialVerificationUrl:string; // Official issuer evidence / public registry
 certificateDocumentUrl?:string;
 scope:'exact_product';
 reviewStatus:'approved'|'pending'|'rejected';
};
export type DisplayHalalCertificate={
 status:'verified';
 issuer:string;
 certificateNumber:string;
 validFrom:string;
 validUntil:string;
 verifiedAt:string;
 productName:string;
 officialVerificationUrl:string;
 certificateDocumentUrl?:string;
};
/** Reviewed certificate registry. Intentionally empty until issuer evidence is approved. */
export const VERIFIED_HALAL_CERTIFICATES:ReadonlyArray<ReviewedHalalCertificate> = [];

function normalized(s:string):string{
 return String(s||'').normalize('NFKC').toLocaleLowerCase().replace(/\s+/g,' ').trim();
}
function validGtin(s:string):boolean{
 if(!/^(?:\d{8}|\d{12,14})$/.test(s))return false;
 const ds=s.split('').map(Number);
 const check=ds.pop()!;
 const weighted=ds.reverse().reduce((sum,d,i)=>sum+d*(i%2===0?3:1),0);
 return (10-weighted%10)%10===check;
}
function isoDate(s:string):number|null{
 if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return null;
 const day=new Date(s+'T00:00:00.000Z');
 return Number.isFinite(day.getTime())&&day.toISOString().startsWith(s)?day.getTime():null;
}
export function isCertificateDisplayCurrent(cert:DisplayHalalCertificate, at=new Date()):boolean{
 if(!cert||cert.status!=='verified'||!cert.issuer||!cert.certificateNumber)return false;
 const start=isoDate(cert.validFrom),end=isoDate(cert.validUntil),checked=isoDate(cert.verifiedAt);
 if(start===null||end===null||checked===null)return false;
 const today=isoDate(at.toISOString().slice(0,10));
 return today!==null && start<=today && today<=end &&
 checked<=today && today-checked<=180*86400000 && checked>=start;
}
/**
 * A certificate qualifies only if manually approved, dates/current issuer
 * re-check are valid, exact valid barcode matches, and independently reviewed
 * product/brand names match. Names cannot be wildcard/substrings.
 */
export function findVerifiedHalalCertificate(
 barcode:string|null|undefined, productName:string|null|undefined,brand:string|null|undefined,
 at=new Date(), records:ReadonlyArray<ReviewedHalalCertificate>=VERIFIED_HALAL_CERTIFICATES
):DisplayHalalCertificate|null{
 const code=String(barcode||'').trim(),name=normalized(String(productName||'')),maker=normalized(String(brand||''));
 if(!validGtin(code)||!name||!maker)return null;
 for(const r of records){
  if(r.reviewStatus!=='approved'||r.scope!=='exact_product'||r.barcode!==code||!validGtin(r.barcode))continue;
  if(!r.issuer?.trim()||!r.certificateNumber?.trim()||!r.brand?.trim()||!r.productNames?.length)continue;
  if(normalized(r.brand)!==maker||!r.productNames.some(n=>normalized(n)===name))continue;
  if(!/^https:\/\/[^/]+/i.test(r.officialVerificationUrl))continue;
  if(r.certificateDocumentUrl&&!/^https:\/\/[^/]+/i.test(r.certificateDocumentUrl))continue;
  const record:DisplayHalalCertificate={
   status:'verified',issuer:r.issuer,certificateNumber:r.certificateNumber,
   validFrom:r.validFrom,validUntil:r.validUntil,verifiedAt:r.verifiedAt,
   productName:r.productNames.find(n=>normalized(n)===name)||r.productNames[0],
   officialVerificationUrl:r.officialVerificationUrl,
   ...(r.certificateDocumentUrl?{certificateDocumentUrl:r.certificateDocumentUrl}:{})
  };
  if(isCertificateDisplayCurrent(record,at))return record;
 }
 return null;
}
