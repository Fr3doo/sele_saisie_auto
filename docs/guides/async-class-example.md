# Exemple de classe asynchrone

Ce court exemple montre comment définir une classe dont les méthodes sont `async` afin d'être utilisées dans un flux asynchrone. La classe effectue simplement une opération fictive avec `await asyncio.sleep`.

## Code

```python
import asyncio

class SimpleAsyncWorker:
    async def run(self, data: str) -> str:
        await asyncio.sleep(0.5)
        return data.upper()
```

## Appel depuis l'application

Pour exécuter la méthode asynchrone, utilisez `asyncio.run` ou incluez-la dans une boucle existante :

```python
async def main() -> None:
    worker = SimpleAsyncWorker()
    result = await worker.run("demo")
    print(result)

asyncio.run(main())
```
