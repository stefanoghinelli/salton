# [salton](https://en.wikipedia.org/wiki/Gerard_Salton)

Salton is a vertical search engine built on a corpus of documents sourced from [arXiv](https://arxiv.org) and [CORE](https://core.ac.uk), public repositories of open-access research papers.
It uses the [Okapi BM25](https://en.wikipedia.org/wiki/Okapi_BM25) ranking function with field boosting to estimate document relevance and an NLTK-based lemmatization for linguistic accuracy.
End users can formulate natural language queries and results are ranked by relevance with title, score, URL, and abstract summary.

## Running the project

The project runs using Python 3 and pip. To install it as a Python package, do the following:

1. Clone the repository and change directory

   ```bash
   $ git clone https://github.com/stefanoghinelli/salton.git
   $ cd salton
   ```

2. Install from source

   ```bash
   $ python3 -m venv venv
   $ source venv/bin/activate
   $ pip install -e .
   ```

3. Download NLTK corpora

   ```bash
   $ python3 -c "import ssl, nltk; ssl._create_default_https_context=ssl._create_unverified_context; [nltk.download(p) for p in ['punkt','stopwords','omw-1.4','wordnet','averaged_perceptron_tagger']]"
   ```

## Usage

This builds Salton locally for command line running.

To fetch papers on arXiv:

```bash
$ salton fetch -l [number of papers] --source arxiv --category cs.DC
```

Or fetch from CORE:

```bash
$ salton fetch -l [number of papers] --source core
```

To build the index:

```bash
$ salton index
```

To query papers by keyword:

```bash
$ salton search -q "[your query]" -l [number of results]
```

## Evaluation

The system can measure IR quality using standard metrics.

### Setup benchmarks
To run benchmarks, you'll need aset of test queries:
   - evaluation/queries/query_natural_lang.txt: natural language queries
   - evaluation/queries/query_benchmark.txt: structured queries
   - evaluation/queries/query_relevance.txt: relevance data

### Benchmark metrics
The currently supported metrics are precision, recall, NDCG, MAP.

Check out the [evaluation guide](./evaluation/EVAL.md) for how to interpret the metrics.

## Example results

```bash
$ salton search -q "distributed microservices scheduling" -l 3

==================================================
  Results for: distributed microservices scheduling
==================================================

1. Title: A Decentralized Microservice Scheduling Approach Using Service Mesh in Cloud-Edge Systems
   Score: 40.9297
   Abstract: This paper presents a new architectural direction: leveraging service
             mesh sidecar proxies as decentralized, in-situ schedulers to enable
             scalable, low-latency coordination in large-scale, cloud-native
             environments. Rather than delivering a finalized scheduling algorithm,
             this paper presents a system-level architectural direction and
             preliminary evidence to support its scalability potential.
   URL: http://arxiv.org/pdf/2510.11189v1

2. Title: REACH Reinforcement Learning for Adaptive Microservice Rescheduling in the Cloud-Edge Continuum
   Score: 34.6261
   Abstract: We propose REACH, a novel rescheduling algorithm that dynamically
             adapts microservice placement in real time using reinforcement
             learning to react to fluctuating resource availability, and
             performance variations across distributed infrastructures. Extensive
             experiments on a real-world testbed demonstrate that REACH reduces
             average end-to-end latency by 7.9%, 10%, and 8% across three benchmark
             MSA applications, while effectively mitigating latency fluctuations
             and spikes.
   URL: http://arxiv.org/pdf/2510.06675v1

3. Title: QONNECT A QoS-Aware Orchestration System for Distributed Kubernetes Clusters
   Score: 28.5372
   Abstract: Modern applications increasingly span across cloud, fog, and edge
             environments, demanding orchestration systems that can adapt to
             diverse deployment contexts while meeting Quality-of-Service (QoS)
             requirements. To address this need, we present QONNECT, a vendor-
             agnostic orchestration framework that enables declarative, QoS-driven
             application deployment across heterogeneous Kubernetes and K3s
             clusters.
   URL: http://arxiv.org/pdf/2510.09851v1
```
