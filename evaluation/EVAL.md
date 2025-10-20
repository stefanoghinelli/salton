# Evaluation

Salton uses manual relevance judgments to measure IR quality. You mark which papers are relevant, then the system computes metrics.

## Setup

Generate ground truth labels:

```bash
salton mark-relevance
```

Shows you top 20 results per query. Mark relevant ones: 1 8 19 or 10-15.

Saves to evaluation/queries/query_relevance.txt.

## Run

```bash
salton benchmark
```

Outputs per-query metrics and saves results to evaluation/results/.

## Example

```
Query: microservice scheduling

Precision: 0.30
Recall: 1.00
NDCG: 0.95
MAP: 0.88
```

Good; found all 3 relevant papers and ranked them near the top.

```
Query: Byzantine consensus

Precision: 0.10
Recall: 0.33
NDCG: 0.15
MAP: 0.05
```

Poor; missed 2 of 3 relevant papers, didn't rank well.

## Files

Input: evaluation/queries/query_natural_lang.txt  queries to test

Labels: evaluation/queries/query_relevance.txt your relevance judgments
```
1|Paper Title A|Paper Title B
2|Paper Title C
```

Output: evaluation/results/metrics_*.json for computed metrics

## Tips

I found that marking 3-6 papers per query as relevant works better than just 1. Be consistent across queries.

If metrics are poor:
1. Check if corpus has papers on that topic: salton search -q "topic" -l 20
2. Try different query phrasing
3. Fetch more papers: salton fetch -l 500
4. Re-run evaluation
