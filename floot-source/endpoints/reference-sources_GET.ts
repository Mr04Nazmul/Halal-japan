import { db } from '../helpers/db';
import superjson from 'superjson';
export async function handle() {
  const rows = await db.selectFrom('foodReferenceSources')
    .select(['sourceKey','sourceName','sourceUrl','sourceKind','usageNote','halalCertificationSource'])
    .orderBy('sourceName','asc').execute();
  return new Response(superjson.stringify({sources:rows}), {headers:{'Content-Type':'application/json'}});
}

