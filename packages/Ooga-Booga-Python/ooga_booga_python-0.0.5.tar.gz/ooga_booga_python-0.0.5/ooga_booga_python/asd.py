from ooga_booga_python.client import OogaBoogaClient
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

async def main():
    client = OogaBoogaClient(
        api_key=os.getenv("OOGA_BOOGA_API_KEY"),
        private_key=os.getenv("PRIVATE_KEY")
    )
    # Example: Fetch token list
    tokens = await client.get_token_list()
    for token in tokens:
        print(f"Name: {token.name}, Symbol: {token.symbol}")

asyncio.run(main())
