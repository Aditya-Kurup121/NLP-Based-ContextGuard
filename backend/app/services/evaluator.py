from typing import List, Dict, Any
from backend.app.schemas.analysis import AnalyzeRequest, ContextInfo
from backend.app.services.engine import ContextGuardAnalysisEngine

# Curated benchmark dataset of labeled multi-turn conversations
# Formulated according to ethical academic NLP standards (synthetic non-PII dialogues)
BENCHMARK_CONVERSATIONS = [
    {
        "id": "bench_01",
        "conversation": "Alice: You're such a genius 😂\nBob: Bro, I know. Nobel Prize incoming.\nAlice: Don't forget us when you're famous.",
        "relationship": "Friends",
        "setting": "Chat",
        "ground_truth_risk": "Low",
        "primary_label": "Friendly Banter"
    },
    {
        "id": "bench_02",
        "conversation": "Alex: Nobody wants you in this group.\nAlex: Seriously, just leave.\nAlex: Everyone here would be happier without you.",
        "relationship": "Classmates",
        "setting": "Group Chat",
        "ground_truth_risk": "High",
        "primary_label": "Possible Cyberbullying"
    },
    {
        "id": "bench_03",
        "conversation": "Sam: Wow, you're a real genius.\nJordan: What is that supposed to mean?\nSam: Forget it.",
        "relationship": "Acquaintances",
        "setting": "Forum",
        "ground_truth_risk": "Moderate",
        "primary_label": "Potentially Harmful"
    },
    {
        "id": "bench_04",
        "conversation": "Taylor: I'm going to find you after class and hurt you.",
        "relationship": "Peers",
        "setting": "Direct Message",
        "ground_truth_risk": "Critical",
        "primary_label": "Threat / Urgent Concern"
    },
    {
        "id": "bench_05",
        "conversation": "Emma: Hey guys, what time does the library close today?\nNoah: I think it's 9 PM on weekdays.\nEmma: Thanks Noah!",
        "relationship": "Students",
        "setting": "Study Group",
        "ground_truth_risk": "Low",
        "primary_label": "Harmless / Neutral"
    },
    {
        "id": "bench_06",
        "conversation": "Jake: Stop talking; nobody cares what you think.\nJake: We are kicking you out of the group call.",
        "relationship": "Peers",
        "setting": "Discord",
        "ground_truth_risk": "High",
        "primary_label": "Possible Cyberbullying"
    },
    {
        "id": "bench_07",
        "conversation": "Mia: Watch your back tomorrow, you won't make it home safe.",
        "relationship": "Unknown",
        "setting": "Anonymous Post",
        "ground_truth_risk": "Critical",
        "primary_label": "Threat / Urgent Concern"
    },
    {
        "id": "bench_08",
        "conversation": "Leo: Your gaming skills are absolute garbage bro haha 😂\nKai: Lmao says the guy who died in 5 seconds\nLeo: 1v1 rematch right now!",
        "relationship": "Gaming Buddies",
        "setting": "Game Lobby",
        "ground_truth_risk": "Low",
        "primary_label": "Friendly Banter"
    },
    {
        "id": "bench_09",
        "conversation": "Sarah: Great job breaking the build again.\nDavid: It wasn't my PR.\nSarah: Sure, whatever you say.",
        "relationship": "Coworkers",
        "setting": "Slack Channel",
        "ground_truth_risk": "Moderate",
        "primary_label": "Potentially Harmful"
    },
    {
        "id": "bench_10",
        "conversation": "Chris: Did anyone understand question 4?\nPat: Yes, use Bayes theorem.\nChris: Awesome, appreciate the tip.",
        "relationship": "Classmates",
        "setting": "Group Chat",
        "ground_truth_risk": "Low",
        "primary_label": "Harmless / Neutral"
    }
]

def run_benchmark_evaluation() -> Dict[str, Any]:
    """
    Executes the analysis engine over the labeled test dataset,
    computing precision, recall, F1, accuracy, and confusion matrix.
    """
    engine = ContextGuardAnalysisEngine()
    
    classes = ["Low", "Moderate", "High", "Critical"]
    confusion_matrix = {true_c: {pred_c: 0 for pred_c in classes} for true_c in classes}
    
    detailed_results = []
    correct_count = 0
    total = len(BENCHMARK_CONVERSATIONS)

    for item in BENCHMARK_CONVERSATIONS:
        req = AnalyzeRequest(
            conversation=item["conversation"],
            context=ContextInfo(
                relationship=item["relationship"],
                setting=item["setting"]
            )
        )
        res = engine.analyze(req)
        predicted_risk = res.overall_risk
        true_risk = item["ground_truth_risk"]

        if true_risk in confusion_matrix and predicted_risk in confusion_matrix[true_risk]:
            confusion_matrix[true_risk][predicted_risk] += 1

        is_match = (predicted_risk == true_risk)
        if is_match:
            correct_count += 1

        detailed_results.append({
            "id": item["id"],
            "true_risk": true_risk,
            "predicted_risk": predicted_risk,
            "risk_score": res.risk_score,
            "is_correct": is_match,
            "message_count": len(res.messages),
            "top_classification": res.messages[0].classification if res.messages else "N/A"
        })

    # Compute metrics per class
    metrics_per_class = {}
    for c in classes:
        tp = confusion_matrix[c][c]
        fp = sum(confusion_matrix[other_c][c] for other_c in classes if other_c != c)
        fn = sum(confusion_matrix[c][other_c] for other_c in classes if other_c != c)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics_per_class[c] = {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3)
        }

    macro_f1 = round(sum(m["f1_score"] for m in metrics_per_class.values()) / len(classes), 3)
    accuracy = round(correct_count / total, 3)

    return {
        "total_test_samples": total,
        "overall_accuracy": accuracy,
        "macro_f1_score": macro_f1,
        "per_class_metrics": metrics_per_class,
        "confusion_matrix": confusion_matrix,
        "detailed_results": detailed_results,
        "methodology": {
            "dataset_origin": "Ten curated synthetic conversation demonstrations. These are regression examples, not an independent real-world evaluation dataset.",
            "privacy_compliance": "Zero personally identifiable information (PII); completely synthetic and ethically simulated test cases.",
            "reproducibility": "Run via 'python -m backend.app.services.evaluator' or in-browser evaluation panel."
        }
    }

if __name__ == "__main__":
    import json
    results = run_benchmark_evaluation()
    print(json.dumps(results, indent=2))
