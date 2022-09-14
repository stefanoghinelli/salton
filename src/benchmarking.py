from queryprocessing import *


def benchmarking():
    tot_q = 10
    precisions = [1, 1, 1, 1, 1, 0.6, 0.3, 0.3, 0.3, 1]
    map_val = sum(precisions) / tot_q

    natural_queries = []
    with open(QUERY_NATURAL_PATH, 'r') as f:
        for line in f:
            # print(line, "-----")
            natural_queries.append(line[:-1])

    comp_queries = []
    with open(QUERY_BENCH_PATH, 'r') as f:
        for line in f:
            # print(line, "-----")
            comp_queries.append(line[:-1])

    final_res = []
    for cq in comp_queries:
        x = search_something(cq)[:11]
        final_res.append(x)

    # print(final_res)
    for fs in final_res:
        print(f'Natural query: {natural_queries.pop(0)}')
        print(f'Executed query: {comp_queries.pop(0)}')

        print('Results number: ' + str(len(fs)))
        print(fs)
        print(f'Average Precision for first 10 results: {precisions.pop(0)} \n\n')
    print(f'\nMean Average Precision: {map_val} \n')


if __name__ == '__main__':
    benchmarking()
