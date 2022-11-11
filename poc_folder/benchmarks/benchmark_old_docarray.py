import time

import numpy as np

from docarray import DocumentArray, Document


def bench():

    da = DocumentArray(
        [
            Document(
                chunks=[
                    Document(text=1000 * 'a'),
                    Document(tensor=np.zeros((3, 224, 224))),
                ]
            )
            for _ in range(1000)
        ]
    )

    n = 100

    init_time = time.time()

    for _ in range(n):
        DocumentArray.from_protobuf(da.to_protobuf())

    total_time = time.time() - init_time

    print(f'{n} iteration in  {total_time} : {total_time/n} it/s')


if __name__ == '__main__':
    bench()
