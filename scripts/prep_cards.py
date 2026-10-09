"""
Take data from data/hsk/cards.json and prep it for use in the app.
Filter out less useful cards, recategorize some cards, and add supporting data.
"""

from pathlib import Path
import json
from typing import TypedDict
import requests
import json
import dotenv
import os
dotenv.load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "data" / "hsk" / "cards.json"
DEFAULT_OUT = ROOT / "data" / "hsk" / "prepped_cards.json"

class Card(TypedDict):
    hsk_level: int
    simplified: str
    chinese: str
    pinyin: str
    english_basic: str

ANALYSIS_PROMPT = """
You are a Chinese tutor helping prepare flash cards for a student learning Chinese in Taiwan.
You will be given a Chinese word with basic information from the HSK curriculum.

Your goal is to analyze the word and provide information to help the student learn words and what to
what is most important for achieving proficiency.

## GUIDELINES
**Meaning**
Meaning should be as concise as possible to convery the meaning of a word.
Favor the provided HSK meaning and only add details if necesssary.

**Example Sentence**
The example sentence should use words at the same level or easier than the given word.
Try to use the provided HSK level as a guide for what words to use.
All varients of the example sentence should be equivalent.

**should_exclude**
Some words are given an alternative definition by the HSK curriculum that are not actually useful for
a learner trying to achieve proficiency. Slang or archaic uses of a word should be excluded from the deck.
Consider the provided HSK level and decide if the word is actually useful for a learner at that stage.
They may still be included in other categories.
"""

OUTPUT_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
      "name": "card_data",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "meaning": {
            "type": "string",
            "description": "Meaning of the word or phrase in English"
          },
          "example_sentence": {
            "type": "object",
            "description": "An example sentence using the word",
            "properties": {
              "traditional": {
                "type": "string",
                "description": "The example sentence in traditional Chinese."
              },
              "simplified": {
                "type": "string",
                "description": "The example sentence in simplified Chinese."
              },
              "pinyin": {
                "type": "string",
                "description": "The example sentence in pinyin."
              },
              "english": {
                "type": "string",
                "description": "The translation of the example sentence in English."
              }
            },
            "additionalProperties": False,
            "required": ["traditional", "simplified", "pinyin", "english"]
          },
          "categories": {
            "type": "array",
            "description": "Semantic categories the word belogs to for studying related words. ex: 'food', 'family', 'basics'",
            "items": {
              "type": "string",
              "description": "The name of the category."
            }
          },
          "exclude": {
            "type": "boolean",
            "description": "Whether the word should be excluded or recategorized from the provided HSK category."
          }
        },
        "required": ["meaning", "example_sentence", "categories", "exclude"],
        "additionalProperties": False
      }
    }
}
    # chinese = models.CharField(max_length=64)
    # simplified = models.CharField(max_length=64, default="")
    # pinyin = models.CharField(max_length=128)
    # english_basic = models.CharField(max_length=255)
    # Future enhancement: add example sentences for the word.
    # example_sentence_traditional = models.CharField(max_length=255, default="")
    # example_sentence_simplified = models.CharField(max_length=255, default="")
    # example_sentence_pinyin = models.CharField(max_length=255, default="")
    # example_sentence_english = models.CharField(max_length=255, default="")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
def analyze_card(card: Card):
    formatted_word = f"""
        Simplified: {card["simplified"]}
        Traditional: {card["chinese"]}
        Pinyin: {card["pinyin"]}
        English: {card["english_basic"]}
        HSK Level: {card["hsk_level"]}
    """
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        data=json.dumps({
            "model": "openai/gpt-6-luna",
            "messages": [
                { "role": "system", "content": ANALYSIS_PROMPT },
                { "role": "user", "content": formatted_word },
            ],
            "response_format": OUTPUT_SCHEMA,
            "reasoning": {
                "effort": "low",
                "exclude": True
            }
        })
    )
    return response.json()

def test():
    with open(DEFAULT_IN) as f:
        cards = json.load(f)
    for card in cards[:7]:
        result = analyze_card(card)
        print(json.dumps(result, indent=4))

def main():
    pass

if __name__ == "__main__":
    exit(test())