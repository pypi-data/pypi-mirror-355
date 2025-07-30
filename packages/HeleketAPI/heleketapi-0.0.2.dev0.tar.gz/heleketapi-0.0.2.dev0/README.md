```bash
pip install HeleketAPI
```

```python
import asyncio
from HeleketAPI import HeleketClient

api = HeleketClient("MERCHANT-UUID", "API-KEY")


async def main() -> None:
    invoice = await api.create_invoice(
        amount=10,
        currency="USDT"
        network="tron",
        lifetime=300
    )
    print(invoice.url)

    await api.session.close()


if __name__ == "__main__":
    asyncio.run(main())
```
