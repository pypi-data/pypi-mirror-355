import asyncio
from tqdm import tqdm
from .settings import AI_TRANSLATOR, AI_CLIENT as client, AI_ASYNC_CLIENT as async_client

def translate_text(text, 
                         target_language, 
                         model=AI_TRANSLATOR['MODEL'], 
                         prompt_text=AI_TRANSLATOR['PROMPT_TEXT']):
    prompt = f"{prompt_text} {target_language}:\n\n{text}"
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}]
    )
    return response.choices[0].message.content.strip()



# async def async_translate_text(text,
#                           target_language,
#                           model=AI_TRANSLATOR['MODEL'],
#                           prompt_text=AI_TRANSLATOR['PROMPT_TEXT']):
#     prompt = f"{prompt_text} {target_language}:\n\n{text}"
    
#     if AI_TRANSLATOR['ENGINE'] == 'anthropic':
#         # Use async context manager for streaming
#         async with async_client.messages.stream(
#             max_tokens=4096,
#             model=model,
#             messages=[{"role": "user", "content": prompt}]
#         ) as stream:
#             content = ""
#             async for chunk in stream:
#                 if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
#                     content += chunk.delta.text
#                 elif hasattr(chunk, 'content_block') and hasattr(chunk.content_block, 'text'):
#                     content += chunk.content_block.text
#             return content.strip()
#     else:
#         response = await async_client.chat.completions.create(
#             model=model,
#             messages=[{"role": "user", "content": prompt}],
#             timeout=600.0  # 10 minutes timeout
#         )
#         return response.choices[0].message.content.strip()

# async def translate_in_batches(entries, target_language, batch_size=100):
#     for i in tqdm(range(0, len(entries), batch_size), desc="Translating", total=len(entries) // batch_size):
#         batch = entries[i:i + batch_size]
#         tasks = [async_translate_text(entry.msgid, target_language) for entry in batch]
#         translations = await asyncio.gather(*tasks)
#         for entry, translation in zip(batch, translations):
#             entry.msgstr = translation


async def async_translate_text(text,                           
                              target_language,                           
                              model=AI_TRANSLATOR['MODEL'],                           
                              prompt_text=AI_TRANSLATOR['PROMPT_TEXT']):
    prompt = f"{prompt_text} {target_language}:\n\n{text}"          
    
    if AI_TRANSLATOR['ENGINE'] == 'anthropic':
        async with async_client.messages.stream(
            max_tokens=4096,
            model=model,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            content = ""
            async for chunk in stream:
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                    content += chunk.delta.text
                elif hasattr(chunk, 'content_block') and hasattr(chunk.content_block, 'text'):
                    content += chunk.content_block.text
            return content.strip()
    else:
        response = await async_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            timeout=600.0
        )
        return response.choices[0].message.content.strip()


async def async_translate_batch(batch_entries, target_language, model=AI_TRANSLATOR['MODEL'], prompt_text=AI_TRANSLATOR['PROMPT_TEXT']):
    """Send one request for a batch of entries using multiple message dictionaries."""
    
    messages = [
        {"role": "system", "content": f"{prompt_text} {target_language}. Return only translations in order, separated by '|||SEP|||'."}
    ]
    
    # Add each entry as a separate message
    for i, entry in enumerate(batch_entries, 1):
        messages.append({"role": "user", "content": f"Text {i}: {entry.msgid}"})
    
    messages.append({"role": "user", "content": f"Translate all {len(batch_entries)} texts to {target_language}, separated by '|||SEP|||':"})
    
    if AI_TRANSLATOR['ENGINE'] == 'anthropic':
        async with async_client.messages.stream(
            max_tokens=8192,
            model=model,
            messages=messages
        ) as stream:
            content = ""
            async for chunk in stream:
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                    content += chunk.delta.text
                elif hasattr(chunk, 'content_block') and hasattr(chunk.content_block, 'text'):
                    content += chunk.content_block.text
            
            # Parse response
            translations = [t.strip() for t in content.strip().split('|||SEP|||')]
            if len(translations) != len(batch_entries):
                translations = [t.strip() for t in content.strip().split('\n') if t.strip()][:len(batch_entries)]
            
            # Pad if needed
            while len(translations) < len(batch_entries):
                translations.append(batch_entries[len(translations)].msgid)
            
            return translations[:len(batch_entries)]
    
    else:
        response = await async_client.chat.completions.create(
            model=model,
            messages=messages,
            timeout=900.0
        )
        
        content = response.choices[0].message.content.strip()
        translations = [t.strip() for t in content.split('|||SEP|||')]
        if len(translations) != len(batch_entries):
            translations = [t.strip() for t in content.split('\n') if t.strip()][:len(batch_entries)]
        
        while len(translations) < len(batch_entries):
            translations.append(batch_entries[len(translations)].msgid)
        
        print(translations)
        return translations[:len(batch_entries)]


async def translate_in_batches(entries, target_language, batch_size=20):
    for i in tqdm(range(0, len(entries), batch_size), desc="Translating", total=len(entries) // batch_size):
        batch = entries[i:i + batch_size]
        
        try:
            # Single request per batch
            translations = await async_translate_batch(batch, target_language)
            
            # Assign translations to entries
            for entry, translation in zip(batch, translations):
                entry.msgstr = translation
                
        except Exception as e:
            print(f"Batch failed: {e}. Falling back to individual translations.")
            # Fallback to original individual translation logic
            tasks = [async_translate_text(entry.msgid, target_language) for entry in batch]
            translations = await asyncio.gather(*tasks)
            for entry, translation in zip(batch, translations):
                entry.msgstr = translation
