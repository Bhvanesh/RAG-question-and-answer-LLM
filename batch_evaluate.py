import json
import time
from datetime import datetime
from ai_engine import answer_question
from evalutor import evaluate_rag_response

def run_batch_evaluation(dataset_path: str = "golden_dataset.json"):
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    document_id = dataset["document_id"]
    test_case = dataset["test_cases"]

    print(f"\n{'='*60}")
    print(f"Batch Evaluation - {len(test_case)} questions")
    print(f"Document ID: {document_id}")
    print(f"{'='*60}\n")

    results = []

    for i , case in enumerate(test_case):
        question = case["question"]
        ground_truth = case["ground_truth"]

        print(f"[{i}/{len(test_case)}] {question}")

        try:
            #get rag answer from the AI engine

            rag_result = answer_question(document_id, question)
            answer = rag_result["answer"]
            context = rag_result["contexts"]

            scores = evaluate_rag_response(question = question, answer = answer, context = context, ground_truth = ground_truth)

            results.append({
                "question": question,
                "ground_truth": ground_truth,
                "answer": answer,
                "faithfulness": scores["faithfulness"],
                "answer_relevancy": scores["answer_relevancy"],
                "context_precision": scores["context_precision"],
                "context_recall": scores["context_recall"]
            })

            print(f"    faithfulness={scores['faithfulness']} | "
                  f"relevancy={scores['answer_relevancy']} | "
                  f"precision={scores['context_precision']} | "
                  f"recall={scores['context_recall']}\n")
        except Exception as e:
            print(f"    Error: {str(e)}\n")
            results.append({"question": question, "error": str(e)})

    aggregate = calcualte_aggregate(results)
    print_report(aggregate, len(test_case))

    save_results()




    def calcualte_aggregate(results):
        def avg(metric):
            values = [r[metric] for r in results
                      if metric in r and r[metric] is not None]
            return round(sum(values)/ len(values), 3) if values else None

        return{
            "avg_faithfulness": avg("faithfulness"),
            "avg_answer_relevancy": avg("answer_relevancy"),
            "avg_context_precision": avg("context_precision"),
            "avg_context_recall": avg("context_recall"),
            "total_questions": len(results),
            "failed": len([r for r in results if "error" in r])
        }

def print_report(aggregate, total):
    print(f"{'='*60}")
    print(f"AGGREGATE REPORT")
    print(f"{'='*60}")
    print(f"Total questions:        {total}")
    print(f"Failed:                 {aggregate['failed']}")
    print(f"Avg Faithfulness:       {aggregate['avg_faithfulness']}")
    print(f"Avg Answer Relevancy:   {aggregate['avg_answer_relevancy']}")
    print(f"Avg Context Precision:  {aggregate['avg_context_precision']}")
    print(f"Avg Context Recall:     {aggregate['avg_context_recall']}")
    print(f"{'='*60}\n")




def save_results(results, aggregate):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "timestamp": timestamp,
        "results": results,
        "aggregate": aggregate
    }
    filename= f"eval_run_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(output, f, indent = 2)
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    run_batch_evaluation()

