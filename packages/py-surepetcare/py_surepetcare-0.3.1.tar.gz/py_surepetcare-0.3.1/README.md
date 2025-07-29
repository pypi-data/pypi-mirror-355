# SurePetcare API Client

This repository provides a Python client for accessing the [SurePetcare API](https://app-api.beta.surehub.io/index.html?urls.primaryName=V1).  
**Note:** This project is a work in progress. Many features are experimental or under development. Devices are dynamically loaded from the `devices` folder and mapped based on their `product_id`.

The project is inspired by [benleb/surepy](https://github.com/benleb/surepy), but aims for improved separation of concerns between classes, making it easier to extend and support the v2 SurePetcare API.

## Contributing
**Important:** Store your credentials in a `.env` file (see below) to keep them out of the repository.

Before pushing validate the changes with: `pre-commit run --all-files`.

### Issue with missing data
Please upload issue with data find in contribute/files with `python -m contribute.contribution`. This generates mock data that can be used to improve the library. Dont forget to add email and password in the .env file.

## Example Usage

```python
from dotenv import load_dotenv
import os
from surepetcare.client import SurePetcareClient

# Load credentials from .env file
load_dotenv(dotenv_path=".env")

email = os.getenv("SUREPY_EMAIL")
password = os.getenv("SUREPY_PASSWORD")

client = SurePetcareClient()
await client.login(email=email, password=password)
household_ids = [household['id'] for household in (await client.get_households())]
await client.get_devices(household_ids)
```
