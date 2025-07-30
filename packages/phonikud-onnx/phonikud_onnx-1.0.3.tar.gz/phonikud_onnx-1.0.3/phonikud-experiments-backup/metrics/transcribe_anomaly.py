import json

with open('report_non_vocalized.json') as fp:
    non_enhanced = json.load(fp)

with open('report_vocalized.json') as fp:
    enhanced = json.load(fp)

print("🔍 Keys where **non-enhanced** is better (lower WER/CER):\n")

# Compare top-level metrics
top_level_metrics = ["average_wer", "global_wer", "average_cer", "global_cer"]
for key in top_level_metrics:
    non_val = non_enhanced.get(key)
    enh_val = enhanced.get(key)
    if non_val < enh_val:
        print(f"• {key}: {non_val:.4f} (non-enhanced) < {enh_val:.4f} (enhanced)")

# Compare individual WERs
print("\n📋 Individual WERs where non-enhanced is better:\n")
better_individuals = 0
for idx, non_val in non_enhanced["individual_wers"].items():
    enh_val = enhanced["individual_wers"].get(idx)
    if enh_val is not None and non_val < enh_val:
        print(f"• Sentence {idx}: {non_val:.3f} < {enh_val:.3f}")
        better_individuals += 1

if better_individuals == 0:
    print("None 🟢")
else:
    print(f"\n✅ Total sentences where non-enhanced is better: {better_individuals}")
