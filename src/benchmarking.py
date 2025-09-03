import json
import math
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from .config import BENCHMARK_DIR
from .query_processing import process_query

class BenchmarkRunner:
    def __init__(self):
        self.results_dir = Path("./evaluation/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def load_queries(self) -> List[Dict]:
        """
        Load benchmark queries from structured text files
        """
        queries = []
        benchmark_path = Path(BENCHMARK_DIR)
        
        natural_lang_file = benchmark_path / "query_natural_lang.txt"
        benchmark_file = benchmark_path / "query_benchmark.txt" 
        relevance_file = benchmark_path / "query_relevance.txt"
        
        if not all(f.exists() for f in [natural_lang_file, benchmark_file, relevance_file]):
            return queries
            
        try:
            with open(natural_lang_file) as f:
                natural_queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            with open(benchmark_file) as f:
                structured_queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            with open(relevance_file) as f:
                relevance_data = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        precision, recall, relevant_docs = line.split(',')
                        relevance_data.append({
                            'expected_precision': float(precision),
                            'expected_recall': float(recall), 
                            'expected_relevant_docs': int(relevant_docs)
                        })
            
            for i, (natural, structured, relevance) in enumerate(zip(natural_queries, structured_queries, relevance_data)):
                queries.append({
                    'natural_language': natural,
                    'structured_query': structured,
                    'query': natural,
                    'expected_relevant_docs': relevance['expected_relevant_docs'],
                    'expected_precision': relevance['expected_precision'],
                    'expected_recall': relevance['expected_recall'],
                    'limit': 10
                })
                
        except Exception as e:
            print(f"Error loading query files: {e}")
            
        return queries
    
    def run_query(self, query: Dict) -> Dict:
        """
        Run a single benchmark query
        """
        query_text = query.get("natural_language", query.get("query", ""))
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
        Compute precision and recall using title-based relevance matching
        """
        if not results:
            return 0.0, 0.0
        
        query_text = query_data.get('natural_language', '').lower()
        query_terms = set(query_text.split())
        
        relevant_count = 0
        for result in results:
            title = result.get('title', '').lower()
            title_terms = set(title.split())
            
            overlap = len(query_terms.intersection(title_terms))
            if overlap >= min(2, len(query_terms) // 2):
                relevant_count += 1
        
        expected_relevant = query_data.get('expected_relevant_docs', 10)
        
        precision = relevant_count / len(results) if results else 0.0
        recall = relevant_count / expected_relevant if expected_relevant > 0 else 0.0
        
        return precision, recall
    
    def compute_ndcg(self, results: List[Dict], query_data: Dict) -> float:
        if not results:
            return 0.0
            
        query_terms = set(query_data.get('natural_language', '').lower().split())
        expected_relevant = query_data.get('expected_relevant_docs', 5)
        
        actual_gains = []
        for result in results:
            title_terms = set(result.get('title', '').lower().split())
            overlap = len(query_terms.intersection(title_terms))
            gain = min(overlap / len(query_terms) if query_terms else 0, 1.0)
            actual_gains.append(gain)
        
        dcg = sum(gain / math.log2(i + 2) for i, gain in enumerate(actual_gains))
        
        ideal_gains = [1.0] * min(expected_relevant, len(results)) + [0.0] * max(0, len(results) - expected_relevant)
        idcg = sum(gain / math.log2(i + 2) for i, gain in enumerate(ideal_gains))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def compute_map(self, results: List[Dict], query_data: Dict) -> float:
        if not results:
            return 0.0
            
        query_terms = set(query_data.get('natural_language', '').lower().split())
        
        precisions_at_relevant = []
        relevant_found = 0
        
        for i, result in enumerate(results, 1):
            title_terms = set(result.get('title', '').lower().split())
            overlap = len(query_terms.intersection(title_terms))
            
            if overlap >= max(1, len(query_terms) // 3):
                relevant_found += 1
                precisions_at_relevant.append(relevant_found / i)
        
        return sum(precisions_at_relevant) / len(precisions_at_relevant) if precisions_at_relevant else 0.0
    
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
    
    def run_benchmark(self, save_results: bool = True, progress_callback: Optional[Any] = None) -> Dict[str, Dict]:
        queries = self.load_queries()
        if not queries:
            raise ValueError("No benchmark queries found")
        
        raw_results = []
        total_queries = len(queries)
        
        for i, query in enumerate(queries):
            try:
                result = self.run_query(query)
                raw_results.append(result)
                
                if progress_callback:
                    progress = int((i + 1) / total_queries * 100)
                    progress_callback(progress)
                    
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

def run_benchmark(save_results: bool = True, progress_callback: Optional[Any] = None) -> Dict[str, Dict]:
    runner = BenchmarkRunner()
    return runner.run_benchmark(save_results=save_results, progress_callback=progress_callback)