# Algorithme asynchrone

Ce guide explique comment écrire un `AlgorithmBase` dont le traitement est asynchrone tout en restant compatible avec l'API existante.

## Code

```python
import asyncio


class AsyncAlgorithm(AlgorithmBase):
    async def solve_async(self, cube):
        await asyncio.sleep(0.1)
        return ["U", "R", "F"]


async def main():
    cube = "demo"
    algo = AsyncAlgorithm()
    result = await algo.solve_async(cube)
    print(result)
```

## Utilisation

```python
asyncio.run(main())
```


