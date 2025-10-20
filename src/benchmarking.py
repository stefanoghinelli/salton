import json
import math
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from .config import BENCHMARK_DIR
from .querier import process_query

class BenchmarkRunner:
    def __init__(self, query_set: str = "default"):
        """
        Initialize benchmark runner
        """
        self.results_dir = Path("./evaluation/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.query_set = query_set

    def load_queries(self) -> List[Dict]:
        """
        Load benchmark queries with ground truth relevance judgments
        """
        queries = []
        benchmark_path = Path(BENCHMARK_DIR)

        suffix = f"_{self.query_set}" if self.query_set != "default" else ""
        natural_lang_file = benchmark_path / f"query_natural_lang{suffix}.txt"
        relevance_file = benchmark_path / f"query_relevance{suffix}.txt"

        if not natural_lang_file.exists():
            print(f"Error: {natural_lang_file} not found")
            return queries

        try:
            with open(natural_lang_file) as f:
                natural_queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            relevance_data = {}
            if relevance_file.exists():
                with open(relevance_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('|')
                            if len(parts) >= 2:
                                query_idx = int(parts[0])
                                relevant_titles = [t.strip() for t in parts[1:] if t.strip()]
                                relevance_data[query_idx] = relevant_titles

            for i, natural in enumerate(natural_queries, 1):
                queries.append({
                    'query_id': i,
                    'query': natural,
                    'relevant_papers': relevance_data.get(i, []),
                    'limit': 10
                })

        except Exception as e:
            print(f"Error loading query files: {e}")
            import traceback
            traceback.print_exc()

        return queries
    
    def run_query(self, query: Dict) -> Dict:
        """
        Run a single benchmark query
        """
        query_text = query.get("query", "")
        limit = query.get("limit", 10)

        start_time = time.time()
        results = process_query(query_text, limit=limit)
        total_time = time.time() - start_time

        return {
            "query": query_text,
            "query_data": query,
            "results": results,
            "total_time": total_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def compute_precision_recall(self, results: List[Dict], query_data: Dict) -> tuple[float, float]:
        """
        Compute precision and recall using ground truth relevance judgments
        """
        if not results:
            return 0.0, 0.0

        relevant_papers = set(query_data.get('relevant_papers', []))

        if not relevant_papers:
            return 0.0, 0.0

        retrieved_relevant = 0
        for result in results:
            if result.get('title', '') in relevant_papers:
                retrieved_relevant += 1

        precision = retrieved_relevant / len(results) if results else 0.0

        recall = retrieved_relevant / len(relevant_papers) if relevant_papers else 0.0

        return precision, recall
    
    def compute_ndcg(self, results: List[Dict], query_data: Dict) -> float:
        """
        Compute NDCG using ground truth relevance judgments
        """
        if not results:
            return 0.0

        relevant_papers = set(query_data.get('relevant_papers', []))

        if not relevant_papers:
            return 0.0

        actual_gains = []
        for result in results:
            gain = 1.0 if result.get('title', '') in relevant_papers else 0.0
            actual_gains.append(gain)

        dcg = sum(gain / math.log2(i + 2) for i, gain in enumerate(actual_gains))

        ideal_gains = [1.0] * min(len(relevant_papers), len(results))
        ideal_gains += [0.0] * (len(results) - len(ideal_gains))
        idcg = sum(gain / math.log2(i + 2) for i, gain in enumerate(ideal_gains))

        return dcg / idcg if idcg > 0 else 0.0

    def compute_map(self, results: List[Dict], query_data: Dict) -> float:
        """
        Compute Mean Average Precision using ground truth relevance judgments
        """
        if not results:
            return 0.0

        relevant_papers = set(query_data.get('relevant_papers', []))

        if not relevant_papers:
            return 0.0

        precisions_at_relevant = []
        relevant_found = 0

        for i, result in enumerate(results, 1):
            if result.get('title', '') in relevant_papers:
                relevant_found += 1
                precision_at_i = relevant_found / i
                precisions_at_relevant.append(precision_at_i)

        return sum(precisions_at_relevant) / len(relevant_papers) if relevant_papers else 0.0
    
    def evaluate_result(self, benchmark_result: Dict) -> Dict:
        """
        Evaluate a single benchmark result
        """
        results = benchmark_result["results"]
        query_data = benchmark_result["query_data"]
        
        precision, recall = self.compute_precision_recall(results, query_data)
        ndcg = self.compute_ndcg(results, query_data)
        map_score = self.compute_map(results, query_data)
        
        return {
            "precision": precision,
            "recall": recall,
            "ndcg": ndcg,
            "map": map_score,
            "execution_time": benchmark_result["total_time"],
            "result_count": len(results)
        }
    
    def save_results(self, raw_results: List[Dict], metrics: Dict[str, Dict]) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        raw_output = self.results_dir / f"raw_results_{timestamp}.json"
        with open(raw_output, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "results": raw_results
            }, f, indent=2)
        
        metrics_output = self.results_dir / f"metrics_{timestamp}.json"
        with open(metrics_output, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "metrics": metrics
            }, f, indent=2)
    
    def run_benchmark(self, save_results: bool = True) -> Dict[str, Dict]:
        queries = self.load_queries()
        if not queries:
            raise ValueError("No benchmark queries found")
        
        raw_results = []
        for i, query in enumerate(queries):
            try:
                result = self.run_query(query)
                raw_results.append(result)
                    
            except Exception as e:
                print(f"Error running query '{query.get('natural_language', 'unknown')}': {e}")
                continue
        
        metrics = {}
        for result in raw_results:
            query_text = result["query"]
            metrics[query_text] = self.evaluate_result(result)
        
        if save_results:
            self.save_results(raw_results, metrics)
        
        return metrics

def run_benchmark(save_results: bool = True, query_set: str = "default") -> Dict[str, Dict]:
    runner = BenchmarkRunner(query_set=query_set)
    return runner.run_benchmark(save_results=save_results)
