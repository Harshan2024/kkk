from app.nlp.parser import parse_compound_activity

cases = [
    "I travelled 25 km by train and ate veg rice",
    "I used AC for 2 hours then drove 10 km",
    "I ate idli, travelled 5 km by bike and used fan for 3 hours",
    "I ate idli and used fan for 3 hours",
]
for case in cases:
    results = parse_compound_activity(case)
    print(f"\nINPUT: {case}")
    print(f"  PARTS: {len(results)}")
    for r in results:
        print(f"    cat={r['category']} item={r['item']} qty={r['quantity']} conf={r['confidence']}")
