from dotenv import load_dotenv
from google import genai
from groq import Groq
from openai import OpenAI
from pathlib import Path
import anthropic
import os

def load_clients():
    load_dotenv()

    # connect to providers
    return {
        'ANTHROPIC': anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_KEY')),
        'GOOGLE': genai.Client(api_key=os.environ.get('GOOGLE_KEY')),
        'GROQ': Groq(api_key=os.environ.get('GROQ_KEY')),
        'OPENAI': OpenAI(api_key=os.environ.get('OPENAI_KEY')),
    }

def is_text_model(model_name: str) -> bool:
    """Filter out non-text models and models requiring special parameters."""
    name = model_name.lower()
    non_text = ['whisper', 'tts', 'audio', 'dall-e', 'image', 'embedding', 
                'moderation', 'guard', 'realtime', 'search', 'transcribe',
                'babbage', 'davinci', 'computer-use', 'o1-mini', 'o1-preview',
                'saba', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-instruct']
    return not any(keyword in name for keyword in non_text)

def fetch_model_ids(clients):
    # get the lists of models
    return {
        'ANTHROPIC': [model.id for model in clients['ANTHROPIC'].models.list(limit=20).data],
        'GOOGLE': [model.name for model in clients['GOOGLE'].models.list() 
                   if 'generateContent' in getattr(model, 'supported_actions', [])],
        'GROQ': [model.id for model in clients['GROQ'].models.list().data 
                 if is_text_model(model.id)],
        'OPENAI': [model.id for model in clients['OPENAI'].models.list().data 
                   if is_text_model(model.id)],
    }


def normalize_name(name: str, seen: set) -> str:
    norm = name.replace('-', '_').replace('.', '_').replace('/', '_').upper()
    if norm in seen:
        raise ValueError(f'Duplicate name: {norm} from {name}')
    seen.add(norm)
    return norm

def generate_enums(model_ids: dict) -> str:
    provider_enum = [
        'from enum import Enum, auto\n\n',
        'class Provider(Enum):\n'
    ]

    for provider in sorted(model_ids):
        provider_enum.append(f'    {provider} = auto()\n')

    model_enum = ['\nclass Model(Enum):\n']
    model_to_provider = ['\nmodel_to_provider = {\n']

    seen = set()
    for provider, ids in model_ids.items():
        for model in sorted(ids):
            model_name = normalize_name(model, seen)
            model_enum.append(f'    {model_name} = \'{model}\'\n')
            model_to_provider.append(f'    Model.{model_name}: Provider.{provider},\n')

    model_to_provider.append('}\n')

    return ''.join(provider_enum + model_enum + model_to_provider)

def main():
    clients = load_clients()
    model_ids = fetch_model_ids(clients)
    enum_code = generate_enums(model_ids)

    output_path = Path('llmpy_models.py')
    output_path.write_text(enum_code)
    

if __name__ == '__main__':
    main()