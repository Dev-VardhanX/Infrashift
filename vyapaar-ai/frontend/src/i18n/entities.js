// Entity translations for Hindi mode.
// Product names, customer names, supplier names, categories, insight titles & text, chat answers & tables.
// Counting numbers and digits strictly stay in Western Arabic format (1, 2, 3...) per user requirement.

export const ENTITY_MAP = {
  // Brand & User
  "Vyapaar AI": "व्यापार AI",
  "Rajesh Sharma": "राजेश शर्मा",
  "Kirana Store Owner": "किराना स्टोर मालिक",
  "Sharma General Store": "शर्मा जनरल स्टोर",

  // Suppliers
  "Gupta Traders": "गुप्ता ट्रेडर्स",
  "Jain Distributors": "जैन डिस्ट्रीब्यूटर्स",
  "Verma Dry Fruit House": "वर्मा ड्राई फ्रूट हाउस",
  "Om Puja Bhandar": "ओम पूजा भंडार",
  "Delhi Dairy Agency": "दिल्ली डेयरी एजेंसी",

  // Customers (All 30 customers from store data)
  "Anil Gupta": "अनिल गुप्ता",
  "Meena Kohli": "मीना कोहली",
  "Vikas Yadav": "विकास यादव",
  "Rajesh Jain": "राजेश जैन",
  "Sandeep Arora": "संदीप अरोड़ा",
  "Harish Chand": "हरीश चंद",
  "Priya Nair": "प्रिया नायर",
  "Ramesh Kumar": "रमेश कुमार",
  "Sunita Devi": "सुनीता देवी",
  "Pooja Verma": "पूजा वर्मा",
  "Mohd. Irfan": "मोहम्मद इरफान",
  "Neha Singh": "नेहा सिंह",
  "Kavita Sharma": "कविता शर्मा",
  "Fatima Begum": "फातिमा बेगम",
  "Gurpreet Singh": "गुरप्रीत सिंह",
  "Anjali Mehta": "अंजलि मेहता",
  "Deepak Tyagi": "दीपक त्यागी",
  "Rekha Rani": "रेखा रानी",
  "Suresh Babu": "सुरेश बाबू",
  "Nisha Khan": "निशा खान",
  "Amit Saxena": "अमित सक्सेना",
  "Lata Mishra": "लता मिश्रा",
  "Manoj Tiwari": "मनोज तिवारी",
  "Seema Bhatia": "सीमा भाटिया",
  "Kiran Pal": "किरण पाल",
  "Rohit Malhotra": "रोहित मल्होत्रा",
  "Shanti Devi": "शांति देवी",
  "Ajay Chauhan": "अजय चौहान",
  "Divya Kapoor": "दिव्या कपूर",
  "Bharat Lal": "भरत लाल",

  // Categories
  "Staples": "किराना / मुख्य खाद्य",
  "Oil & Ghee": "तेल और घी",
  "Dairy & Eggs": "डेयरी और अंडे",
  "Dry Fruits": "सूखे मेवे",
  "Personal & Home Care": "पर्सनल और होम केयर",
  "Snacks & Biscuits": "स्नैक्स और बिस्कुट",
  "Beverages": "पेय पदार्थ",
  "Sweets & Chocolates": "मिठाई और चॉकलेट",
  "Puja & Decor": "पूजा और सजावट",

  // Payment modes
  "UPI": "UPI",
  "Cash": "नकद",
  "Card": "कार्ड",
  "Khata": "उधार खाता",
  "upi": "UPI",
  "cash": "नकद",
  "card": "कार्ड",
  "khata": "उधार खाता",

  // Statuses
  "OUT": "स्टॉक खत्म",
  "CRITICAL": "बेहद कम",
  "LOW": "कम",
  "OK": "ठीक",
  "FESTIVAL_OVER": "त्योहार समाप्त",

  // Products (38 catalog products with Western numerals preserved)
  "Aashirvaad Atta 5kg": "आशीर्वाद आटा 5kg",
  "India Gate Basmati Rice 5kg": "इंडिया गेट बासमती चावल 5kg",
  "Toor Dal 1kg": "तूर दाल 1kg",
  "Sugar 1kg": "चीनी 1kg",
  "Tata Salt 1kg": "टाटा नमक 1kg",
  "Fortune Sunflower Oil 1L": "फॉर्च्यून सनफ्लावर तेल 1L",
  "Saffola Gold Oil 1L": "सफ़ोला गोल्ड तेल 1L",
  "Amul Ghee 1L": "अमूल घी 1L",
  "Amul Taza Milk 500ml": "अमूल ताज़ा दूध 500ml",
  "Amul Paneer 200g": "अमूल पनीर 200g",
  "Eggs Tray (30)": "अंडे की ट्रे (30)",
  "Amul Butter 500g": "अमूल बटर 500g",
  "Parle-G 800g": "पारले-जी 800g",
  "Good Day Cashew 250g": "गुड डे काजू 250g",
  "Maggi Noodles 12-pack": "मैगी नूडल्स 12-पैक",
  "Haldiram Bhujia 400g": "हल्दीराम भुजिया 400g",
  "Lays Classic 52g": "लेज़ क्लासिक 52g",
  "Cadbury Dairy Milk 52g": "कैडबरी डेयरी मिल्क 52g",
  "Cadbury Celebrations 118g": "कैडबरी सेलिब्रेशन्स 118g",
  "Haldiram Soan Papdi 250g": "हल्दीराम सोन पापड़ी 250g",
  "Almonds 250g": "बादाम 250g",
  "Cashew 250g": "काजू 250g",
  "Raisins 250g": "किशमिश 250g",
  "Dettol Soap 3x75g": "डेटॉल साबुन 3x75g",
  "Clinic Plus Shampoo 340ml": "क्लिनिक प्लस शैम्पू 340ml",
  "Colgate Strong Teeth 200g": "कोलगेट स्ट्रॉन्ग टीथ 200g",
  "Surf Excel Easy Wash 1kg": "सर्फ एक्सेल ईज़ी वॉश 1kg",
  "Harpic Toilet Cleaner 500ml": "हार्पिक टॉयलेट क्लीनर 500ml",
  "Tata Tea Gold 500g": "टाटा टी गोल्ड 500g",
  "Nescafe Classic 100g": "नेस्कैफे क्लासिक 100g",
  "Bisleri Water 1L": "बिसलेरी पानी 1L",
  "Real Mango Juice 1L": "रियल मैंगो जूस 1L",
  "Rooh Afza 750ml": "रूह अफ़ज़ा 750ml",
  "Glucon-D Orange 500g": "ग्लूकोन-डी ऑरेंज 500g",
  "Earthen Diyas (12)": "मिट्टी के दीये (12)",
  "Agarbatti Cycle Pure 100s": "अगरबत्ती साइकिल प्योर 100 पीस",
  "Rangoli Colour 500g": "रंगोली रंग 500g",
  "Tealight Candles 50pc": "टीलाइट मोमबत्तियां 50 पीस",

  // Seasonal notes & stock evidence
  "Seasonal demand has ended, leftover stock is slow-moving": "मौसमी मांग खत्म हो चुकी है, बचा हुआ स्टॉक धीमी गति से बिक रहा है",
  "Seasonal stock, festival over": "मौसमी स्टॉक, त्योहार समाप्त",
  "Dead stock, 0 sales in 30 days": "डेड स्टॉक, 30 दिनों में 0 बिक्री",
  "Festival over, do not reorder": "त्योहार समाप्त, दोबारा ऑर्डर न करें",
  "Compressor fault - high bill": "कंप्रेसर की खराबी - अधिक बिल",

  // Insights Titles
  "7 customers owe Rs 31,369, all unpaid for 45+ days": "7 ग्राहकों पर Rs 31,369 बाकी हैं, 45+ दिनों से कोई भुगतान नहीं",
  "Rs 45,556 is locked in 3 slow-moving items": "3 धीमी गति से बिकने वाले सामानों में Rs 45,556 फंसे हैं",
  "Amul Ghee 1L has about 1.1 days of cover (lead time 2 days)": "अमूल घी 1L का लगभग 1.1 दिन का स्टॉक बचा है (लीड टाइम 2 दिन)",
  "Fortune Sunflower Oil now earns only 1.3% margin (was 10.4%)": "फॉर्च्यून सनफ्लावर तेल पर अब केवल 1.3% मार्जिन मिल रहा है (पहले 10.4% था)",
  "Electricity in Oct was Rs 9,718, 1.8x the usual Rs 5,305": "अक्टूबर में बिजली का खर्च Rs 9,718 था, सामान्य Rs 5,305 से 1.8 गुना",
  "Dry Fruits sold 4.1x more in Diwali week, and stock ran low": "दिवाली के हफ्ते में सूखे मेवे की 4.1 गुना ज्यादा बिक्री हुई, और स्टॉक कम हो गया",

  // Insights Why
  "Rule: balance > 0 and days since last payment > 45. Two customers are over the Rs 5,000 credit limit.":
    "नियम: बकाया > 0 और पिछले भुगतान से दिन > 45। दो ग्राहकों का बकाया Rs 5,000 की क्रेडिट सीमा से अधिक है।",
  "Rule: stock > 0 and units sold in last 30 days <= 5% of stock on hand, not a festival item.":
    "नियम: स्टॉक > 0 और पिछले 30 दिनों में बेची गई यूनिट्स उपलब्ध स्टॉक के 5% से कम हैं, त्योहारी सामान नहीं है।",
  "Rule: days of cover < lead time means CRITICAL.":
    "नियम: स्टॉक के दिन < सप्लायर का लीड टाइम का अर्थ है बेहद कम (CRITICAL)।",
  "Latest purchase cost rose 10% on 15 Sep; price is capped at MRP Rs 150. Rule: margin at latest cost dropped >= 5pp vs cost 60+ days ago. Negotiate cost with Gupta Traders (target about Rs 130) or push Saffola Gold (7.4% margin). Do not raise price above MRP.":
    "15 Sep को नवीनतम खरीद लागत 10% बढ़ गई; मूल्य MRP Rs 150 पर सीमित है। नियम: नवीनतम लागत पर मार्जिन 60+ दिन पहले की तुलना में >= 5pp गिरा। गुप्ता ट्रेडर्स से लागत घटाने पर बात करें (लक्ष्य लगभग Rs 130) या सफोला गोल्ड (7.4% मार्जिन) को बढ़ावा दें। MRP से अधिक दाम न बढ़ाएं।",
  "Rule: monthly category total > 1.5x median of other months (and > Rs 1,000). Delivery Fuel in Oct (Rs 5,100 vs Rs 3,020) also flagged.":
    "नियम: मासिक श्रेणी कुल अन्य महीनों के औसत के 1.5 गुना से अधिक (और > Rs 1,000)। अक्टूबर में डिलीवरी ईंधन (Rs 5,100 बनाम Rs 3,020) भी चिह्नित किया गया।",
  "Rule: category revenue in festive window >= 2x prior equal window. Plan: order dry fruits and puja items 2 weeks earlier next year.":
    "नियम: त्योहारी समय में श्रेणी की बिक्री पिछले समान समय से >= 2 गुना। योजना: अगले साल सूखे मेवे और पूजा सामग्री 2 हफ्ते पहले ऑर्डर करें।",
  "These customers have not made any payment in over 45 days. Sending a polite WhatsApp reminder recovers 60-70% of overdue balances within 48 hours without damaging customer relationships.":
    "इन ग्राहकों ने 45 दिनों से अधिक समय से कोई भुगतान नहीं किया है। एक विनम्र व्हाट्सएप रिमाइंडर भेजने से ग्राहकों से रिश्ते खराब किए बिना 48 घंटों में 60-70% बकाया राशि वापस आ जाती है।",
  "These items have had zero or negligible sales in the last 30 days while holding capital. Consider bundling them, offering a discount, or returning them to the supplier.":
    "इन सामानों की पिछले 30 दिनों में शून्य या नगण्य बिक्री हुई है जबकि इनमें पूंजी फंसा हुआ है। इन्हें बंडल करने, छूट देने या सप्लायर को वापस करने पर विचार करें।",
  "Current stock will run out before a fresh order can arrive based on supplier lead time. Reorder immediately to avoid stockout.":
    "सप्लायर के लीड टाइम के अनुसार नया ऑर्डर आने से पहले वर्तमान स्टॉक खत्म हो जाएगा। स्टॉक खत्म होने से बचने के लिए तुरंत ऑर्डर करें।",
  "Supplier cost increased while MRP / selling price remained fixed, severely compressing gross margin. Consider negotiating with the supplier or promoting higher-margin alternatives.":
    "MRP / बिक्री मूल्य स्थिर रहने के दौरान सप्लायर लागत बढ़ गई, जिससे सकल मार्जिन बहुत कम हो गया। सप्लायर से बातचीत करने या अधिक मार्जिन वाले विकल्पों को बढ़ावा देने पर विचार करें।",
  "Oct electricity expense was significantly above the 6-month trailing average. Check for meter errors, festival lighting, or refrigeration issues.":
    "अक्टूबर का बिजली खर्च पिछले 6 महीनों के औसत से काफी अधिक था। मीटर की खराबी, त्योहारी लाइटिंग या फ्रिज संबंधी समस्याओं की जांच करें।",
  "Diwali week saw strong festive demand surge. Review whether sales could have been even higher with better stocking to prepare for next festive season.":
    "दिवाली के हफ्ते में त्योहारी मांग में भारी उछाल देखा गया। समीक्षा करें कि क्या अगले त्योहारी सीजन की तैयारी के लिए बेहतर स्टॉक के साथ बिक्री और अधिक हो सकती थी।",

  // Insight Action Labels
  "Send reminders": "रिमाइंडर भेजें",
  "Stop reordering; discount or bundle": "ऑर्डर बंद करें; छूट दें या बंडल बनाएं",
  "Draft PO": "ऑर्डर ड्राफ्ट करें",
  "Review price": "मूल्य की समीक्षा करें",
  "Check freezer compressor": "फ्रीजर कंप्रेसर की जांच करें",
  "Noted": "दर्ज किया गया",

  // Evidence table column headers
  "Customer": "ग्राहक",
  "Balance (Rs)": "बकाया राशि (Rs)",
  "Days since payment": "भुगतान के बाद से दिन",
  "Over limit": "क्रेडिट सीमा पार",
  "Item": "सामान",
  "In stock": "उपलब्ध स्टॉक",
  "Sold last 30d": "पिछले 30 दिनों में बिक्री",
  "Metric": "मीट्रिक",
  "Value": "मान",
  "Before 15 Sep": "15 Sep से पहले",
  "Before": "पहले",
  "Now": "अब",
  "Month": "महीना",
  "Electricity (Rs)": "बिजली (Rs)",
  "Note": "टिप्पणी",
  "Category": "श्रेणी",
  "18-24 Oct": "18-24 Oct",
  "1-7 Nov": "1-7 Nov",
  "Lift": "बढ़ोतरी",
  "Stock": "स्टॉक",
  "Days of cover": "स्टॉक के दिन",
  "Status": "स्थिति",
  "Cost per unit": "प्रति यूनिट लागत",
  "Margin": "मार्जिन",
  "Oct (Rs)": "अक्टूबर (Rs)",
  "Median (Rs)": "औसत (Rs)",
  "Ratio": "अनुपात",
  "Diwali week": "दिवाली सप्ताह",
  "Prior week": "पिछला सप्ताह",
  "Days": "दिन",
  "Daily demand": "दैनिक मांग",
  "Lead time": "लीड टाइम",
  "Margin on taxable value": "कर योग्य मूल्य पर मार्जिन",
  "Balance": "बकाया राशि",
  "Days overdue": "बकाया दिन",
  "Stock value": "स्टॉक मूल्य",
  "Days dead": "रुके हुए दिन",
  "Days left": "बचे हुए दिन",
  "Product": "उत्पाद",
  "Old margin": "पुराना मार्जिन",
  "New margin": "नया मार्जिन",
  "Cost increase": "लागत वृद्धि",
  "Expense": "खर्च",
  "Oct amount": "अक्टूबर राशि",
  "Normal avg": "सामान्य औसत",

  // Evidence table row cell values
  "Yes": "हाँ",
  "No": "नहीं",
  "2 days": "2 दिन",
  "Electricity": "बिजली",
  "Delivery Fuel": "डिलीवरी ईंधन",
  "Jun": "जून",
  "Jul": "जुलाई",
  "Aug": "अगस्त",
  "Sep": "सितंबर",
  "Oct": "अक्टूबर",
  "Nov": "नवंबर",

  // Chat Answers (translated into natural Hindi, keeping numbers in Western digits)
  "Diwali week (1-7 Nov) revenue was Rs 4,36,555 against Rs 4,03,802 the week before, up 8.1%. Dry Fruits, Puja & Decor and Sweets drove most of the lift.":
    "दिवाली सप्ताह (1-7 Nov) की बिक्री Rs 4,36,555 थी जबकि पिछले सप्ताह Rs 4,03,802 थी, जो 8.1% अधिक है। सूखे मेवे, पूजा और सजावट तथा मिठाई से सबसे अधिक बढ़ोतरी हुई।",

  "Sugar 1kg is already out of stock and Amul Ghee 1L has about 1.1 days left. Almonds, Cashew and Aashirvaad Atta are also under 4 days. Diyas and Rangoli are excluded because Diwali is over.":
    "चीनी 1kg का स्टॉक खत्म हो चुका है और अमूल घी 1L का लगभग 1.1 दिन का स्टॉक बचा है। बादाम, काजू और आशीर्वाद आटा भी 4 दिन से कम हैं। दीये और रंगोली शामिल नहीं हैं क्योंकि दिवाली समाप्त हो चुकी है।",

  "3 products are dead stock and Rs 45,556 is locked in them: Real Mango Juice 1L, Rooh Afza 750ml and Glucon-D Orange 500g.":
    "3 सामान डेड स्टॉक हैं और उनमें Rs 45,556 फंसे हैं: रियल मैंगो जूस 1L, रूह अफ़ज़ा 750ml और ग्लूकोन-डी ऑरेंज 500g।",

  "7 customers owe Rs 31,369 for more than 45 days. The largest is Anil Gupta at Rs 9,685.":
    "7 ग्राहकों पर 45 दिनों से अधिक से Rs 31,369 बाकी हैं। सबसे बड़ा बकाया अनिल गुप्ता का Rs 9,685 है।",

  "Fortune Sunflower Oil cost rose from Rs 128 to Rs 141, so its margin on taxable value fell from 10.4% to 1.3%. Price is capped at MRP Rs 150, so negotiate the cost or push Saffola Gold.":
    "फॉर्च्यून सनफ्लावर तेल की लागत Rs 128 से बढ़कर Rs 141 हो गई, जिससे इसका मार्जिन 10.4% से घटकर 1.3% रह गया। मूल्य MRP Rs 150 पर सीमित है, इसलिए लागत घटाने पर बात करें या सफोला गोल्ड को बढ़ावा दें।",

  "Electricity in October was Rs 9,718 against a usual Rs 5,305, and Delivery Fuel was Rs 5,100 against Rs 3,020.":
    "अक्टूबर में बिजली का खर्च Rs 9,718 रहा जबकि सामान्य खर्च Rs 5,305 है, और डिलीवरी ईंधन Rs 5,100 रहा जबकि सामान्य Rs 3,020 है।",

  "In the last 30 days UPI was 61.4% of revenue, cash 30.6%, card 5.8% and khata 2.2%.":
    "पिछले 30 दिनों में UPI से 61.4% बिक्री हुई, नकद 30.6%, कार्ड 5.8% और उधार खाता 2.2% रहा।",

  "Kul udhaar baaki Rs 35,248 hai. Isme se Rs 31,369 pichhle 45 din se zyada purana hai.":
    "कुल उधार बाकी Rs 35,248 है। इसमें से Rs 31,369 पिछले 45 दिन से ज्यादा पुराना है।",

  "I can only answer from your store data and I could not match that question to a tool. Try one of the suggestions below.":
    "मैं केवल आपकी दुकान के डेटा से उत्तर दे सकता हूँ और इस प्रश्न को किसी टूल से नहीं जोड़ सका। नीचे दिए गए सुझावों में से आज़माएं।",

  // Chat Suggestions
  "Which items will run out in the next 3 days?": "अगले 3 दिनों में कौन सा सामान खत्म हो जाएगा?",
  "Who owes me money for more than 45 days?": "45 दिनों से अधिक समय से किसका उधार बाकी है?",
  "UPI vs cash split in the last 30 days?": "पिछले 30 दिनों में UPI बनाम नकद का अनुपात क्या है?",

  // Upload Loaded entity types
  "sales": "बिक्री",
  "products": "उत्पाद",
  "inventory": "इन्वेंट्री / स्टॉक",
  "purchases": "खरीद",
  "expenses": "खर्च",
  "customers": "ग्राहक",
  "khata_payments": "उधार भुगतान",
};

/**
 * Translates an entity name, product name, customer name, supplier name,
 * category, table header/cell, or insight/chat text if language is Hindi.
 * Strictly maintains Western Arabic counting numerals (1, 2, 3...).
 */
export function tEntity(val, lang) {
  if (lang !== "hi" || val === null || val === undefined) return val;
  if (typeof val !== "string") return val;

  const trimmed = val.trim();
  if (ENTITY_MAP[trimmed]) return ENTITY_MAP[trimmed];

  // Regex for "Sold X units in last Y days" -> "पिछले Y दिनों में X यूनिट बिकीं"
  const soldMatch = trimmed.match(/^Sold\s+(\d+)\s+units\s+in\s+last\s+(\d+)\s+days$/i);
  if (soldMatch) {
    return `पिछले ${soldMatch[2]} दिनों में ${soldMatch[1]} यूनिट बिकीं`;
  }

  // Regex for "X days" -> "X दिन"
  const daysMatch = trimmed.match(/^(\d+(\.\d+)?)\s+days?$/i);
  if (daysMatch) {
    return `${daysMatch[1]} दिन`;
  }

  // Check if string contains known entity keys (like product names or customer names)
  let result = val;
  let changed = false;

  for (const [enTerm, hiTerm] of Object.entries(ENTITY_MAP)) {
    if (enTerm.length > 2 && result.includes(enTerm)) {
      result = result.replaceAll(enTerm, hiTerm);
      changed = true;
    }
  }

  return changed ? result : val;
}
