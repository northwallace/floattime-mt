"""Section-specific map approval fingerprints. Changed evidence needs re-review."""
import hashlib, json


def fingerprint(river, section, put_in, take_out):
    fields=('id','putIn','takeOut','putInAccessId','takeOutAccessId','miles','difficulty','accessReview','distanceReview','notices','notes','distanceEvidence')
    payload={'riverId':river['id'],'state':river['state'],'section':{k:section[k] for k in fields if k in section},'putIn':put_in,'takeOut':take_out}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
