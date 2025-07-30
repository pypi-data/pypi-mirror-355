"""Example of using the SROIE dataset for receipt information extraction evaluation."""

import json

import doteval


@doteval.eval
def extract_receipt_info(image):
    """Extract key information from a receipt image.

    This function should analyze the receipt image and return a JSON string
    containing the company name, date, address, and total amount.

    Args:
        image: PIL Image object of the receipt

    Returns:
        JSON string with keys: company, date, address, total
    """
    # This is a placeholder implementation
    # In practice, you would use an OCR model or multimodal LLM here

    # Example using a hypothetical multimodal model:
    # response = model.generate(
    #     prompt="Extract the company name, date, address, and total from this receipt",
    #     image=image
    # )

    # For demonstration, return empty fields
    return json.dumps(
        {"company": "", "date": "", "address": "", "total": ""}, sort_keys=True
    )


# Run evaluation on SROIE dataset
if __name__ == "__main__":
    # SROIE only has a train split with ground truth
    results = doteval.run(
        extract_receipt_info, dataset="sroie", metrics=["exact_match", "valid_json"]
    )

    print(f"Exact match accuracy: {results['exact_match']:.2%}")
    print(f"Valid JSON rate: {results['valid_json']:.2%}")
