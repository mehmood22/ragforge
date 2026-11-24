# RAGForge Evaluation

RAGForge includes automated retrieval and answer evaluation to measure the quality of its retrieval-augmented generation pipeline and detect regressions.

## Evaluation methodology

The evaluation framework separates retrieval quality from answer generation quality.

Retrieval metrics:

- Hit@K
- Precision@K
- Recall@K
- Mean Reciprocal Rank (MRR)
- Reference evidence coverage
- Retrieval latency

Answer metrics:

- Expected response status
- Required facts present
- Cited evidence coverage
- Citation contract validity
- Correct abstention
- False answers on unsupported questions
- False abstentions
- Overall evaluation pass rate

## Benchmark configuration

| Parameter | Value |
|---|---|
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| LLM | qwen/qwen3.8-27b |
| Retrieval Top K | 7 |
| Minimum relevance score | 0.0 |
| Chunk size | 800 characters |
| Chunk overlap | 120 characters |
| Distance metric | Squared L2 |
| Relevance scoring | Non-negative cosine similarity derived from normalized embeddings |

## Answer evaluation results

Benchmark date: November 24, 2026.

| Dataset | Passed | Total |
|---|---:|---:|
| Synthetic professional profile | 10 | 10 |
| Telecom reference guide — tuning | 12 | 12 |
| Telecom reference guide — held-out | 8 | 8 |
| Total | 30 | 30 |

- Answerable questions passed: 22/22
- Unsupported questions correctly rejected: 8/8
- Citation contract validation: 30/30
- False abstentions: 0

## Telecom retrieval results

The telecom reference document contains 31 indexed chunks across nine pages.

| Metric | Tuning | Held-out |
|---|---:|---:|
| Hit@7 | 100% | 100% |
| Recall@7 | 100% | 100% |
| Precision@7 | 15.87% | 19.05% |
| Evidence coverage | 100% | 100% |
| MRR | 1.000 | 0.875 |
| Mean retrieval latency | 30.36 ms | 24.33 ms |

## Engineering decisions

The retrieval pipeline prioritizes evidence coverage while maintaining a bounded context window.

A fixed relevance threshold can incorrectly discard useful evidence. The default minimum relevance score is therefore zero, allowing the grounded answer generation pipeline to determine whether retrieved evidence is sufficient.

For unit-normalized embeddings, squared L2 distance and cosine similarity have the following relationship:

`cosine_similarity = 1 - squared_l2_distance / 2`

Negative cosine similarities are clipped to zero to maintain the public relevance score range of zero to one.

Relevance scores are similarity measurements, not calibrated probabilities of answer correctness.

## Running evaluations

Index the corresponding evaluation PDF through the standard document ingestion pipeline and wait until its status becomes indexed.

Run retrieval evaluation:

```bash
python -m evals.benchmark_retrieval \
  --document-id DOCUMENT_UUID \
  --dataset evals/datasets/synthetic_telecom.json \
  --split tuning \
  --output evals/reports/telecom-retrieval-tuning.json
```

Run answer evaluation:

```bash
python -m evals.benchmark_answers \
  --document-id DOCUMENT_UUID \
  --dataset evals/datasets/synthetic_telecom.json \
  --split tuning \
  --output evals/reports/telecom-answers-tuning.json
```

Use the held_out split to evaluate a previously selected configuration.

Answer evaluation requires a configured LLM provider. Retrieval evaluation does not require LLM generation.

## Limitations

These results represent a small, controlled evaluation suite across two documents. They do not establish universal accuracy or guarantee hallucination-free answers.

Deterministic required-fact and citation checks cannot detect every semantic error or unsupported claim.

The held-out retrieval report includes comparisons across multiple retrieval configurations. The selected answer generation configuration remained unchanged.

End-to-end answer latency varies with the remote LLM provider. Mean latency ranged from approximately 5.1 to 9.8 seconds across the evaluated datasets.

Future work includes broader document coverage, larger evaluation datasets, semantic faithfulness evaluation, and production-scale performance testing.