from ..models.schemas import CropRequest
RULES={
 'Cereal':[('Millet','Drought-tolerant option often considered for lower-water settings; suitability depends on local rainfall and cultivar.','Generally lower water need than paddy; verify sowing window with local KVK.'),('Maize','Can suit several soil types with adequate drainage and timely moisture.','Moderate water; avoid waterlogging; local season and seed choice matter.')],
 'Pulse':[('Pigeon pea','Pulse option for warm season and well-drained soils; variety and duration vary.','Usually suited to rain-fed systems; verify local sowing calendar.'),('Green gram','Short-duration pulse considered in suitable warm windows.','Sensitive to waterlogging; check local variety and season.')],
 'Oilseed':[('Groundnut','Can suit lighter, well-drained soils where climate and seed availability fit.','Avoid waterlogging; local sowing window is essential.')],
 'Vegetable':[('Okra','Warm-season option with staggered harvest potential.','Needs regular moisture and pest monitoring; select locally adapted seed.')],
 'Horticulture':[('Papaya','Possible horticulture option where frost and water conditions are suitable.','Requires drainage and ongoing care; seek local horticulture guidance.')]
}
def recommend(req: CropRequest):
    candidates=[]
    for group, items in RULES.items():
        if req.category not in ('Any',group): continue
        for crop, why, care in items:
            score=2
            if req.irrigation=='Rain-fed' and crop in ('Millet','Pigeon pea'): score+=2
            if req.soil_type in ('Sandy','Loamy') and crop in ('Groundnut','Millet'): score+=1
            if req.budget=='Low' and crop in ('Millet','Green gram'): score+=1
            candidates.append({'crop':crop,'category':group,'score':score,'why':why,'considerations':care,'duration':'Varies by cultivar and local conditions; confirm locally','water':'Qualitative guidance only; assess soil moisture and rainfall','sowing_window':'Not validated for the selected district; confirm with local KVK/agriculture office','risks':['Local climate, variety, seed access, pests, and market conditions can change suitability'],'next_steps':['Check locally recommended varieties and sowing dates','Compare seed and input costs locally','Consider a soil test before planting']})
    candidates.sort(key=lambda x:-x['score'])
    return {'recommendations':candidates[:4],'note':'Transparent rule-based shortlist for exploration, not a yield, profit, or field-specific prediction. Confirm with the district agriculture office/KVK.'}
