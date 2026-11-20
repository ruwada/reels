import json,sys
d=json.load(open(sys.argv[1])); o={}
for k,v in d.items():
    o[k]=[b for b in v if b[4]>=0.3 or (b[0]<90 or b[2]>990 or b[1]<90 or b[3]>1830)]
json.dump(o,open(sys.argv[2],'w'))
