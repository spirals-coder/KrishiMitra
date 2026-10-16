import os, httpx
SYSTEM='You are KrishiMitra, a cautious agriculture education assistant for farmers in India. Reply in the language used by the farmer (Hindi or English). Give concise numbered practical steps. Emphasize affordability, sustainability, integrated pest management, safety, and responsible water use. Separate general information from region-specific advice. Never invent weather, scheme eligibility, pesticide doses, scientific facts, yields, or profits. Ask a useful follow-up when context is missing and refer field-specific cases to local agriculture extension officers. Do not prescribe pesticide use.'
async def answer(message, context, history):
    key=os.getenv('OPENAI_API_KEY')
    if not key:
        if any('\u0900' <= char <= '\u097f' for char in message):
            return 'AI सेवा कॉन्फ़िगर नहीं है। सामान्य शैक्षिक सुझाव: 1. कोई कदम उठाने से पहले फसल, बढ़वार की अवस्था, मिट्टी की नमी और हाल की खेत की स्थिति जाँचें। 2. कम लागत वाली रोकथाम, मिट्टी की जाँच और एकीकृत कीट प्रबंधन को प्राथमिकता दें। 3. खेत के अनुसार सलाह के लिए अपना स्थान और फसल बताएँ या स्थानीय कृषि विस्तार अधिकारी से संपर्क करें।'
        return 'AI provider is not configured. General educational guidance: 1. Check crop, growth stage, soil moisture, and recent field conditions before acting. 2. Prefer low-cost prevention, soil testing, and integrated pest management. 3. For a field-specific recommendation, share your location, crop, and growth stage or consult your local agriculture extension officer.'
    payload={'model':os.getenv('OPENAI_MODEL','gpt-4o-mini'),'messages':[{'role':'system','content':SYSTEM+f' Farmer context: {context}.'}]+history+[{'role':'user','content':message}], 'temperature':0.3}
    async with httpx.AsyncClient(timeout=25) as c:
        r=await c.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':f'Bearer {key}'},json=payload); r.raise_for_status(); return r.json()['choices'][0]['message']['content']
